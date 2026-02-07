from typing import Dict, Tuple, List, Optional
import os
import random
import time
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
from model.runelite_bot import RuneLiteObject
import utilities.color as clr
import utilities.random_util as rd

# === Import behavior system ===
from utilities.behavior.config import BotBehaviorConfig
from utilities.behavior.profiles import MouseProfile, CameraProfile


class OSRSCooking(OSRSBot):
    """
    Cooking bot for OSRS - bank-standing activities.

    Workflow:
    1. Check for raw fish in inventory
    2. If have raw fish → cook on range/fire
    3. If no raw fish → bank (deposit cooked/burnt, withdraw raw)
    4. Press space after 0.5-1.5s delay to start cooking
    5. Wait for "Cooking" text via ActionWatcher
    6. Repeat

    USES BEHAVIOR SYSTEM:
    - BehaviorManager with bank-standing profile
    - Ultra-minimal camera movement
    - Human-like timing patterns
    - ActionWatcher for "Cooking" text detection

    INHERITS FROM OSRSBot:
    - All mixins (TemplateMixin, BankingMixin, ItemInteractionMixin, ActionWaitingMixin)
    - Template validation, banking, item interaction, action waiting
    """

    FISH_TYPES = [
        "Raw shrimp",
        "Raw trout",
        "Raw salmon",
        "Raw lobster",
        "Raw swordfish",
        "Raw shark",
        "Raw karambwan",
    ]

    # Map fish type to (raw_template, cooked_template)
    ITEM_TEMPLATES: Dict[str, Tuple[str, str]] = {
        "Raw shrimp": ("raw_shrimp.png", "cooked_shrimp.png"),
        "Raw trout": ("raw_trout.png", "cooked_trout.png"),
        "Raw salmon": ("raw_salmon.png", "cooked_salmon.png"),
        "Raw lobster": ("raw_lobster.png", "cooked_lobster.png"),
        "Raw swordfish": ("raw_swordfish.png", "cooked_swordfish.png"),
        "Raw shark": ("raw_shark.png", "cooked_shark.png"),
        "Raw karambwan": ("raw_karambwan.png", "cooked_karambwan.png"),
    }

    BURNT_TEMPLATE = "burnt_fish.png"

    def __init__(self) -> None:
        bot_title = "Cooking"
        description = (
            "Cooks raw fish on a range or fire. "
            "Bank-standing with human-like behavior. "
            "Requires GREEN-tagged bank and PURPLE-tagged range/fire."
        )

        # === Configure behavior system ===
        # Bank-standing profiles: minimal camera, frequent mouse fidgeting
        behavior_config = BotBehaviorConfig(
            profile="high-active",  # Fast, efficient profile
            mouse_profile=MouseProfile.BANK_STANDING,
            camera_profile=CameraProfile.BANK_STANDING,
            custom_config={
                "timing": {
                    "speed_multiplier": 0.9,  # Slightly faster
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
        self.primary_skill = "cooking"

        self.running_time = 60  # minutes
        self.fish_type = "Raw shrimp"  # Default fish type
        self.options = {}  # Initialize options dict for reload_model() transfer
        print(
            f"[INIT DEBUG] Bot instance created, fish_type default = {self.fish_type}"
        )

        # Enable default options
        self.options_set = True

        # Cooking timeouts
        self._cooking_start_timeout = 4.0
        self._cooking_end_timeout = 90.0  # Full inventory can take ~60-80s

    def create_options(self) -> None:
        self.options_builder.add_slider_option(
            "running_time", "How long to run (minutes)?", 10, 500
        )
        self.options_builder.add_dropdown_option(
            "fish_type", "Fish type", self.FISH_TYPES
        )

    def save_options(self, options: dict) -> None:
        self.log_msg(f"[DEBUG] save_options called with: {options}")

        # CRITICAL: Store options dict for reload_model() to transfer to new instance
        self.options = options

        for option in options:
            if option == "running_time":
                self.running_time = int(options[option])
                self.log_msg(f"[DEBUG] Set running_time = {self.running_time}")
            elif option == "fish_type":
                self.log_msg(f"[OPTIONS] Received fish_type: '{options[option]}'")
                self.fish_type = options[option]
                # Validate template lookup immediately
                templates = self.ITEM_TEMPLATES.get(self.fish_type)
                if templates:
                    raw_template, cooked_template = templates
                    self.log_msg(
                        f"[OPTIONS] Templates: raw={raw_template}, cooked={cooked_template}"
                    )
                else:
                    self.log_msg(
                        f"[OPTIONS] ERROR: No templates for '{self.fish_type}'!"
                    )
            else:
                self.log_msg(f"Unknown option: {option}")
                self.options_set = False
                return

        self.log_msg(f"Running time: {self.running_time} minutes")
        self.log_msg(f"Fish type: {self.fish_type}")
        self.log_msg(f"[DEBUG] After save_options, self.fish_type = '{self.fish_type}'")
        self.options_set = True

    def _define_item_templates(self) -> Dict[str, Tuple[str, str]]:
        """Return item templates for cooking (for TemplateMixin)."""
        return self.ITEM_TEMPLATES

    def main_loop(self) -> None:
        """
        Main cooking loop with behavior system integration.
        Uses mixins for banking, item interaction, and action waiting.
        """
        self.log_msg(f"[MAIN_LOOP START] cooking '{self.fish_type}'")

        try:
            self.log_msg("[DEBUG] Step 1: Checking inventory ready...")
            if not self._ensure_inventory_ready():
                self._stop_with_message(
                    "Inventory slots unavailable. Open the inventory tab and try again."
                )
                return
            if not self.validate_templates(self.fish_type):
                self.log_msg("Template validation failed - stopping bot")
                self.set_status(BotStatus.STOPPED)
                return
            self._open_inventory_tab()
            self.behavior.log_stats_summary(self.log_msg)
            if hasattr(self, "controller") and self.controller:
                self.controller.update_behavior_display()
        except Exception as e:
            self.log_msg(f"[ERROR] Exception during initialization: {e}")
            import traceback

            self.log_msg(traceback.format_exc())
            self.set_status(BotStatus.STOPPED)
            return

        # Track time for periodic stats logging
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

                    # === Periodic stats logging ===
                    now = time.time()
                    if now - last_stats_log >= stats_log_interval:
                        self.behavior.log_stats_summary(self.log_msg)
                        if hasattr(self, "controller") and self.controller:
                            stats = self.behavior.get_stats_summary()
                            self.controller.update_behavior_display(stats=stats)
                        last_stats_log = now

                    # Main cooking cycle
                    if not self._cooking_cycle():
                        # === Use behavior system for sleep ===
                        self.behavior.timing.sleep((0.15, 0.4))
                        continue

                    session.increment("cycles")
            finally:
                self.behavior.stop_fidgeting()

        self.log_msg("Cooking session complete.")
        if self.status == BotStatus.RUNNING:
            self.set_status(BotStatus.STOPPED)

    def _cooking_cycle(self) -> bool:
        """
        Main cooking cycle: check raw fish -> cook or bank.
        Uses mixins for all operations.
        """
        templates = self.get_templates(self.fish_type)  # Uses TemplateMixin
        if not templates:
            self._stop_with_message(f"No templates for: {self.fish_type}")
            return False

        raw_template, cooked_template = templates

        # Get full path (uses TemplateMixin)
        raw_path = self.get_template_path(raw_template, category="items")

        # Find raw fish slots (uses ItemInteractionMixin's find_items_in_inventory wrapper)
        raw_slots = self.find_items_in_inventory(raw_path, confidence=0.05)

        # Check if we need to bank
        if not raw_slots:
            self.log_msg("No raw fish, need to visit bank...")
            return self._handle_banking(raw_template, cooked_template)

        # We have raw fish, let's cook
        return self._cook_fish(raw_slots)

    def _cook_fish(self, raw_slots: List[int]) -> bool:
        """
        Cook fish by using raw fish on range/fire.
        Uses ItemInteractionMixin and ActionWaitingMixin.
        """
        # Find PURPLE-tagged range/fire
        range_obj = self.get_nearest_tag(clr.PURPLE)
        if range_obj is None:
            return False

        # Pause fidgeting for the cooking action sequence
        self.behavior.pause_fidgeting()

        try:
            # Click a raw fish in inventory first
            raw_slot = random.choice(raw_slots)
            if not self.click_inventory_slot(
                raw_slot, speed="fastest"
            ):  # Uses ItemInteractionMixin
                return False
            self.behavior.timing.sleep((0.03, 0.08))

            # Click the range/fire
            self.behavior.mouse.move_to(
                range_obj.random_point(),
                mouseSpeed=random.choice(["fast", "fastest"]),
            )
            self.behavior.timing.sleep((0.2, 0.5))

            # Verify hover text
            if not self.mouseover_text(contains=["Cook", "Range", "Fire", "Use"]):
                self.log_msg(
                    "Hover text doesn't match cooking target, clicking anyway..."
                )

            self.behavior.mouse.click()
            self.behavior.timing.sleep((0.3, 0.6))

            # Press spacebar with randomized delay (uses ItemInteractionMixin)
            if not self.press_space_to_confirm(delay_range=(0.5, 1.5)):
                return False
        finally:
            # Resume fidgeting after item interaction is complete
            self.behavior.resume_fidgeting()

        # Wait for "Cooking" to start (uses ActionWaitingMixin)
        if not self.wait_for_action_start("Cooking", 4.0):
            # Try spacebar again
            if not self.press_space_to_confirm(delay_range=(0.5, 1.5)):
                return False
            if not self.wait_for_action_start("Cooking", 4.0):
                self.log_msg("Cooking did not start (no 'Cooking' text).")
                return False

        # Wait for cooking to end (uses ActionWaitingMixin)
        return self.wait_for_action_end("Cooking", 60.0)

    def _handle_banking(self, raw_template: str, cooked_template: str) -> bool:
        """
        Handle banking: deposit cooked/burnt fish, then withdraw raw fish.
        Uses BankingMixin and ItemInteractionMixin.
        """
        # Open bank (uses BankingMixin)
        if not self.open_bank(tag_color="green"):
            self.log_msg("Failed to open bank.")
            return False

        # Ensure bank slots detected (uses BankingMixin)
        if not self.ensure_bank_slots_detected():
            self.log_msg("Cannot perform banking: bank slot detection failed.")
            self._safe_key_press("escape")
            return False

        # Find cooked + burnt fish
        cooked_path = self.get_template_path(cooked_template, category="items")
        burnt_path = self.get_template_path(self.BURNT_TEMPLATE, category="items")

        cooked_slots = self.find_items_in_inventory(cooked_path, confidence=0.3)

        # Try to find burnt fish (template might not exist)
        burnt_slots = []
        if os.path.exists(burnt_path):
            burnt_slots = self.find_items_in_inventory(burnt_path, confidence=0.3)
        else:
            self.log_msg(f"Burnt fish template not found (this is OK): {burnt_path}")

        total_products = len(cooked_slots) + len(burnt_slots)

        # Deposit cooked/burnt fish (uses BankingMixin)
        # Only need to shift-click ONE slot per item type (deposits all of that type)
        slots_to_deposit = []
        if cooked_slots:
            slots_to_deposit.append(cooked_slots[0])  # One cooked fish deposits all
        if burnt_slots:
            slots_to_deposit.append(burnt_slots[0])  # One burnt fish deposits all

        if slots_to_deposit:
            self.log_msg(
                f"Found {len(cooked_slots)} cooked + {len(burnt_slots)} burnt, depositing..."
            )
            if not self.deposit_items_shift_click(slots_to_deposit):
                self._safe_key_press("escape")
                return False
            self.behavior.timing.sleep((0.3, 0.7))

        # Withdraw raw fish
        return self._withdraw_raw_fish(raw_template)

    def _withdraw_raw_fish(self, raw_template: str) -> bool:
        """
        Withdraw raw fish from bank.
        Bank must already be open. Uses ItemInteractionMixin.
        """
        self.log_msg(f"Withdrawing {raw_template}...")
        raw_path = self.get_template_path(raw_template, category="items")

        # Find raw fish in bank (uses ItemInteractionMixin)
        # Bank items need higher confidence (more lenient) due to rendering differences
        # 0.0 = perfect match (strict), 1.0 = any match (lenient)
        # Karambwan specifically needs very high confidence (0.95) - may need bank-specific template
        result = self.find_item_in_bank(raw_path, confidence=0.05)

        if result:
            raw_slot, slot_index = result
            self.behavior.mouse.move_to(raw_slot.random_point(), mouseSpeed="fast")
            self.behavior.timing.sleep((0.1, 0.2))
            self.behavior.mouse.click()
            self.behavior.timing.sleep((0.3, 0.6))
        else:
            self.log_msg(f"{raw_template} not found in bank! Stopping...")
            self._safe_key_press("escape")
            return False

        # Close bank
        self._safe_key_press("escape")
        self.behavior.timing.sleep((0.4, 0.9))
        return True

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
