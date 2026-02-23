"""
BankingMixin - Shared banking operations for OSRS bots.

Provides common banking functionality:
- Opening bank (with camera rotation retry)
- Detecting bank UI
- Depositing items (shift-click or by item name)
- Withdrawing items (by item name)
- Bank slot detection

Extracted from cooking/crafting bots to eliminate duplication.
"""

import random
import time
from typing import Optional, List, Union, Dict, TYPE_CHECKING

import utilities.color as clr
import utilities.ocr as ocr
import utilities.random_util as rd
from model.bot import BotStatus
from model.runelite_bot import RuneLiteObject
from utilities.window import BankDetectionError

if TYPE_CHECKING:
    from model.osrs.mixins.bot_protocol import BotProtocol


class BankingMixin:
    """
    Mixin providing shared banking operations.

    This mixin expects to be mixed into a bot class that provides:
    - self.behavior: BehaviorManager
    - self.win: RuneLiteWindow
    - self.status: BotStatus
    - self.log_msg(), self.get_nearest_tag(), self.mouseover_text()
    - self._safe_key_press(), _safe_key_down(), _safe_key_up()
    - self.get_template_path() (from TemplateMixin)
    - self.find_items_in_inventory() (from ItemInteractionMixin)
    - self.find_item_in_bank() (from ItemInteractionMixin)
    """

    if TYPE_CHECKING:
        from utilities.behavior import BehaviorManager
        from model.runelite_bot import RuneLiteWindow
        from utilities.geometry import Point

        behavior: "BehaviorManager"
        win: "RuneLiteWindow"
        status: BotStatus

        def log_msg(self: "BotProtocol", msg: str, overwrite: bool = False) -> None: ...
        def get_template_path(
            self: "BotProtocol", filename: str, category: str = "items"
        ) -> str: ...
        def find_items_in_inventory(
            self: "BotProtocol", template_path: str, confidence: float = 0.3
        ) -> List[int]: ...
        def find_item_in_bank(
            self: "BotProtocol", template_path: str, confidence: float = 0.3
        ): ...
        def get_nearest_tag(
            self: "BotProtocol", color, search_rect=None
        ) -> Optional[RuneLiteObject]: ...
        def mouseover_text(
            self: "BotProtocol", contains: Union[str, List[str]], **kwargs
        ) -> bool: ...
        def _safe_key_down(self: "BotProtocol", key: str) -> bool: ...
        def _safe_key_up(self: "BotProtocol", key: str) -> bool: ...
        def _ensure_focus(self: "BotProtocol") -> bool: ...

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
        self.banking_hesitation()

        # Verify mouseover text
        if not self.mouseover_text(contains=["Bank", "Deposit"]):
            # Try clicking anyway and retry
            self.behavior.mouse.click()
            self.behavior.timing.sleep((1.0, 1.8))
            bank = self._find_bank_with_rotation(tag_color, attempts=2)
            if bank is None:
                return False
            self.behavior.mouse.move_to(bank.random_point(), mouseSpeed="medium")
            self.banking_hesitation()
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
                    self.banking_click_delay()
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

    def deposit_items(
        self: "BotProtocol",
        items: Dict[str, Union[int, str]],
        exclude_slots: Optional[List[int]] = None,
        confidence: float = 0.2,
    ) -> bool:
        """
        Deposit items from inventory by template name.

        Args:
            items: Dict mapping item template names to quantities
                   e.g., {"cooked_shrimp.png": "all", "burnt_fish.png": "all"}
                   Currently only "all" is supported (shift-click deposit)
            exclude_slots: Inventory slots to never deposit (e.g., [0] for catalyst)

        Returns:
            True if deposit successful, False otherwise

        Example:
            # Deposit all cooked/burnt fish, but keep item in slot 0
            self.deposit_items(
                {"cooked_shrimp.png": "all", "burnt_fish.png": "all"},
                exclude_slots=[0]
            )
        """
        if not items:
            return True  # Nothing to deposit

        slots_to_deposit = []

        for template_name, quantity in items.items():
            # Get full template path
            template_path = self.get_template_path(template_name, category="items")

            # Find items in inventory
            item_slots = self.find_items_in_inventory(
                template_path, confidence=confidence
            )

            # Apply exclusion filter
            if exclude_slots:
                item_slots = [slot for slot in item_slots if slot not in exclude_slots]

            # For "all", we only need one slot per item type (shift-click deposits all)
            if quantity == "all" and item_slots:
                slots_to_deposit.append(item_slots[0])
            # Future: support specific quantities
            # elif isinstance(quantity, int):
            #     slots_to_deposit.extend(item_slots[:quantity])

        if not slots_to_deposit:
            self.log_msg("No items found to deposit")
            return True  # Not an error if nothing to deposit

        self.log_msg(f"Depositing {len(slots_to_deposit)} item type(s)...")
        return self.deposit_items_shift_click(slots_to_deposit)

    def withdraw_items(
        self: "BotProtocol", items: Dict[str, Union[int, str]], confidence: float = 0.1
    ) -> bool:
        """
        Withdraw items from bank by template name.

        Args:
            items: Dict mapping item template names to quantities
                   e.g., {"raw_shrimp.png": "all"}
                   Currently only "all" is supported (single left-click withdraws 28)

        Returns:
            True if all withdrawals successful, False otherwise

        Example:
            # Withdraw raw shrimp (fills inventory)
            self.withdraw_items({"raw_shrimp.png": "all"})
        """
        if not items:
            return True

        for template_name, quantity in items.items():
            # Get full template path
            template_path = self.get_template_path(template_name, category="items")

            # Find item in bank
            result = self.find_item_in_bank(template_path, confidence=confidence)

            if not result:
                self.log_msg(f"{template_name} not found in bank! Stopping...")
                return False

            bank_slot, slot_index = result

            # For "all", single left-click withdraws 28 items (default behavior)
            if quantity == "all":
                self.log_msg(f"Withdrawing {template_name}...")
                self.behavior.mouse.move_to(bank_slot.random_point(), mouseSpeed="fast")
                self.behavior.timing.sleep((0.1, 0.2))
                self.behavior.mouse.click()
                self.behavior.timing.sleep((0.3, 0.6))
            # Future: support specific quantities with right-click menu
            # elif isinstance(quantity, int):
            #     # Right-click -> Withdraw-X -> Type quantity
            #     pass

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
        self, tag_color, attempts: int = 8
    ) -> Optional[RuneLiteObject]:
        """
        Find bank with progressive camera rotation and recovery actions.

        Uses a multi-stage search strategy similar to mining bot:
        1. Initial rotation attempts (light search)
        2. Zoom adjustments (change perspective)
        3. Larger camera movements (thorough search)
        4. Mini adjustments (fine-tune view)

        Args:
            tag_color: Color to search for
            attempts: Maximum number of search attempts (default: 8)

        Returns:
            RuneLiteObject if found, None otherwise
        """
        for attempt in range(attempts):
            # Check for bank in current view
            bank = self.get_nearest_tag(tag_color)
            if bank is not None:
                return bank

            # Don't try recovery actions on the last attempt
            if attempt >= attempts - 1:
                break

            # Log search attempt
            self.log_msg(
                f"Bank not found, trying recovery action (attempt {attempt + 1}/{attempts})"
            )

            # Progressive recovery actions (similar to mining bot's _run_recovery)
            stage = attempt % 6  # Cycle through 6 different recovery actions

            if stage == 0:
                # Light camera rotation
                self._rotate_camera_search()
            elif stage == 1:
                # Zoom out for wider view
                self._zoom_out_banking()
            elif stage == 2:
                # Larger rotation
                self._rotate_camera_search_large()
            elif stage == 3:
                # Zoom in for closer view
                self._zoom_in_banking()
            elif stage == 4:
                # Mini camera adjustment (vertical + small horizontal)
                self._mini_camera_adjust_banking()
            elif stage == 5:
                # Full rotation to opposite direction
                self._rotate_camera_search_opposite()

            # Wait for camera to settle and UI to update
            self.behavior.timing.sleep((0.6, 1.4))

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
            self.banking_wait_open_poll()
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

    def _rotate_camera_search_large(self) -> None:
        """
        Rotate camera more significantly to search for bank.

        Similar to mining bot's _rotate_camera_search - larger movements.
        """
        try:
            # Random direction, larger rotation
            key = "left" if random.random() < 0.5 else "right"

            if not self._safe_key_down(key):
                return

            try:
                # Longer duration for bigger rotation
                duration = rd.truncated_normal_sample(0.8, 1.6, mean=1.2, std=0.25)
                self.behavior.timing.sleep((duration, duration))
            finally:
                self._safe_key_up(key)

            self.behavior.timing.sleep((0.2, 0.5))
        except Exception as exc:
            self.log_msg(f"Large camera rotation error: {exc}")

    def _rotate_camera_search_opposite(self) -> None:
        """
        Rotate camera in the opposite direction for full 360° coverage.

        Useful when bank might be just out of view behind the player.
        """
        try:
            # Pick a direction and rotate significantly
            key = random.choice(["left", "right"])

            if not self._safe_key_down(key):
                return

            try:
                # Very long duration for near-180° turn
                duration = rd.truncated_normal_sample(1.5, 2.5, mean=2.0, std=0.3)
                self.behavior.timing.sleep((duration, duration))
            finally:
                self._safe_key_up(key)

            self.behavior.timing.sleep((0.3, 0.7))
        except Exception as exc:
            self.log_msg(f"Opposite camera rotation error: {exc}")

    def _mini_camera_adjust_banking(self) -> None:
        """
        Make small camera adjustments (vertical tilt + small horizontal).

        Sometimes bank is visible but at an awkward angle.
        """
        try:
            # Small vertical adjustment (up/down arrow keys)
            if random.random() < 0.7:
                v_key = "up" if random.random() < 0.5 else "down"
                if self._safe_key_down(v_key):
                    try:
                        duration = rd.truncated_normal_sample(
                            0.15, 0.4, mean=0.25, std=0.08
                        )
                        self.behavior.timing.sleep((duration, duration))
                    finally:
                        self._safe_key_up(v_key)
                    self.behavior.timing.sleep((0.1, 0.2))

            # Small horizontal adjustment
            if random.random() < 0.6:
                h_key = "left" if random.random() < 0.5 else "right"
                if self._safe_key_down(h_key):
                    try:
                        duration = rd.truncated_normal_sample(
                            0.2, 0.5, mean=0.35, std=0.1
                        )
                        self.behavior.timing.sleep((duration, duration))
                    finally:
                        self._safe_key_up(h_key)

        except Exception as exc:
            self.log_msg(f"Mini camera adjust error: {exc}")

    def _zoom_out_banking(self) -> None:
        """
        Zoom out for better view when searching for bank.

        Wider FOV can help spot tagged banks that are slightly off-screen.
        """
        self.log_msg("Zooming out to search for bank...")
        try:
            import pyautogui as pag

            if not self._ensure_focus():
                self.log_msg("Cannot zoom out, game not focused.")
                return

            center = self.win.game_view.get_center()
            self.behavior.mouse.move_to(center, mouseSpeed="fast")
            self.behavior.timing.sleep((0.1, 0.25))

            # Scroll out 3-5 times
            scroll_clicks = random.randint(3, 5)
            for _ in range(scroll_clicks):
                pag.scroll(-240)
                self.behavior.timing.sleep((0.05, 0.12))

            self.behavior.timing.sleep((0.2, 0.4))
        except Exception as exc:
            self.log_msg(f"Zoom out error: {exc}")

    def _zoom_in_banking(self) -> None:
        """
        Zoom in for closer view when searching for bank.

        Sometimes tags are small and easier to see when zoomed in.
        """
        self.log_msg("Zooming in to search for bank...")
        try:
            import pyautogui as pag

            if not self._ensure_focus():
                self.log_msg("Cannot zoom in, game not focused.")
                return

            center = self.win.game_view.get_center()
            self.behavior.mouse.move_to(center, mouseSpeed="fast")
            self.behavior.timing.sleep((0.1, 0.25))

            # Scroll in 2-4 times
            scroll_clicks = random.randint(2, 4)
            for _ in range(scroll_clicks):
                pag.scroll(240)
                self.behavior.timing.sleep((0.05, 0.12))

            self.behavior.timing.sleep((0.2, 0.4))
        except Exception as exc:
            self.log_msg(f"Zoom in error: {exc}")

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
