"""
Production Skill Bot Base Class

This base class provides a unified framework for OSRS production skills (cooking, crafting, fletching, etc.)
that follow a common pattern:
1. Bank to withdraw materials
2. Interact with items to start production
3. Wait for action to complete
4. Repeat until target reached or out of materials

The template method pattern is used: subclasses implement abstract methods to define specifics,
while the base class provides the common production cycle logic.

All mixins (TemplateMixin, BankingMixin, ItemInteractionMixin, ActionWaitingMixin) are available
via inheritance from OSRSBot.
"""

from abc import abstractmethod
from typing import Dict, Tuple, Callable, Union, Optional, List
import time
import utilities.random_util as rd
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot


class ProductionSkillBot(OSRSBot):
    """
    Base class for production skill bots (cooking, crafting, fletching, etc.)

    Subclasses must implement:
    - get_item_templates() -> Dict mapping skill selections to template tuples/lambdas
    - get_action_text() -> str (e.g., "Cooking", "Fletching")
    - get_action_timeouts() -> Tuple[float, float] (start_timeout, end_timeout)
    - get_production_target() -> int (how many items to produce before stopping)
    - get_space_delay() -> Tuple[float, float] (min, max delay for spacebar confirmation)

    Optional overrides:
    - before_production_cycle() -> Called before each cycle
    - after_production_cycle() -> Called after each cycle
    - should_stop_early() -> bool (custom stop conditions)
    - custom_item_interaction() -> Customize how items are combined
    """

    def __init__(self, bot_title: str, description: str):
        super().__init__(bot_title, description)
        self.items_produced = 0
        self.production_target = 0
        self.current_selection = None  # Tracks user's selected item/recipe

    # NOTE: Subclasses SHOULD override main_loop() to add behavior system integration,
    # timed sessions, fidgeting, etc. This base class provides _production_cycle() as a helper.

    def _production_cycle(self) -> bool:
        """
        Core production cycle - uses mixins for all operations.

        Returns:
            bool: True if cycle completed successfully, False otherwise
        """
        action_text = self.get_action_text()
        start_timeout, end_timeout = self.get_action_timeouts()

        # Step 1: Open bank
        self.log_msg("Opening bank...")
        if not self.open_bank(tag_color=self.get_bank_tag_color()):
            self.log_msg("Failed to open bank")
            return False

        # Step 2: Deposit all items (shift-click)
        self.log_msg("Depositing items...")
        if not self.deposit_all_shift_click():
            self.log_msg("Failed to deposit items")
            return False

        self.behavior.timing.sleep((0.3, 0.6))

        # Step 3: Withdraw materials from bank
        self.log_msg("Withdrawing materials...")
        if not self._withdraw_materials():
            self.log_msg("Failed to withdraw materials - possibly out of materials")
            return False

        # Step 4: Close bank
        self.log_msg("Closing bank...")
        if not self._safe_key_press("escape"):
            self.log_msg("Failed to close bank (window focus lost)")
            return False
        self.behavior.timing.sleep((0.4, 0.9))

        # Step 5: Interact with items to start production
        self.log_msg("Starting production interaction...")
        if not self._perform_item_interaction():
            self.log_msg("Failed to interact with items")
            return False

        # Step 6: Wait for action to start
        self.log_msg(f"Waiting for {action_text} to start...")
        if not self.wait_for_action_start(action_text, start_timeout):
            self.log_msg(f"{action_text} did not start in time")
            return False

        # Step 7: Wait for action to complete
        self.log_msg(f"Waiting for {action_text} to complete...")
        if not self.wait_for_action_end(action_text, end_timeout):
            self.log_msg(f"{action_text} did not complete in time")
            return False

        # Step 8: Increment counter (assume 1 inventory = 28 items produced)
        self.items_produced += 28
        self.log_msg(
            f"Production cycle complete - Total: {self.items_produced}/{self.production_target}"
        )

        return True

    def _withdraw_materials(self) -> bool:
        """
        Withdraw materials from bank using templates.
        Uses get_templates() to resolve static or dynamic templates.

        Returns:
            bool: True if materials withdrawn successfully
        """
        try:
            # Get templates for current selection
            templates = self.get_templates(self.current_selection)

            if not templates:
                self.log_msg(
                    f"No templates found for selection: {self.current_selection}"
                )
                return False

            # Withdraw each material (templates are in order: tool/primary, secondary, etc.)
            for i, template_filename in enumerate(templates):
                template_path = self.get_template_path(template_filename)

                self.log_msg(f"Withdrawing material {i + 1}: {template_filename}")

                # Find item in bank (returns Tuple[Rectangle, int] or None)
                result = self.find_item_in_bank(template_path, confidence=0.80)

                if not result:
                    self.log_msg(f"Material not found in bank: {template_filename}")
                    return False

                # Unpack result
                item_slot, slot_index = result

                # Click item to withdraw (default is left-click for 1, can override)
                self.behavior.mouse.move_to(item_slot.random_point(), mouseSpeed="fast")
                self.behavior.timing.sleep((0.1, 0.2))
                self.behavior.mouse.click()
                self.behavior.timing.sleep((0.2, 0.5))

            return True

        except Exception as e:
            self.log_msg(f"Error withdrawing materials: {e}")
            return False

            # Withdraw each material (templates are in order: tool/primary, secondary, etc.)
            for i, template_filename in enumerate(templates):
                template_path = self.get_template_path(template_filename)

                self.log_msg(f"Withdrawing material {i + 1}: {template_filename}")

                # Find item in bank
                matches = self.find_item_in_bank(template_path, confidence=0.80)

                if not matches:
                    self.log_msg(f"Material not found in bank: {template_filename}")
                    return False

                # Click item to withdraw (default is left-click for 1, can override)
                item_slot = matches[0]
                self.mouse.move_to(item_slot.random_point(), mouseSpeed="fast")
                self.mouse.click()
                time.sleep(rd.truncated_normal_sample(0.2, 0.5, mean=0.3, std=0.1))

            return True

        except Exception as e:
            self.log_msg(f"Error withdrawing materials: {e}")
            return False

    def _perform_item_interaction(self) -> bool:
        """
        Perform item interaction to start production.
        Subclasses can override custom_item_interaction() for special logic.

        Returns:
            bool: True if interaction successful
        """
        # Check if subclass wants custom interaction logic
        custom_result = self.custom_item_interaction()
        if custom_result is not None:
            return custom_result

        # Default: Use item on item (slot 0 on slot 14 - first column top + middle)
        self.log_msg("Using item on item (default: slot 0 on slot 14)...")
        if not self.use_item_on_item(primary_slot=0, secondary_slot=14):
            return False

        # Confirm with spacebar
        space_min, space_max = self.get_space_delay()
        if not self.press_space_to_confirm(delay_range=(space_min, space_max)):
            return False

        return True

    # ==================== ABSTRACT METHODS (MUST IMPLEMENT) ====================

    @abstractmethod
    def get_item_templates(self) -> Dict[str, Union[Tuple[str, ...], Callable]]:
        """
        Define item templates for this production skill.

        Returns:
            Dict mapping selection names to:
            - Static tuple: ("tool.png", "material.png", ...)
            - Dynamic lambda: lambda **kwargs: ("tool.png", f"{kwargs['type']}_material.png", ...)

        Example (Cooking):
            return {
                "Raw shrimp": ("raw_shrimp.png", "cooked_shrimp.png"),
                "Raw lobster": ("raw_lobster.png", "cooked_lobster.png"),
            }

        Example (Crafting - dynamic):
            return {
                "Cutting gems": lambda gem_type: ("chisel.png", f"uncut_{gem_type.lower()}.png", ...),
            }
        """
        pass

    @abstractmethod
    def get_action_text(self) -> str:
        """
        Return the action text that appears in RuneLite during production.

        Examples: "Cooking", "Fletching", "Crafting"
        """
        pass

    @abstractmethod
    def get_action_timeouts(self) -> Tuple[float, float]:
        """
        Return timeout values for action start and end.

        Returns:
            Tuple[float, float]: (start_timeout, end_timeout) in seconds

        Example:
            return (5.0, 120.0)  # 5s to start, 120s to complete
        """
        pass

    @abstractmethod
    def get_production_target(self) -> int:
        """
        Return how many items to produce before stopping.

        Returns:
            int: Number of items to produce (0 = infinite)
        """
        pass

    @abstractmethod
    def get_space_delay(self) -> Tuple[float, float]:
        """
        Return delay range for spacebar confirmation.

        Returns:
            Tuple[float, float]: (min_delay, max_delay) in seconds
        """
        pass

    # ==================== OPTIONAL OVERRIDES ====================

    def get_bank_tag_color(self) -> Optional[str]:
        """
        Return bank tag color to search for (default: None).

        Returns:
            Optional[str]: Color name (e.g., "cyan", "purple") or None
        """
        return None

    def before_production_cycle(self) -> bool:
        """
        Hook called before each production cycle.
        Override to add custom pre-cycle logic.

        Returns:
            bool: True to continue, False to stop bot
        """
        return True

    def after_production_cycle(self) -> bool:
        """
        Hook called after each production cycle.
        Override to add custom post-cycle logic.

        Returns:
            bool: True to continue, False to stop bot
        """
        return True

    def should_stop_early(self) -> bool:
        """
        Hook for custom stop conditions.
        Override to add conditions like time limits, break system, etc.

        Returns:
            bool: True to stop bot early
        """
        return False

    def custom_item_interaction(self) -> Optional[bool]:
        """
        Override to customize item interaction logic.
        If returns None, default interaction is used.

        Returns:
            Optional[bool]: True if successful, False if failed, None to use default
        """
        return None
