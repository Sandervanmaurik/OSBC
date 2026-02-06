"""
BankingMixin - Shared banking operations for OSRS bots.

Provides common banking functionality:
- Opening bank (with camera rotation retry)
- Detecting bank UI
- Depositing items (shift-click)
- Withdrawing items
- Bank slot detection

Extracted from cooking/crafting bots to eliminate duplication.
"""

import random
import time
from typing import Optional, List, Union

import utilities.color as clr
import utilities.ocr as ocr
import utilities.random_util as rd
from model.bot import BotStatus
from model.runelite_bot import RuneLiteObject
from utilities.window import BankDetectionError


class BankingMixin:
    """
    Mixin providing shared banking operations.

    This mixin expects to be mixed into a bot class that provides:
    - self.behavior: BehaviorManager
    - self.win: RuneLiteWindow
    - self.status: BotStatus
    - self.log_msg(), self.get_nearest_tag(), self.mouseover_text()
    - self._safe_key_press(), _safe_key_down(), _safe_key_up()
    """

    def open_bank(
        self, tag_color: Union[str, object, None] = None, max_attempts: int = 3
    ) -> bool:
        """
        Find and open a tagged bank with camera rotation fallback.

        Args:
            tag_color: Color to search for - can be:
                      - String: "green", "cyan", "purple", etc.
                      - Color object: clr.GREEN, clr.CYAN, etc.
                      - None: defaults to GREEN
            max_attempts: Number of camera rotation attempts (default: 3)

        Returns:
            True if bank opened successfully, False otherwise
        """
        # Convert string color names to color objects
        if tag_color is None:
            tag_color = clr.GREEN
        elif isinstance(tag_color, str):
            tag_color = self._string_to_color(tag_color)

        # Check if bank already open
        if self.is_bank_open():
            self.log_msg("Bank already open.")
            return True

        # Find bank with rotation
        bank = self._find_bank_with_rotation(tag_color, max_attempts)
        if bank is None:
            self.log_msg(
                f"Bank with tag color {tag_color} not found after {max_attempts} attempts."
            )
            return False

        # Move to bank and click
        self.behavior.mouse.move_to(bank.random_point(), mouseSpeed="medium")
        self.behavior.timing.sleep((0.2, 0.6))

        # Verify mouseover text
        if not self.mouseover_text(contains=["Bank", "Deposit"]):
            # Try clicking anyway and retry
            self.behavior.mouse.click()
            self.behavior.timing.sleep((1.0, 1.8))
            bank = self._find_bank_with_rotation(tag_color, attempts=2)
            if bank is None:
                return False
            self.behavior.mouse.move_to(bank.random_point(), mouseSpeed="medium")
            self.behavior.timing.sleep((0.2, 0.5))
            if not self.mouseover_text(contains=["Bank", "Deposit"]):
                return False

        # Click bank
        self.behavior.mouse.click()
        if not self._wait_for_bank_open():
            self.log_msg("Bank did not open, retrying...")
            self.behavior.timing.sleep((0.5, 1.0))
            return False

        return True

    def is_bank_open(self) -> bool:
        """
        Check if bank UI is currently open using OCR.

        Returns:
            True if bank UI detected, False otherwise
        """
        try:
            words = ["The Bank of Gielinor", "Gielinor", "(GE:)"]
            # Try PLAIN_12 first
            if ocr.find_text(words, self.win.game_view, ocr.PLAIN_12, [clr.OFF_ORANGE]):
                return True
            # Fallback to BOLD_12
            if ocr.find_text(words, self.win.game_view, ocr.BOLD_12, [clr.OFF_ORANGE]):
                return True
        except Exception as exc:
            self.log_msg(f"Bank UI check error: {exc}")
        return False

    def deposit_items_shift_click(self, slot_indices: List[int]) -> bool:
        """
        Deposit items from inventory using shift+click.

        Note: Shift+clicking ONE item deposits ALL items of that type.
        This method clicks the first slot in each unique item type.

        Args:
            slot_indices: List of inventory slot indices to deposit

        Returns:
            True if deposit successful, False otherwise
        """
        if not slot_indices:
            return True  # Nothing to deposit

        if not self._safe_key_down("shift"):
            return False

        try:
            if not self.win.inventory_slots:
                return False

            # Click each slot (shift-click deposits ALL of that item type)
            for slot_index in slot_indices:
                if slot_index < len(self.win.inventory_slots):
                    slot = self.win.inventory_slots[slot_index]
                    self.behavior.mouse.move_to(slot.random_point(), mouseSpeed="fast")
                    self.behavior.timing.sleep((0.05, 0.1))
                    self.behavior.mouse.click()
                    self.behavior.timing.sleep((0.15, 0.3))
        finally:
            self._safe_key_up("shift")

        self.behavior.timing.sleep((0.3, 0.7))
        return True

    def deposit_all_shift_click(self) -> bool:
        """
        Deposit all inventory items using shift+click on one slot.

        Returns:
            True if deposit successful, False otherwise
        """
        if not self._safe_key_down("shift"):
            return False

        try:
            if not self.win.inventory_slots:
                return False
            # Click any non-empty slot
            slot = random.choice(self.win.inventory_slots)
            self.behavior.mouse.move_to(slot.random_point(), mouseSpeed="fast")
            self.behavior.timing.sleep((0.1, 0.3))
            self.behavior.mouse.click()
        finally:
            self._safe_key_up("shift")

        self.behavior.timing.sleep((0.3, 0.7))
        return True

    def ensure_bank_slots_detected(self) -> bool:
        """
        Detect bank slots if not already done.

        Call this after opening the bank. Bank slots are cached after first detection.

        Returns:
            True if bank slots are detected/cached, False if detection failed
        """
        if self.win.bank_slots:
            return True  # Already detected and cached

        try:
            self.win.locate_bank_slots(verbose=False)
            self.log_msg(f"Detected {len(self.win.bank_slots)} bank slots")
            return True
        except BankDetectionError as e:
            self.log_msg(f"Bank slot detection failed: {e}")
            return False

    def _find_bank_with_rotation(
        self, tag_color, attempts: int = 3
    ) -> Optional[RuneLiteObject]:
        """
        Find bank with camera rotation fallback.

        Args:
            tag_color: Color to search for
            attempts: Number of rotation attempts

        Returns:
            RuneLiteObject if found, None otherwise
        """
        for attempt in range(attempts):
            bank = self.get_nearest_tag(tag_color)
            if bank is not None:
                return bank
            if attempt < attempts - 1:
                self.log_msg(
                    f"Bank not found, rotating camera (attempt {attempt + 1}/{attempts})"
                )
                self._rotate_camera_search()
                self.behavior.timing.sleep((0.5, 1.2))
        return None

    def _wait_for_bank_open(self, timeout_seconds: float = 8.0) -> bool:
        """
        Wait for bank interface to open.

        Args:
            timeout_seconds: Maximum time to wait

        Returns:
            True if bank opened, False if timeout
        """
        start = time.time()
        while time.time() - start < timeout_seconds:
            if self.status != BotStatus.RUNNING:
                return False
            if self.is_bank_open():
                return True
            self.behavior.timing.sleep((0.12, 0.25))
        return False

    def _rotate_camera_search(self) -> None:
        """
        Rotate camera slightly to search for bank.

        Randomly rotates left or right for 0.3-0.8 seconds.
        """
        key = "left" if random.random() < 0.5 else "right"

        if not self._safe_key_down(key):
            return

        try:
            duration = rd.truncated_normal_sample(0.3, 0.8, mean=0.5, std=0.15)
            self.behavior.timing.sleep((duration, duration))
        finally:
            self._safe_key_up(key)

    def _string_to_color(self, color_name: str):
        """
        Convert string color name to color object.

        Args:
            color_name: Color name (e.g., "green", "cyan", "purple")

        Returns:
            Color object from utilities.color

        Raises:
            ValueError: If color name not recognized
        """
        color_map = {
            "green": clr.GREEN,
            "cyan": clr.CYAN,
            "purple": clr.PURPLE,
            "red": clr.RED,
            "blue": clr.BLUE,
            "yellow": clr.YELLOW,
            "orange": clr.ORANGE,
            "white": clr.WHITE,
            "black": clr.BLACK,
        }

        color_lower = color_name.lower()
        if color_lower not in color_map:
            raise ValueError(
                f"Unknown color name: {color_name}. "
                f"Valid options: {', '.join(color_map.keys())}"
            )

        return color_map[color_lower]
