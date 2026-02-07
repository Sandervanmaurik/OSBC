import random
import time
from typing import Callable, Dict, List, Tuple

from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot

# === Import behavior system ===
from utilities.behavior.config import BotBehaviorConfig
from utilities.behavior.profiles import MouseProfile, CameraProfile


class OSRSCrafting(OSRSBot):
    """
    Crafting bot for OSRS - bank-standing activities.

    Current method: Cutting gems (chisel + uncut gem → cut gem)
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

        # === Configure behavior system ===
        # Bank-standing profiles: minimal camera, frequent mouse fidgeting
        behavior_config = BotBehaviorConfig(
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

        super().__init__(
            bot_title=bot_title,
            description=description,
            behavior_config=behavior_config,
        )
        self.primary_skill = "crafting"

        self.options = {}  # Initialize for reload_model() check
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
        self.options = options  # CRITICAL: Store for reload_model() to transfer options

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
        self.log_msg(f"Starting crafting bot with method '{self.crafting_method}'")
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
        # Open bank using BankingMixin (supports string color or None)
        if not self.open_bank(tag_color="green"):  # Uses BankingMixin
            self.log_msg("Failed to open bank.")
            return False

        # Ensure bank slots are detected using BankingMixin
        if not self.ensure_bank_slots_detected():  # Uses BankingMixin
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
            # Shift-click deposits ALL items of that type, so we only need to click one slot per item type
            # One click for cut gems, one click for crushed gems (2 clicks total max)
            unique_product_slots = []
            if cut_gem_slots:
                unique_product_slots.append(cut_gem_slots[0])  # One cut gem slot
            if crushed_gem_slots:
                unique_product_slots.append(
                    crushed_gem_slots[0]
                )  # One crushed gem slot

            if not self.deposit_items_shift_click(
                unique_product_slots
            ):  # Uses BankingMixin
                return False

        # Now withdraw supplies (tool if needed, then input items)
        return self._withdraw_supplies(tool_template, input_template)

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
            # Search for tool in bank slots - use TemplateMixin
            tool_path = self.get_template_path(tool_template)
            result = self.find_item_in_bank(tool_path, confidence=self._item_confidence)
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

        # Withdraw input items (click to fill inventory) - use TemplateMixin
        self.log_msg(f"Withdrawing {input_template}...")
        input_path = self.get_template_path(input_template)
        result = self.find_item_in_bank(input_path, confidence=self._item_confidence)

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

    def _craft_gems(self, tool_slots: List[int], input_slots: List[int]) -> bool:
        """
        Craft gems by using tool on input item.

        NOTE: Uses ItemInteractionMixin.use_item_on_item() which automatically
        pauses fidgeting during the item interaction sequence.
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

        # Use item on item (auto-pauses fidgeting) - ItemInteractionMixin
        if not self.use_item_on_item(
            primary_slot, secondary_slot, randomize_order=False
        ):
            return False

        # Press spacebar with randomized delay - ItemInteractionMixin
        if not self.press_space_to_confirm():
            return False

        # Wait for "Cutting" to start - ActionWaitingMixin
        if not self.wait_for_action_start("Cutting", self._cutting_start_timeout):
            # Try spacebar again
            if not self.press_space_to_confirm():
                return False
            if not self.wait_for_action_start("Cutting", self._cutting_start_timeout):
                self.log_msg("Crafting did not start (no 'Cutting' text).")
                return False

        # Wait for cutting to end - ActionWaitingMixin
        return self.wait_for_action_end("Cutting", self._cutting_end_timeout)

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

        # Use TemplateMixin to get paths (auto-detects "tools" vs "items")
        tool_path = self.get_template_path(tool_template)
        input_path = self.get_template_path(input_template)

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

        # Use TemplateMixin to get paths
        output_path = self.get_template_path(output_template)
        byproduct_path = self.get_template_path(self.BYPRODUCT_TEMPLATE)

        # Find both cut gems and crushed gems
        cut_gem_slots = self.find_item_in_inventory_visual(
            output_path, confidence=self._item_confidence
        )
        crushed_gem_slots = self.find_item_in_inventory_visual(
            byproduct_path, confidence=self._item_confidence
        )

        return (cut_gem_slots, crushed_gem_slots)

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
