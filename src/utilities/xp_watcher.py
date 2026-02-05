"""
XP Watcher Service for Auto-OSBC

Monitors the XP popup area (left of minimap) to detect skill XP gains in real-time.
Automatically updates SkillsManager when XP is detected.

Usage:
    from utilities.xp_watcher import XPWatcher

    # Initialize watcher with window reference
    watcher = XPWatcher(bot.win)

    # In bot main loop
    if watcher.should_check():
        watcher.check_for_xp()

    # Debug: Save screenshot of detection area
    watcher.save_debug_screenshot("xp_area_debug")
"""

import time
from pathlib import Path
from typing import Optional, Tuple, TYPE_CHECKING
import cv2
import numpy as np

from utilities.geometry import Rectangle
from utilities.window import Window
from utilities.osrs_skills import skill_names
import utilities.ocr as ocr
import utilities.color as clr
import utilities.imagesearch as imsearch

if TYPE_CHECKING:
    from model.skills import SkillsManager

# Confidence threshold for skill icon matching (0.0-1.0, higher = stricter)
SKILL_ICON_CONFIDENCE_THRESHOLD = 0.8

# Size of skill icon in XP popup (pixels)
SKILL_ICON_SIZE = 25


class XPWatcher:
    """
    Watches the XP popup area for skill experience gains.

    The XP popup appears to the left of the minimap when you gain XP.
    Format: [Skill Icon] +X XP
    """

    # Check interval (seconds) - how often to check for XP popup
    CHECK_INTERVAL = 2.0

    # XP popup appears for ~4-5 seconds, so we check every 2 seconds to catch it

    def __init__(self, window: Window, debug: bool = False):
        """
        Initialize the XP watcher.

        Args:
            window: Window instance with initialized game client
            debug: Enable debug logging and screenshot saving
        """
        self.window = window
        self.debug = debug
        self._last_check_time = 0.0
        self._xp_area: Optional[Rectangle] = None
        self._skill_templates_loaded = False
        self._skill_templates = {}

        # Calculate XP detection area (left of minimap)
        self._calculate_xp_area()

        # Auto-load skill templates from skills directory
        self.load_skill_templates()

    def _calculate_xp_area(self) -> None:
        """
        Calculate the XP popup detection area based on minimap position.

        XP popup appears to the left of the minimap, roughly:
        - Width: ~150 pixels
        - Height: ~30 pixels
        - Position: Left edge of minimap - 160px, vertically centered on minimap top
        """
        if not self.window or not self.window.minimap_area:
            return

        minimap = self.window.minimap_area

        # XP popup area configuration
        # These values can be adjusted based on your client settings
        xp_popup_width = 150
        xp_popup_height = 33

        # Position: Left of minimap with 10px gap
        xp_left = minimap.left - xp_popup_width - 20
        xp_top = minimap.top  # Slightly below top of minimap

        self._xp_area = Rectangle(
            left=xp_left, top=xp_top, width=xp_popup_width, height=xp_popup_height
        )

        if self.debug:
            print(
                f"[XP Watcher] XP area calculated: left={xp_left}, top={xp_top}, width={xp_popup_width}, height={xp_popup_height}"
            )
            print(
                f"[XP Watcher] Minimap position: left={minimap.left}, top={minimap.top}"
            )

    def should_check(self) -> bool:
        """
        Check if enough time has passed to check for XP again.

        Returns:
            True if we should check for XP now
        """
        current_time = time.time()
        elapsed = current_time - self._last_check_time
        return elapsed >= self.CHECK_INTERVAL

    def check_for_xp(self) -> bool:
        """
        Check the XP area for a popup and update skills if found.

        Returns:
            True if XP was detected and processed
        """
        if not self._xp_area:
            if self.debug:
                print("[XP Watcher] XP area not initialized")
            return False

        self._last_check_time = time.time()

        try:
            # Capture XP area
            screenshot = self._xp_area.screenshot()

            if self.debug:
                print(
                    f"[XP Watcher] Screenshot captured: {screenshot.shape if screenshot is not None else 'None'}"
                )

            # Try to detect skill and parse XP
            skill_name, xp_amount = self._parse_xp_popup(screenshot)

            if self.debug:
                print(
                    f"[XP Watcher] Parsed popup - Skill: {skill_name}, XP: {xp_amount}"
                )

            if skill_name and xp_amount is not None:
                # Update SkillsManager with new XP (lazy import to avoid circular dependency)
                from model.skills import SkillsManager
                from model.bot_session_state import BotSessionState

                manager = SkillsManager()
                manager.update_skill_xp(skill_name, xp_amount)

                # Record starting XP for session tracking
                BotSessionState().record_starting_xp(skill_name, xp_amount)

                print(f"[XP Watcher] Detected {skill_name}: total: {xp_amount})")
                return True
            elif xp_amount and not skill_name:
                print(
                    f"[XP Watcher] WARNING: Detected XP amount ({xp_amount}) but no skill icon matched!"
                )
                if self.debug:
                    # Save debug screenshot for investigation
                    self.save_debug_screenshot(
                        f"failed_skill_detection_{int(time.time())}"
                    )

        except Exception as e:
            # Log error in debug mode, otherwise fail silently
            if self.debug:
                import traceback

                print(f"[XP Watcher] Error during XP check: {e}")
                traceback.print_exc()

        return False

    def _is_popup_visible(self, screenshot: np.ndarray) -> bool:
        """
        Check if the XP popup is currently visible.

        The popup contains numbers (XP amount) when visible.
        When not visible, this area shows the game world without numbers.

        Args:
            screenshot: Screenshot of XP area (unused, kept for backwards compatibility)

        Returns:
            True if popup appears to be visible (contains numbers)
        """
        # Try OCR with common XP popup text colors
        colors = [clr.WHITE, clr.OFF_WHITE, clr.OFF_YELLOW]

        for font in (ocr.PLAIN_11, ocr.PLAIN_12, ocr.BOLD_12):
            text = ocr.extract_text(self._xp_area, font, colors)
            if not text:
                continue

            # Check if text contains any digits
            import re

            if re.search(r"\d", text):
                if self.debug:
                    print(f"[XP Watcher] Popup visible - detected text: '{text}'")
                return True

        if self.debug:
            print("[XP Watcher] No numbers detected - popup not visible")

        return False

    def _parse_xp_popup(
        self, screenshot: np.ndarray
    ) -> Tuple[Optional[str], Optional[int]]:
        """
        Parse the XP popup to extract skill name and XP amount.

        Format: [Icon] +X XP

        Args:
            screenshot: Screenshot of XP area (unused - kept for backwards compatibility)

        Returns:
            Tuple of (skill_name, xp_amount) or (None, None) if parsing fails
        """
        # Match skill icon from the left edge of the XP popup
        skill_name, confidence = self._match_skill_icon()

        # Extract XP amount via OCR
        xp_amount = self._extract_xp_amount(screenshot)

        if self.debug and skill_name:
            print(
                f"[XP Watcher] Matched {skill_name} (confidence: {confidence:.2f}), XP: {xp_amount}"
            )

        if xp_amount and not skill_name:
            print(
                f"[XP Watcher] Detected XP amount ({xp_amount}) but no skill icon matched"
            )

        return skill_name, xp_amount

    def _match_skill_icon(self) -> Tuple[Optional[str], float]:
        """
        Match skill icon using the XP popup area with existing search_img_in_rect function.

        Uses the same proven template matching as other bots (fishing.py, etc.)

        Returns:
            Tuple of (skill_name, confidence) or (None, 0.0) if no match
        """
        if not self._skill_templates_loaded:
            return None, 0.0

        if not self._xp_area:
            if self.debug:
                print("[XP Watcher] XP area not initialized")
            return None, 0.0

        if self.debug:
            print(
                f"[XP Watcher] Searching XP area: ({self._xp_area.width}x{self._xp_area.height})"
            )
            print(
                f"[XP Watcher] Checking {len(self._skill_templates)} skill templates..."
            )

        # Try each skill template using search_img_in_rect (same pattern as fishing.py)
        for skill_name in self._skill_templates.keys():
            try:
                # Get template path (supports machine profiles)
                template_path = imsearch.get_template_path(
                    "skills", f"{skill_name}.png"
                )

                # Search for template in XP area using existing function
                # confidence parameter: lower = stricter match (for TM_SQDIFF_NORMED)
                found = imsearch.search_img_in_rect(
                    template_path,
                    self._xp_area,
                    confidence=0.25,  # Lenient for XP popup icons
                )

                if found:
                    if self.debug:
                        print(f"[XP Watcher]   {skill_name}: ✓ MATCHED")
                    return skill_name, 1.0  # Return immediately on first match

                if self.debug:
                    print(f"[XP Watcher]   {skill_name}: not found")

            except Exception as e:
                if self.debug:
                    print(f"[XP Watcher]   {skill_name}: ERROR - {e}")
                    import traceback

                    traceback.print_exc()

        # No match - save debug
        if self.debug:
            print(f"[XP Watcher] No skill matched")
            try:
                screenshot = self._xp_area.screenshot()
                if screenshot is not None:
                    self._save_failed_icon_screenshot(screenshot, None, 0.0)
            except Exception as e:
                print(f"[XP Watcher] Failed to save debug screenshot: {e}")

        return None, 0.0

    def _extract_xp_amount(self, screenshot: np.ndarray) -> Optional[int]:
        """
        Extract XP amount from screenshot using OCR.

        Looks for pattern like "+123 XP" or "123 XP"

        Args:
            screenshot: Screenshot of XP area

        Returns:
            XP amount as integer, or None if not found
        """
        # Try OCR with white/yellow text colors (typical for XP popup)
        colors = [clr.WHITE, clr.OFF_WHITE, clr.OFF_YELLOW]

        for font in (ocr.PLAIN_11, ocr.PLAIN_12, ocr.BOLD_12):
            text = ocr.extract_text(self._xp_area, font, colors)
            if not text:
                continue

            # Look for XP pattern: "+123" or "123"
            import re

            match = re.search(r"\+?(\d+)", text)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return None

    def _save_failed_icon_screenshot(
        self, icon_screenshot: np.ndarray, best_match: Optional[str], confidence: float
    ) -> None:
        """
        Save the icon screenshot when matching fails for debugging.

        Args:
            icon_screenshot: The 25x25 icon screenshot that failed to match
            best_match: The best matching skill name (if any)
            confidence: The confidence score of the best match
        """
        try:
            # Create output directory
            output_dir = Path("debug_screenshots")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create filename with timestamp and match info
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            best_str = f"best_{best_match}" if best_match else "no_match"
            conf_str = f"conf_{confidence:.2f}".replace(".", "_")

            # Save the 25x25 icon screenshot
            icon_filename = f"failed_icon_{timestamp}_{best_str}_{conf_str}.png"
            icon_filepath = output_dir / icon_filename
            cv2.imwrite(str(icon_filepath), icon_screenshot)
            print(f"[XP Watcher] Saved failed icon screenshot: {icon_filepath}")

            # Save the best matching template for comparison
            if best_match and best_match in self._skill_templates:
                template_path = self._skill_templates[best_match]
                template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
                if template is not None:
                    template_filename = (
                        f"failed_template_{timestamp}_{best_str}_{conf_str}.png"
                    )
                    template_filepath = output_dir / template_filename
                    cv2.imwrite(str(template_filepath), template)
                    print(
                        f"[XP Watcher] Saved best template for comparison: {template_filepath}"
                    )

            # Also save the FULL XP area screenshot for context
            if self._xp_area:
                full_xp_screenshot = self._xp_area.screenshot()
                if full_xp_screenshot is not None:
                    full_xp_filename = (
                        f"failed_full_xp_area_{timestamp}_{best_str}_{conf_str}.png"
                    )
                    full_xp_filepath = output_dir / full_xp_filename
                    cv2.imwrite(str(full_xp_filepath), full_xp_screenshot)
                    print(
                        f"[XP Watcher] Saved full XP area screenshot: {full_xp_filepath}"
                    )

        except Exception as e:
            print(f"[XP Watcher] Failed to save icon debug screenshot: {e}")

    def save_debug_screenshot(self, description: str = "xp_area") -> Optional[Path]:
        """
        Save a debug screenshot of the XP detection area with overlay.

        This helps you verify the detection area is correctly positioned.

        Args:
            description: Description for the screenshot filename

        Returns:
            Path to saved screenshot, or None if failed
        """
        if not self._xp_area:
            print("[XP Watcher] Cannot save debug screenshot: XP area not calculated")
            return None

        try:
            # Create output directory
            output_dir = Path("debug_screenshots")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            session_dir = output_dir / f"{timestamp}_{description}"
            session_dir.mkdir(parents=True, exist_ok=True)

            # Capture full client for context
            full_client = self.window.rectangle().screenshot()

            # Draw XP area rectangle on full client screenshot
            overlay = full_client.copy()

            # Calculate XP area position relative to client window
            rel_x = self._xp_area.left - self.window.rectangle().left
            rel_y = self._xp_area.top - self.window.rectangle().top

            # Draw detection area in bright green
            cv2.rectangle(
                overlay,
                (rel_x, rel_y),
                (rel_x + self._xp_area.width, rel_y + self._xp_area.height),
                (0, 255, 0),  # Bright green
                2,  # Thicker line for visibility
            )

            # Add label
            cv2.putText(
                overlay,
                "XP Detection Area",
                (rel_x, rel_y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

            # Save full client with overlay
            full_path = session_dir / "full_client_with_xp_area.png"
            cv2.imwrite(str(full_path), overlay)
            print(f"[XP Watcher] Saved full client overlay: {full_path}")

            # Save just the XP area
            xp_area_screenshot = self._xp_area.screenshot()
            xp_area_path = session_dir / "xp_area_closeup.png"
            cv2.imwrite(str(xp_area_path), xp_area_screenshot)
            print(f"[XP Watcher] Saved XP area closeup: {xp_area_path}")

            # Save metadata
            metadata = {
                "timestamp": timestamp,
                "description": description,
                "xp_area": {
                    "left": self._xp_area.left,
                    "top": self._xp_area.top,
                    "width": self._xp_area.width,
                    "height": self._xp_area.height,
                },
                "minimap": {
                    "left": self.window.minimap_area.left,
                    "top": self.window.minimap_area.top,
                    "width": self.window.minimap_area.width,
                    "height": self.window.minimap_area.height,
                },
                "client_mode": "fixed" if self.window.client_fixed else "resizable",
            }

            import json

            metadata_path = session_dir / "xp_area_metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            print(f"[XP Watcher] Debug session saved to: {session_dir}")
            print(f"   - Full client with overlay: full_client_with_xp_area.png")
            print(f"   - XP area closeup: xp_area_closeup.png")
            print(f"   - Metadata: xp_area_metadata.json")

            return session_dir

        except Exception as e:
            print(f"[XP Watcher] Failed to save debug screenshot: {e}")
            return None

    def load_skill_templates(self, templates_dir: Optional[Path] = None) -> bool:
        """
        Load skill icon template paths from src/images/bot/skills/ directory.

        Stores paths to templates, not the images themselves (loaded on-demand).

        Args:
            templates_dir: Directory containing skill icon templates
                          Default: src/images/bot/skills/

        Returns:
            True if templates loaded successfully
        """
        if templates_dir is None:
            from utilities.imagesearch import BOT_IMAGES

            templates_dir = BOT_IMAGES / "skills"

        if not templates_dir.exists():
            print(f"[XP Watcher] Skills directory not found: {templates_dir}")
            return False

        loaded_count = 0

        for skill in skill_names():
            template_path = templates_dir / f"{skill}.png"

            if template_path.exists():
                # Store the path string, not the loaded image
                self._skill_templates[skill] = str(template_path)
                loaded_count += 1
                if self.debug:
                    print(
                        f"[XP Watcher] Loaded template path for {skill}: {template_path}"
                    )
            else:
                if self.debug:
                    print(
                        f"[XP Watcher] Template not found for {skill}: {template_path}"
                    )

        self._skill_templates_loaded = loaded_count > 0

        if self._skill_templates_loaded:
            print(
                f"[XP Watcher] Loaded {loaded_count}/{len(skill_names())} skill templates from {templates_dir.name}/"
            )
        else:
            print(f"[XP Watcher] No skill templates loaded from {templates_dir}")

        return self._skill_templates_loaded
