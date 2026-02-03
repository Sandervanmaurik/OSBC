import random
import time
from typing import Callable, Dict, List, Optional, Tuple

import utilities.color as clr
import utilities.imagesearch as imsearch
import utilities.ocr as ocr
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
from model.runelite_bot import RuneLiteObject
from utilities.geometry import Rectangle
from utilities.window import BankDetectionError

# === Import behavior system ===
from utilities.behavior import BehaviorManager
from utilities.behavior.profiles import MouseProfile, CameraProfile


class OSRSCrafting(OSRSBot):
    """
    Crafting bot for OSRS - bank-standing activities.

    Current method: Cutting gems (chisel + uncut gem → cut gem)

    MIGRATED TO BEHAVIOR SYSTEM:
    - Uses BehaviorManager with "focused" profile
    - Ultra-minimal camera movement (1-20 min intervals for bank-standing)
    - Smart chisel detection (only withdraw if missing)
    - Item click order randomization
    - Text-based activity monitoring ("Cutting")
    - Handles crushed gems as byproducts
    """

    CRAFTING_METHODS = ["Cutting gems"]

    GEM_TYPES = ["Opal", "Sapphire", "Emerald", "Ruby", "Diamond"]

    ITEM_TEMPLATES: Dict[str, Callable[[str], Tuple[str, str, str]]] = {
        "Cutting gems": lambda gem_type: (
            "chisel.png",
            f"uncut_{gem_type.lower()}.png",
            f"{gem_type.lower()}.png",
        ),
    }

    BYPRODUCT_TEMPLATE = "crushed_gem.png"  # Can be created from any gem type

    def __init__(self) -> None:
        bot_title = "Crafting"
        description = (
            "Cuts uncut gems using a chisel at the bank. "
            "Supports multiple gem types with crushed gem handling. "
            "Ultra-minimal camera movement, human-like timing patterns."
        )
        super().__init__(bot_title=bot_title, description=description)

        self.running_time = 60  # minutes
        self.crafting_method = "Cutting gems"
        self.gem_type = "Opal"  # Default gem type

        # Enable default options
        self.options_set = True

        self._item_confidence = 0.1
        self._inventory_item_confidence = 0.1
        self._missing_item_cycles = 0
        self._max_missing_cycles = 3

        # Item click order randomization
        self._prefer_chisel_first = True
        self._order_flip_chance = 0.25

        # Crafting timeouts
        self._cutting_start_timeout = 3.0
        self._cutting_end_timeout = 55.0

        # === Initialize behavior system ===
        # Bank-standing profiles: minimal camera, frequent mouse fidgeting
        self.behavior = BehaviorManager(
            bot=self,
            profile="high-active",  # Fast, efficient profile
            mouse_profile=MouseProfile.BANK_STANDING,
            camera_profile=CameraProfile.BANK_STANDING,
            custom_config={
                "timing": {
                    "speed_multiplier": 0.9,  # Slightly slower than fletching
                },
                "mouse": {
                    "default_speed": "fast",
                },
                "action": {
                    "misclick_chance": 0.05,  # Low for repetitive task
                    "hesitation_chance": 0.08,
                },
                "attention": {
                    "skill_check_enabled": False,
                    "inventory_check_enabled": False,
                },
                "breaks": {
                    "enabled": True,  # Optional for bank-standing
                },
            },
        )

    def create_options(self) -> None:
        self.options_builder.add_slider_option(
            "running_time", "How long to run (minutes)?", 50, 500
        )
        self.options_builder.add_dropdown_option(
            "crafting_method", "Crafting method", self.CRAFTING_METHODS
        )
        # Conditional option: only show gem type if "Cutting gems" is selected
        if self.crafting_method == "Cutting gems":
            self.options_builder.add_dropdown_option(
                "gem_type", "Gem type", self.GEM_TYPES
            )

    def save_options(self, options: dict) -> None:
        for option in options:
            if option == "running_time":
                self.running_time = int(options[option])
            elif option == "crafting_method":
                self.crafting_method = options[option]
            elif option == "gem_type":
                self.gem_type = options[option]
            else:
                self.log_msg(f"Unknown option: {option}")
                self.options_set = False
                return

        self.log_msg(f"Running time: {self.running_time} minutes")
        self.log_msg(f"Crafting method: {self.crafting_method}")
        if self.crafting_method == "Cutting gems":
            self.log_msg(f"Gem type: {self.gem_type}")
        self.options_set = True

    def main_loop(self) -> None:
        self.log_msg("Starting crafting bot...")

        if not self._ensure_inventory_ready():
            self._stop_with_message(
                "Inventory slots unavailable. Open the inventory tab and try again."
            )
            return

        self._open_inventory_tab()
        # === Initialize behavior display ===
        self.behavior.log_stats_summary(self.log_msg)
        if hasattr(self, "controller") and self.controller:
            self.controller.update_behavior_display()

        # Track time for periodic stats logging
        import time

        last_stats_log = time.time()
        stats_log_interval = 30  # 30 seconds

        with self.timed_session(self.running_time) as session:
            self.behavior.start_fidgeting(self)
            try:
                while session.running:
                    if self._should_stop():
                        break

                    # === Ultra-minimal attention behaviors ===
                    self.behavior.attention.perform_random_behaviors()

                    # === Periodic stats logging (every 5 minutes) ===
                    now = time.time()
                    if now - last_stats_log >= stats_log_interval:
                        self.behavior.log_stats_summary(self.log_msg)
                        if hasattr(self, "controller") and self.controller:
                            stats = self.behavior.get_stats_summary()
                            self.controller.update_behavior_display(stats=stats)
                        last_stats_log = now

                    # State machine
                    if self.crafting_method == "Cutting gems":
                        # Build templates dynamically based on gem type
                        template_builder = self.ITEM_TEMPLATES.get(self.crafting_method)
                        if not template_builder:
                            self._stop_with_message(
                                f"No templates defined for method: {self.crafting_method}"
                            )
                            break

                        tool_tmpl, input_tmpl, output_tmpl = template_builder(
                            self.gem_type
                        )

                        if not self._cutting_gems_cycle(
                            tool_tmpl, input_tmpl, output_tmpl
                        ):
                            # === Use behavior system for sleep ===
                            self.behavior.timing.sleep((0.15, 0.4))
                            continue
                    else:
                        self._stop_with_message(
                            f"Unsupported method: {self.crafting_method}"
                        )
                        break

                    session.increment("cycles")
            finally:
                self.behavior.stop_fidgeting()

        self.log_msg("Crafting session complete.")
        if self.status == BotStatus.RUNNING:
            self.set_status(BotStatus.STOPPED)

    def _cutting_gems_cycle(
        self, tool_template: str, input_template: str, output_template: str
    ) -> bool:
        """
        Main gem cutting cycle: check items → withdraw → craft → deposit.

        Args:
            tool_template: Template filename for tool (e.g., "chisel.png")
            input_template: Template filename for input item (e.g., "uncut_opal.png")
            output_template: Template filename for output item (e.g., "opal.png")
        """
        tool_slots, input_slots = self._find_crafting_slots(
            tool_template, input_template
        )

        # Check if we need to bank
        if not tool_slots or not input_slots:
            self.log_msg("Missing items, need to visit bank...")
            return self._handle_banking(tool_template, input_template, output_template)

        # We have items, let's craft
        return self._craft_gems(tool_slots, input_slots)

    def _handle_banking(
        self, tool_template: str, input_template: str, output_template: str
    ) -> bool:
        """
        Handle banking: always deposit products first, then withdraw supplies.

        Args:
            tool_template: Template for tool (chisel)
            input_template: Template for input item (uncut gem)
            output_template: Template for output item (cut gem)
        """
        # Open bank
        if not self._open_bank():
            self.log_msg("Failed to open bank.")
            return False

        # Ensure bank slots are detected
        if not self._ensure_bank_slots_detected():
            self.log_msg("Cannot perform banking: bank slot detection failed.")
            self._safe_key_press("escape")
            return False

        # Always check for and deposit cut gems + crushed gems first
        cut_gem_slots, crushed_gem_slots = self._find_product_slots(output_template)
        total_products = len(cut_gem_slots) + len(crushed_gem_slots)

        if total_products > 0:
            self.log_msg(
                f"Found {len(cut_gem_slots)} cut gems and {len(crushed_gem_slots)} crushed gems, depositing..."
            )
            if not self._deposit_products_shift_click(cut_gem_slots, crushed_gem_slots):
                return False

        # Now withdraw supplies (tool if needed, then input items)
        return self._withdraw_supplies(tool_template, input_template)

    def _craft_gems(self, tool_slots: List[int], input_slots: List[int]) -> bool:
        """
        Craft gems by using tool on input item.
        """
        # Randomly flip item click order
        if random.random() < self._order_flip_chance:
            self._prefer_chisel_first = not self._prefer_chisel_first

        if self._prefer_chisel_first:
            primary_slots, secondary_slots = tool_slots, input_slots
        else:
            primary_slots, secondary_slots = input_slots, tool_slots

        # Pick random slots
        primary_slot = random.choice(primary_slots)
        secondary_slot = random.choice(secondary_slots)

        # Click items
        if not self._click_inventory_slot(primary_slot):
            return False
        # === Use behavior system for micro-delay ===
        self.behavior.timing.sleep((0.03, 0.08))
        if not self._click_inventory_slot(secondary_slot):
            return False

        # Press spacebar with randomized delay
        if not self._press_space_to_confirm():
            return False

        # Wait for "Cutting" to start
        if not self._wait_for_cutting_start(
            timeout_seconds=self._cutting_start_timeout
        ):
            # Try spacebar again
            if not self._press_space_to_confirm():
                return False
            if not self._wait_for_cutting_start(
                timeout_seconds=self._cutting_start_timeout
            ):
                self.log_msg("Crafting did not start (no 'Cutting' text).")
                return False

        # Wait for cutting to end
        return self._wait_for_cutting_end(timeout_seconds=self._cutting_end_timeout)

    def _find_crafting_slots(
        self, tool_template: str, input_template: str
    ) -> Tuple[List[int], List[int]]:
        """
        Find tool and input item slots in inventory.

        Args:
            tool_template: Template filename for tool
            input_template: Template filename for input item
        """
        if not self.win.inventory_slots:
            return ([], [])

        tool_path = self._get_item_template_path(tool_template)
        input_path = self._get_item_template_path(input_template)

        tool_slots = self.find_item_in_inventory_visual(
            tool_path, confidence=self._inventory_item_confidence
        )
        input_slots = self.find_item_in_inventory_visual(
            input_path, confidence=self._inventory_item_confidence
        )
        return (tool_slots, input_slots)

    def _find_product_slots(self, output_template: str) -> Tuple[List[int], List[int]]:
        """
        Find product slots in inventory (cut gems + crushed gems).

        Args:
            output_template: Template filename for primary output (cut gem)

        Returns:
            Tuple of (cut_gem_slots, crushed_gem_slots)
        """
        if not self.win.inventory_slots:
            return ([], [])

        output_path = self._get_item_template_path(output_template)
        byproduct_path = self._get_item_template_path(self.BYPRODUCT_TEMPLATE)

        # Find both cut gems and crushed gems
        cut_gem_slots = self.find_item_in_inventory_visual(
            output_path, confidence=self._item_confidence
        )
        crushed_gem_slots = self.find_item_in_inventory_visual(
            byproduct_path, confidence=self._item_confidence
        )

        return (cut_gem_slots, crushed_gem_slots)

    def _get_item_template_path(self, filename: str) -> str:
        """Get path to item template image."""
        # Tools go in "tools" subfolder, others in "items"
        if filename == "chisel.png":
            return str(imsearch.get_template_path("tools", filename))
        else:
            return str(imsearch.get_template_path("items", filename))

    def _click_inventory_slot(self, slot_index: int) -> bool:
        """Click an inventory slot with human-like behavior."""
        if not self.win.inventory_slots or slot_index >= len(self.win.inventory_slots):
            return False

        slot = self.win.inventory_slots[slot_index]
        try:
            click_point = slot.random_point()
            # === Use behavior system for mouse movement ===
            self.behavior.mouse.move_to(
                click_point, mouseSpeed=random.choice(["fastest", "fast", "fastest"])
            )
            # === Use behavior system for pre-click delay ===
            self.behavior.timing.sleep((0.02, 0.06))
            # === Use behavior system for clicking ===
            self.behavior.mouse.click()
            return True
        except Exception as exc:
            self.log_msg(f"Inventory click error: {exc}")
            return False

    def _press_space_to_confirm(self) -> bool:
        """Press spacebar with randomized delay (1-2 seconds)."""
        # === Use behavior system for delay before spacebar ===
        import utilities.random_util as rd

        delay = rd.truncated_normal_sample(1.0, 2.0, mean=1.5, std=0.3)
        time.sleep(delay)

        if not self._safe_key_press("space"):
            self.log_msg("Failed to press space (window focus lost).")
            return False

        # === Use behavior system for delay after ===
        self.behavior.timing.sleep((0.03, 0.08))
        return True

    def _wait_for_cutting_start(self, timeout_seconds: float) -> bool:
        """Wait for 'Cutting' text to appear."""
        start = time.time()
        while time.time() - start < timeout_seconds:
            if self._should_stop():
                return False
            if self._is_cutting():
                return True
            # === Use behavior system for polling delay ===
            self.behavior.timing.sleep((0.08, 0.18))
        return False

    def _wait_for_cutting_end(self, timeout_seconds: float) -> bool:
        """Wait for 'Cutting' text to disappear."""
        start = time.time()
        last_log = 0.0
        while time.time() - start < timeout_seconds:
            if self._should_stop():
                return False
            if not self._is_cutting():
                return True
            if time.time() - last_log > 6.0:
                self.log_msg("Cutting... waiting for completion.")
                last_log = time.time()
            # === Use behavior system for polling delay ===
            self.behavior.timing.sleep((0.2, 0.6))
        self.log_msg("Cutting wait timed out; retrying cycle.")
        return False

    def _is_cutting(self) -> bool:
        """Check if 'Cutting' text is visible (crafting in progress)."""
        rects = self._get_action_text_rects()
        if not rects:
            return False

        colors = [clr.WHITE, clr.OFF_WHITE, clr.OFF_YELLOW]
        for rect in rects:
            if ocr.find_text("Cutting", rect, ocr.BOLD_12, colors):
                return True
            if ocr.find_text("Cutting", rect, ocr.PLAIN_12, colors):
                return True

            extracted = ocr.extract_text(rect, ocr.BOLD_12, colors)
            if "Cutting" in extracted:
                return True
            extracted = ocr.extract_text(rect, ocr.PLAIN_12, colors)
            if "Cutting" in extracted:
                return True

        return False

    def _get_action_text_rects(self) -> List[Rectangle]:
        """Get rectangles where action text appears (top-left of game view)."""
        rects: List[Rectangle] = []

        # Primary action text area
        if hasattr(self.win, "current_action") and self.win.current_action:
            rects.append(self.win.current_action)

        # Fallback: top-left corner of game view
        if self.win and self.win.game_view:
            gv = self.win.game_view
            rects.append(
                Rectangle(gv.left, gv.top, min(320, gv.width), min(90, gv.height))
            )

        return rects

    # === BANKING LOGIC ===

    def _ensure_bank_slots_detected(self) -> bool:
        """
        Detect bank slots if not already done. Call after bank opens.

        Returns:
            True if bank slots are detected/cached, False if detection failed.
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

    def _withdraw_supplies(self, tool_template: str, input_template: str) -> bool:
        """
        Withdraw tool (if needed) and input items from bank.
        Bank must already be open when calling this method.

        Args:
            tool_template: Template filename for tool (e.g., "chisel.png")
            input_template: Template filename for input item (e.g., "uncut_opal.png")
        """
        # Smart tool detection
        tool_slots, _ = self._find_crafting_slots(tool_template, input_template)
        if not tool_slots:
            self.log_msg(f"No {tool_template} found, withdrawing 1...")
            # Search for tool in bank slots
            tool_path = self._get_item_template_path(tool_template)
            result = self.find_item_in_bank_visual(
                tool_path, confidence=self._item_confidence
            )
            if result:
                tool_slot, slot_index = result
                self.behavior.mouse.move_to(tool_slot.random_point(), mouseSpeed="fast")
                self.behavior.timing.sleep((0.1, 0.2))
                self.behavior.mouse.click()
                self.behavior.timing.sleep((0.3, 0.6))
            else:
                self.log_msg(f"{tool_template} not found in bank!")
                self._safe_key_press("escape")
                return False
        else:
            self.log_msg(f"{tool_template} already in inventory, skipping...")

        # Withdraw input items (click to fill inventory)
        self.log_msg(f"Withdrawing {input_template}...")
        input_path = self._get_item_template_path(input_template)
        result = self.find_item_in_bank_visual(
            input_path, confidence=self._item_confidence
        )

        if result:
            input_slot, slot_index = result
            self.behavior.mouse.move_to(input_slot.random_point(), mouseSpeed="fast")
            self.behavior.timing.sleep((0.1, 0.2))
            self.behavior.mouse.click()
            self.behavior.timing.sleep((0.3, 0.6))
        else:
            self.log_msg(f"{input_template} not found in bank! Stopping...")
            self._safe_key_press("escape")
            return False

        # Close bank
        self._safe_key_press("escape")
        self.behavior.timing.sleep((0.4, 0.9))
        return True

    def _deposit_products_shift_click(
        self, cut_gem_slots: List[int], crushed_gem_slots: List[int]
    ) -> bool:
        """
        Deposit cut gems and crushed gems using shift+click.
        Bank must already be open when calling this method.
        Does NOT close the bank after depositing.

        Note: Shift+clicking ONE item deposits ALL items of that type.
        We click one cut gem (deposits all cut gems) and one crushed gem (deposits all crushed gems).

        Args:
            cut_gem_slots: List of inventory slot indices containing cut gems
            crushed_gem_slots: List of inventory slot indices containing crushed gems

        Returns:
            True if deposit successful, False otherwise
        """
        if not cut_gem_slots and not crushed_gem_slots:
            return True  # Nothing to deposit

        if not self._safe_key_down("shift"):
            return False

        try:
            if not self.win.inventory_slots:
                return False

            # Shift+click ONE cut gem to deposit ALL cut gems
            if cut_gem_slots:
                slot_index = cut_gem_slots[0]
                if slot_index < len(self.win.inventory_slots):
                    slot = self.win.inventory_slots[slot_index]
                    self.behavior.mouse.move_to(slot.random_point(), mouseSpeed="fast")
                    self.behavior.timing.sleep((0.05, 0.1))
                    self.behavior.mouse.click()
                    self.behavior.timing.sleep((0.15, 0.3))

            # Shift+click ONE crushed gem to deposit ALL crushed gems
            if crushed_gem_slots:
                slot_index = crushed_gem_slots[0]
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

    def _open_bank(self) -> bool:
        """Find and open green-tagged bank."""
        # Check if bank already open
        if self._bank_interface_visible():
            self.log_msg("Bank already open.")
            return True

        # Find green-tagged bank
        bank = self._find_bank_with_rotation()
        if bank is None:
            self.log_msg("Green-tagged bank not found.")
            return False

        # Move to bank and click
        self.behavior.mouse.move_to(bank.random_point(), mouseSpeed="medium")
        self.behavior.timing.sleep((0.2, 0.6))

        if not self.mouseover_text(contains=["Bank", "Deposit"]):
            self.behavior.mouse.click()
            self.behavior.timing.sleep((1.0, 1.8))
            bank = self._find_bank_with_rotation(attempts=2)
            if bank is None:
                return False
            self.behavior.mouse.move_to(bank.random_point(), mouseSpeed="medium")
            self.behavior.timing.sleep((0.2, 0.5))
            if not self.mouseover_text(contains=["Bank", "Deposit"]):
                return False

        self.behavior.mouse.click()
        if not self._wait_for_bank_open():
            self.log_msg("Bank did not open, retrying...")
            self.behavior.timing.sleep((0.5, 1.0))
            return False

        return True

    def _find_tagged_bank(self) -> Optional[RuneLiteObject]:
        """Find bank marked with GREEN outline."""
        bank = self.get_nearest_tag(clr.GREEN)
        return bank

    def _find_bank_with_rotation(self, attempts: int = 3) -> Optional[RuneLiteObject]:
        """Find bank, rotating camera if needed."""
        for attempt in range(attempts):
            bank = self._find_tagged_bank()
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
        """Wait for bank interface to open."""
        start = time.time()
        while time.time() - start < timeout_seconds:
            if self.status != BotStatus.RUNNING:
                return False
            if self._bank_interface_visible():
                return True
            self.behavior.timing.sleep((0.12, 0.25))
        return False

    def _bank_interface_visible(self) -> bool:
        """Check if bank UI is open using OCR."""
        try:
            words = ["The Bank of Gielinor", "Gielinor", "(GE:)"]
            if ocr.find_text(words, self.win.game_view, ocr.PLAIN_12, [clr.OFF_ORANGE]):
                return True
            if ocr.find_text(words, self.win.game_view, ocr.BOLD_12, [clr.OFF_ORANGE]):
                return True
        except Exception as exc:
            self.log_msg(f"Bank UI check error: {exc}")
        return False

    def _deposit_all_shift_click(self) -> bool:
        """Deposit all items using shift+click."""
        if not self._safe_key_down("shift"):
            return False
        try:
            if not self.win.inventory_slots:
                return False
            slot = random.choice(self.win.inventory_slots)
            self.behavior.mouse.move_to(slot.random_point(), mouseSpeed="fast")
            self.behavior.timing.sleep((0.1, 0.3))
            self.behavior.mouse.click()
        finally:
            self._safe_key_up("shift")
        self.behavior.timing.sleep((0.3, 0.7))
        self._safe_key_press("escape")
        self.behavior.timing.sleep((0.4, 0.9))
        return True

    def _rotate_camera_search(self) -> None:
        """Rotate camera slightly to search for bank."""
        if random.random() < 0.5:
            self._safe_key_down("left")
        else:
            self._safe_key_down("right")

        import utilities.random_util as rd

        duration = rd.truncated_normal_sample(0.3, 0.8, mean=0.5, std=0.15)
        time.sleep(duration)

        self._safe_key_up("left")
        self._safe_key_up("right")

    # === UTILITY METHODS ===

    def _open_inventory_tab(self) -> None:
        """Open inventory tab."""
        if len(self.win.cp_tabs) > 3:
            self.behavior.mouse.move_to(
                self.win.cp_tabs[3].random_point(), mouseSpeed="fast"
            )
            self.behavior.mouse.click()
            self.behavior.timing.sleep((0.15, 0.35))

    def _ensure_inventory_ready(self) -> bool:
        """Check if inventory slots are available."""
        if not self.win or not self.win.inventory_slots:
            return False
        return True

    def _should_stop(self) -> bool:
        """Check if bot should stop."""
        if self.status != BotStatus.RUNNING:
            return True
        if self.thread is None or not self.thread.is_alive():
            return True
        return False

    def _stop_with_message(self, message: str) -> None:
        """Stop bot with a message."""
        self.log_msg(message)
        self.set_status(BotStatus.STOPPED)
