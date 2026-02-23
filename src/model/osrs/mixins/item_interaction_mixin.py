"""
ItemInteractionMixin - Shared item interaction operations for OSRS bots.

Provides common inventory/bank item interaction functionality:
- Clicking inventory slots
- Using item on item (with fidgeting pause)
- Using item on tagged object (e.g., raw fish on range)
- Pressing spacebar to confirm
- Finding items in inventory/bank

Extracted from cooking/crafting/fletching bots to eliminate duplication.
"""

import random
from typing import List, Tuple, Optional, Union, TYPE_CHECKING

import utilities.random_util as rd
import utilities.color as clr
from utilities.geometry import Rectangle
from model.runelite_bot import RuneLiteObject

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
        def get_template_path(
            self: "BotProtocol", filename: str, category: str = "items"
        ) -> str: ...
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
        def get_nearest_tag(self: "BotProtocol", color) -> Optional[RuneLiteObject]: ...
        def mouseover_text(
            self: "BotProtocol",
            contains: Optional[List[str]] = None,
            exact: Optional[str] = None,
        ) -> bool: ...

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
        primary_item: Union[int, str],
        secondary_item: Union[int, str],
        randomize_order: bool = True,
        confidence: float = 0.1,
    ) -> bool:
        """
        Use one item on another with fidget pause/resume.

        Pauses fidgeting during the interaction to prevent mouse interference.
        Optionally randomizes which item is clicked first.

        Args:
            primary_item: First item (slot index or template name like "cooked_chicken.png")
            secondary_item: Second item (slot index or template name like "maple_leaves.png")
            randomize_order: Whether to randomly flip click order (default: True)
            confidence: Template matching confidence if using item names (default: 0.1)

        Returns:
            True if interaction successful, False otherwise

        Example:
            # Using slot indices (legacy)
            self.use_item_on_item(5, 0)

            # Using item names (new)
            self.use_item_on_item("cooked_chicken.png", "maple_leaves.png")
        """
        # Convert item names to slot indices if needed
        primary_slot = self._resolve_item_slot(primary_item, confidence)
        secondary_slot = self._resolve_item_slot(secondary_item, confidence)

        if primary_slot is None or secondary_slot is None:
            return False

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

    def use_item_on_tagged_object(
        self: "BotProtocol",
        item: Union[int, str],
        tag_color: Union[str, object],
        action_keywords: Optional[List[str]] = None,
        confidence: float = 0.1,
    ) -> bool:
        """
        Use an inventory item on a tagged object in the game view.

        This is for interactions like:
        - Using raw fish on a range/fire (PURPLE tag)
        - Using logs on a bonfire (CYAN tag)

        Pauses fidgeting during interaction.

        Args:
            item: Item to use (slot index or template name like "raw_shrimp.png")
            tag_color: Color object (clr.PURPLE) or string ("purple")
            action_keywords: Keywords to verify in mouseover text (e.g., ["Cook", "Range", "Fire"])
            confidence: Template matching confidence if using item name (default: 0.1)

        Returns:
            True if interaction successful, False otherwise

        Example:
            # Cook fish on range
            self.use_item_on_tagged_object(
                "raw_shrimp.png",
                clr.PURPLE,
                action_keywords=["Cook", "Range", "Fire"]
            )
        """
        # Convert string color names to color objects
        if isinstance(tag_color, str):
            tag_color = self._string_to_color(tag_color)

        # Find tagged object
        tagged_obj = self.get_nearest_tag(tag_color)
        if tagged_obj is None:
            self.log_msg(f"Tagged object with color {tag_color} not found")
            return False

        # Convert item name to slot index if needed
        item_slot = self._resolve_item_slot(item, confidence)
        if item_slot is None:
            return False

        # Use context manager to pause fidgeting
        with self.with_paused_fidgeting():
            # Click inventory item first
            if not self.click_inventory_slot(item_slot, speed="fastest"):
                return False

            self.behavior.timing.sleep((0.03, 0.08))

            # Click tagged object
            self.behavior.mouse.move_to(
                tagged_obj.random_point(),
                mouseSpeed=random.choice(["fast", "fastest"]),
            )
            self.behavior.timing.sleep((0.2, 0.5))

            # Verify hover text if keywords provided
            if action_keywords:
                if not self.mouseover_text(contains=action_keywords):
                    self.log_msg(
                        f"Hover text doesn't match {action_keywords}, clicking anyway..."
                    )

            self.behavior.mouse.click()
            self.behavior.timing.sleep((0.3, 0.6))

        return True

    def _resolve_item_slot(
        self: "BotProtocol", item: Union[int, str], confidence: float = 0.1
    ) -> Optional[int]:
        """
        Resolve an item to its inventory slot index.

        Args:
            item: Either slot index (int) or template name (str)
            confidence: Template matching confidence for string items

        Returns:
            Slot index if found, None if not found
        """
        if isinstance(item, int):
            # Already a slot index
            return item
        elif isinstance(item, str):
            # Template name - find in inventory
            template_path = self.get_template_path(item, category="items")
            slots = self.find_items_in_inventory(template_path, confidence=confidence)
            if not slots:
                self.log_msg(f"Item {item} not found in inventory")
                return None
            # Return random slot if multiple found
            return random.choice(slots)
        else:
            self.log_msg(f"Invalid item type: {type(item)}")
            return None

    def _string_to_color(self: "BotProtocol", color_name: str):
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
            crop_bottom_portion=0.5,  # Avoid item count overlays
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
            crop_bottom_portion=0.5,  # Avoid item count overlays
        )
