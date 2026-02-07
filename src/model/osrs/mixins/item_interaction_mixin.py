"""
ItemInteractionMixin - Shared item interaction operations for OSRS bots.

Provides common inventory/bank item interaction functionality:
- Clicking inventory slots
- Using item on item (with fidgeting pause)
- Pressing spacebar to confirm
- Finding items in inventory/bank

Extracted from cooking/crafting/fletching bots to eliminate duplication.
"""

import random
from typing import List, Tuple, Optional, TYPE_CHECKING

import utilities.random_util as rd
from utilities.geometry import Rectangle

if TYPE_CHECKING:
    from utilities.behavior import BehaviorManager
    from model.runelite_bot import RuneLiteWindow
    from model.osrs.mixins.bot_protocol import BotProtocol


class ItemInteractionMixin:
    """
    Mixin providing shared item interaction operations.

    Requires the following from the bot class:
    - self.behavior (BehaviorManager instance)
    - self.win (Window instance with inventory_slots)
    - self.log_msg() method
    - self.find_item_in_inventory_visual() method
    - self.find_item_in_bank_visual() method
    - self._safe_key_press() method
    """

    if TYPE_CHECKING:
        behavior: "BehaviorManager"
        win: "RuneLiteWindow"

        def log_msg(self: "BotProtocol", msg: str, overwrite: bool = False) -> None: ...
        def _safe_key_press(self: "BotProtocol", key: str) -> bool: ...
        def find_item_in_inventory_visual(
            self: "BotProtocol",
            template_path: str,
            confidence: float,
            crop_bottom_portion: float = 0.7,
        ) -> List[int]: ...
        def find_item_in_bank_visual(
            self: "BotProtocol",
            template_path: str,
            confidence: float,
            crop_bottom_portion: float = 0.7,
        ) -> Optional[Tuple[Rectangle, int]]: ...

    def click_inventory_slot(
        self: "BotProtocol", slot_index: int, speed: str = "fastest"
    ) -> bool:
        """
        Click an inventory slot with human-like behavior.

        Args:
            slot_index: Index of the inventory slot (0-27)
            speed: Mouse movement speed ("fastest", "fast", "medium", "slow")

        Returns:
            True if click successful, False otherwise
        """
        if not self.win.inventory_slots or slot_index >= len(self.win.inventory_slots):
            self.log_msg(f"Invalid inventory slot index: {slot_index}")
            return False

        slot = self.win.inventory_slots[slot_index]
        try:
            click_point = slot.random_point()
            # Use behavior system for mouse movement
            self.behavior.mouse.move_to(click_point, mouseSpeed=speed)
            # Pre-click delay using semantic helper
            self.interaction_pre_click_delay()
            # Click
            self.behavior.mouse.click()
            return True
        except Exception as exc:
            self.log_msg(f"Inventory click error: {exc}")
            return False

    def use_item_on_item(
        self: "BotProtocol",
        primary_slot: int,
        secondary_slot: int,
        randomize_order: bool = True,
    ) -> bool:
        """
        Use one item on another with fidget pause/resume.

        Pauses fidgeting during the interaction to prevent mouse interference.
        Optionally randomizes which item is clicked first.

        Args:
            primary_slot: First item slot index
            secondary_slot: Second item slot index
            randomize_order: Whether to randomly flip click order (default: True)

        Returns:
            True if interaction successful, False otherwise
        """
        # Use context manager to pause fidgeting for entire interaction
        with self.with_paused_fidgeting():
            # Randomize click order 50% of the time
            if randomize_order and random.random() < 0.5:
                first_slot, second_slot = secondary_slot, primary_slot
            else:
                first_slot, second_slot = primary_slot, secondary_slot

            # Click first item
            if not self.click_inventory_slot(first_slot):
                return False

            # Micro-delay between clicks using semantic helper
            self.interaction_between_clicks_delay()

            # Click second item
            if not self.click_inventory_slot(second_slot):
                return False

            return True

    def press_space_to_confirm(
        self: "BotProtocol", delay_range: Tuple[float, float] = (0.5, 1.5)
    ) -> bool:
        """
        Press spacebar with randomized delay.

        Args:
            delay_range: (min, max) delay before pressing space in seconds

        Returns:
            True if spacebar pressed successfully, False otherwise
        """
        # Calculate delay within range
        min_delay, max_delay = delay_range
        mean_delay = (min_delay + max_delay) / 2
        std_delay = (max_delay - min_delay) / 4

        delay = rd.truncated_normal_sample(
            min_delay, max_delay, mean=mean_delay, std=std_delay
        )
        self.behavior.timing.sleep((delay, delay))

        # Press spacebar
        if not self._safe_key_press("space"):
            self.log_msg("Failed to press space (window focus lost).")
            return False

        # Short delay after
        self.behavior.timing.sleep((0.03, 0.08))
        return True

    def find_items_in_inventory(
        self: "BotProtocol", template_path: str, confidence: float = 0.3
    ) -> List[int]:
        """
        Find items in inventory using template matching.

        Wrapper around bot's find_item_in_inventory_visual method.

        Args:
            template_path: Full path to template image
            confidence: Matching confidence threshold (0.0-1.0)

        Returns:
            List of slot indices where item was found
        """
        return self.find_item_in_inventory_visual(
            template_path,
            confidence=confidence,
            crop_bottom_portion=0.7,  # Avoid item count overlays
        )

    def find_item_in_bank(
        self: "BotProtocol", template_path: str, confidence: float = 0.3
    ) -> Optional[Tuple[Rectangle, int]]:
        """
        Find item in bank using template matching.

        Wrapper around bot's find_item_in_bank_visual method.

        Args:
            template_path: Full path to template image
            confidence: Matching confidence threshold (0.0-1.0)

        Returns:
            Tuple of (slot_rectangle, slot_index) if found, None otherwise
        """
        return self.find_item_in_bank_visual(
            template_path,
            confidence=confidence,
            crop_bottom_portion=0.7,  # Avoid item count overlays
        )
