from typing import Dict, Tuple, List
import time
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
import utilities.color as clr

# === Import behavior system ===
from utilities.behavior.config import BotBehaviorConfig


class OSRSCooking(OSRSBot):
    """
    Cooking bot for OSRS - bank-standing activities.

    Supports four cooking methods:
    1. Cook fish: Use raw fish on range/fire → wait for "Cooking"
    2. Make rations: Use cooked chicken on maple leaves → wait for "Making"
    3. Make pineapple pizza: Use pineapple rings on plain pizza → wait for "Combining"
    4. Gut yellowfin: Use knife on raw yellowfin → wait for "Gutting"

    Workflow (Cook fish):
    1. Check for raw fish in inventory
    2. If have raw fish → cook on range/fire
    3. If no raw fish → bank (deposit cooked/burnt, withdraw raw)
    4. Press space after 0.5-1.5s delay to start cooking
    5. Wait for "Cooking" text via ActionWatcher
    6. Repeat

    Workflow (Make rations):
    1. Maple leaves stay in slot 0 (stackable, never deposited)
    2. Check for cooked chicken in inventory
    3. If have chicken → use on maple leaves → wait for "Making"
    4. If no chicken → bank (deposit rations, withdraw chicken)
    5. Repeat

    Workflow (Make pineapple pizza):
    1. Check for pineapple rings and plain pizzas in inventory
    2. If have both → use pineapple ring on plain pizza → wait for "Combining"
    3. If missing either → bank (deposit pizzas, withdraw rings + plain pizzas)
    4. Repeat

    Workflow (Gut yellowfin):
    1. Knife persists in inventory (tool, never deposited)
    2. Check for raw yellowfin in inventory
    3. If have yellowfin → use knife on raw yellowfin → wait for "Gutting"
    4. If no yellowfin → bank (deposit products, withdraw raw yellowfin, check for knife)
    5. No spacebar confirmation (auto-starts, no Make-X dialog)
    6. Products stack (yellow fin + fine fish offcuts)
    7. Repeat

    USES BEHAVIOR SYSTEM:
    - BehaviorManager with bank-standing profile
    - Ultra-minimal camera movement
    - Human-like timing patterns
    - ActionWatcher for "Cooking"/"Making"/"Combining"/"Gutting" text detection

    INHERITS FROM OSRSBot:
    - All mixins (TemplateMixin, BankingMixin, ItemInteractionMixin, ActionWaitingMixin)
    - Template validation, banking, item interaction, action waiting
    """

    # Cooking methods available
    COOKING_METHODS = [
        "Cook fish",
        "Make rations",
        "Make pineapple pizza",
        "Gut yellowfin",
    ]

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

    # Ration templates: (input_template, catalyst_template, output_template)
    # Catalyst (maple leaves) stays in inventory slot 0, never deposited
    RATION_TEMPLATES = {
        "input": "cooked_chicken.png",
        "catalyst": "maple_leaves.png",
        "output": "foresters_ration.png",
    }

    # Catalyst slot - maple leaves always stay here (stackable)
    CATALYST_SLOT = 0

    # Pizza templates: (primary_template, secondary_template, output_template)
    PIZZA_TEMPLATES = {
        "primary": "pineapple_ring.png",
        "secondary": "plain_pizza.png",
        "output": "pineapple_pizza.png",
    }

    # Yellowfin gutting templates: (tool, input, output1, output2)
    YELLOWFIN_TEMPLATES = {
        "tool": "knife.png",
        "input": "raw_yellowfin.png",
        "output1": "yellow_fin.png",
        "output2": "fine_fish_offcuts.png",
    }

    def __init__(self) -> None:
        bot_title = "Cooking"
        description = (
            "Cooks raw fish on a range or fire, makes rations, makes pineapple pizza, or guts yellowfin. "
            "Bank-standing with human-like behavior. "
            "Requires GREEN-tagged bank. Fish cooking requires PURPLE-tagged range/fire."
        )

        # === Configure behavior system ===
        # Bank-standing bot: use factory method for simplicity
        behavior_config = BotBehaviorConfig.bank_standing(
            active=True,  # Active profile (fast, efficient)
            cycle=True,  # Enable automatic profile switching
        )

        super().__init__(
            bot_title=bot_title,
            description=description,
            behavior_config=behavior_config,
        )
        self.primary_skill = "cooking"

        self.running_time = 60  # minutes
        self.cooking_method = "Cook fish"  # Default cooking method
        self.fish_type = "Raw shrimp"  # Default fish type
        self.options = {}  # Initialize options dict for reload_model() transfer
        print(
            f"[INIT DEBUG] Bot instance created, cooking_method={self.cooking_method}, fish_type={self.fish_type}"
        )

        # Enable default options
        self.options_set = True

        # Cooking timeouts
        self._cooking_start_timeout = 4.0
        self._cooking_end_timeout = 90.0  # Full inventory can take ~60-80s

        # Ration-making timeouts
        self._making_start_timeout = 4.0
        self._making_end_timeout = 90.0  # Full inventory can take ~60-90s

        # Yellowfin gutting timeouts
        self._gutting_start_timeout = 4.0
        self._gutting_end_timeout = 90.0  # Full inventory can take ~60-90s

    def create_options(self) -> None:
        self.options_builder.add_slider_option(
            "running_time", "How long to run (minutes)?", 10, 500
        )
        self.options_builder.add_dropdown_option(
            "cooking_method", "Cooking method", self.COOKING_METHODS
        )
        # Only show fish type if "Cook fish" is selected
        # Note: For "Make rations", no sub-selection needed (only Forester's ration exists)
        self.options_builder.add_dropdown_option(
            "fish_type", "Fish type (for Cook fish)", self.FISH_TYPES
        )

    def save_options(self, options: dict) -> None:
        self.log_msg(f"[DEBUG] save_options called with: {options}")

        # CRITICAL: Store options dict for reload_model() to transfer to new instance
        self.options = options

        for option in options:
            if option == "running_time":
                self.running_time = int(options[option])
                self.log_msg(f"[DEBUG] Set running_time = {self.running_time}")
            elif option == "cooking_method":
                self.cooking_method = options[option]
                self.log_msg(f"[OPTIONS] Cooking method: {self.cooking_method}")
            elif option == "fish_type":
                self.log_msg(f"[OPTIONS] Received fish_type: '{options[option]}'")
                self.fish_type = options[option]
                # Validate template lookup immediately (only relevant for Cook fish)
                if self.cooking_method == "Cook fish":
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

        self.log_msg("Running time: {self.running_time} minutes")
        self.log_msg(f"Cooking method: {self.cooking_method}")
        if self.cooking_method == "Cook fish":
            self.log_msg(f"Fish type: {self.fish_type}")
        elif self.cooking_method == "Make rations":
            self.log_msg("Making Forester's rations (cooked chicken + maple leaves)")
        elif self.cooking_method == "Make pineapple pizza":
            self.log_msg("Making pineapple pizza (pineapple rings + plain pizza)")
        elif self.cooking_method == "Gut yellowfin":
            self.log_msg("Gutting yellowfin (knife + raw yellowfin)")
        self.log_msg(
            f"[DEBUG] After save_options: cooking_method={self.cooking_method}, fish_type={self.fish_type}"
        )
        self.options_set = True

    def _define_item_templates(self) -> Dict[str, Tuple[str, str]]:
        """Return item templates for cooking (for TemplateMixin)."""
        return self.ITEM_TEMPLATES

    def main_loop(self) -> None:
        """
        Main cooking loop with behavior system integration.
        Uses mixins for banking, item interaction, and action waiting.
        Supports fish cooking, ration making, and pineapple pizza making.
        """
        if self.cooking_method == "Cook fish":
            self.log_msg(f"[MAIN_LOOP START] cooking '{self.fish_type}'")
        elif self.cooking_method == "Make rations":
            self.log_msg("[MAIN_LOOP START] making Forester's rations")
        elif self.cooking_method == "Make pineapple pizza":
            self.log_msg("[MAIN_LOOP START] making pineapple pizza")
        elif self.cooking_method == "Gut yellowfin":
            self.log_msg("[MAIN_LOOP START] gutting yellowfin")
        else:
            self.log_msg(f"[MAIN_LOOP START] unknown method: {self.cooking_method}")

        try:
            self.log_msg("[DEBUG] Step 1: Checking inventory ready...")
            if not self._ensure_inventory_ready():
                self._stop_with_message(
                    "Inventory slots unavailable. Open the inventory tab and try again."
                )
                return

            # Template validation depends on cooking method
            if self.cooking_method == "Cook fish":
                if not self.validate_templates(self.fish_type):
                    self.log_msg("Template validation failed - stopping bot")
                    self.set_status(BotStatus.STOPPED)
                    return
            # Note: For rations, we skip validate_templates since RATION_TEMPLATES
            # doesn't follow the same structure as ITEM_TEMPLATES

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
            # self.behavior.start_fidgeting(self)
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

                    # Main cycle - branch based on cooking method
                    if self.cooking_method == "Cook fish":
                        cycle_success = self._cook_fish_cycle()
                    elif self.cooking_method == "Make rations":
                        cycle_success = self._make_rations_cycle()
                    elif self.cooking_method == "Make pineapple pizza":
                        cycle_success = self._make_pizza_cycle()
                    elif self.cooking_method == "Gut yellowfin":
                        cycle_success = self._gut_yellowfin_cycle()
                    else:
                        self.log_msg(f"Unknown cooking method: {self.cooking_method}")
                        break

                    if not cycle_success:
                        # === Use behavior system for sleep ===
                        self.behavior.timing.sleep((0.15, 0.4))
                        continue

                    session.increment("cycles")
            finally:
                self.log_msg("Cooking session complete.")

        if self.status == BotStatus.RUNNING:
            self.set_status(BotStatus.STOPPED)

    def _cook_fish_cycle(self) -> bool:
        """
        Fish cooking cycle: check raw fish -> cook or bank.
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
        templates = self.get_templates(self.fish_type)
        if not templates:
            return False
        raw_template, _ = templates

        # Use item on tagged object (pauses fidgeting automatically)
        if not self.use_item_on_tagged_object(
            raw_template, clr.PURPLE, action_keywords=["Cook", "Range", "Fire", "Use"]
        ):
            return False

        # Press spacebar to confirm
        if not self.press_space_to_confirm(delay_range=(0.5, 1.5)):
            return False

        # Wait for "Cooking" to start (uses ActionWaitingMixin)
        if not self.wait_for_action_start("Cooking", 4.0):
            # Try spacebar again
            if not self.press_space_to_confirm(delay_range=(0.5, 1.5)):
                return False
            if not self.wait_for_action_start("Cooking", 4.0):
                self.log_msg("Cooking did not start (no 'Cooking' text).")
                return False

        # Wait for cooking to end (uses ActionWaitingMixin)
        cooking_success = self.wait_for_action_end("Cooking", 60.0)

        # Notify behavior manager that we completed an inventory
        # This may trigger automatic profile switching
        if cooking_success:
            self.behavior.on_inventory_complete()

        return cooking_success

    def _handle_banking(self, raw_template: str, cooked_template: str) -> bool:
        """
        Handle banking: deposit cooked/burnt fish, then withdraw raw fish.
        Uses BankingMixin.
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

        # Deposit cooked/burnt fish (uses BankingMixin)
        if not self.deposit_items({cooked_template: "all", self.BURNT_TEMPLATE: "all"}):
            self._safe_key_press("escape")
            return False

        # Withdraw raw fish (uses BankingMixin)
        if not self.withdraw_items({raw_template: "all"}):
            self._safe_key_press("escape")
            return False

        # Close bank
        self._safe_key_press("escape")
        self.behavior.timing.sleep((0.4, 0.9))
        return True

    # ========== RATION MAKING METHODS ==========

    def _make_rations_cycle(self) -> bool:
        """
        Ration making cycle: check items -> make or bank.
        Uses mixins for all operations.
        """
        # Get template paths
        input_template = self.RATION_TEMPLATES["input"]
        catalyst_template = self.RATION_TEMPLATES["catalyst"]
        output_template = self.RATION_TEMPLATES["output"]

        input_path = self.get_template_path(input_template, category="items")
        catalyst_path = self.get_template_path(catalyst_template, category="items")

        # Find items in inventory
        # Catalyst (maple leaves) should always be in slot 0
        catalyst_slots = self.find_items_in_inventory(catalyst_path, confidence=0.1)

        # Find input items (cooked chicken) in slots 1-27
        all_input_slots = self.find_items_in_inventory(input_path, confidence=0.1)
        # Exclude catalyst slot (slot 0) from input slots
        input_slots = [slot for slot in all_input_slots if slot != self.CATALYST_SLOT]

        # Check if we need to bank (either missing catalyst or missing input)
        missing_catalyst = not catalyst_slots
        missing_input = not input_slots

        if missing_catalyst or missing_input:
            if missing_catalyst:
                self.log_msg("No maple leaves, need to visit bank...")
            if missing_input:
                self.log_msg("No cooked chicken, need to visit bank...")
            return self._handle_rations_banking(
                output_template,
                input_template,
                catalyst_template,
                missing_catalyst,
                missing_input,
            )

        # We have both items, let's make rations
        return self._make_rations(input_slots)

    def _make_rations(self, input_slots: List[int]) -> bool:
        """
        Make rations by using cooked chicken on maple leaves.
        Uses ItemInteractionMixin and ActionWaitingMixin.
        """
        input_template = self.RATION_TEMPLATES["input"]
        catalyst_template = self.RATION_TEMPLATES["catalyst"]

        # Use item on item (pauses fidgeting automatically)
        if not self.use_item_on_item(input_template, catalyst_template):
            return False

        # Press spacebar to confirm
        if not self.press_space_to_confirm(delay_range=(0.5, 1.5)):
            return False

        # Wait for "Making" to start (uses ActionWaitingMixin)
        if not self.wait_for_action_start("Making", self._making_start_timeout):
            # Try spacebar again
            if not self.press_space_to_confirm(delay_range=(0.5, 1.5)):
                return False
            if not self.wait_for_action_start("Making", self._making_start_timeout):
                self.log_msg("Making did not start (no 'Making' text).")
                return False

        # Wait for making to end (uses ActionWaitingMixin)
        making_success = self.wait_for_action_end("Making", self._making_end_timeout)

        # Notify behavior manager that we completed an inventory
        # This may trigger automatic profile switching
        if making_success:
            self.behavior.on_inventory_complete()

        return making_success

    def _handle_rations_banking(
        self,
        output_template: str,
        input_template: str,
        catalyst_template: str,
        missing_catalyst: bool,
        missing_input: bool,
    ) -> bool:
        """
        Handle banking for rations: deposit rations, withdraw missing items.
        Uses BankingMixin.

        Args:
            output_template: Template for finished rations
            input_template: Template for cooked chicken
            catalyst_template: Template for maple leaves
            missing_catalyst: Whether maple leaves need to be withdrawn
            missing_input: Whether cooked chicken needs to be withdrawn

        CRITICAL: Only deposit maple leaves if we're withdrawing them fresh.
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

        # Deposit rations (exclude slot 0 if maple leaves are already there)
        # If missing catalyst, we'll deposit everything and withdraw fresh
        if missing_catalyst:
            # Deposit all rations (maple leaves will be withdrawn fresh)
            if not self.deposit_items({output_template: "all"}):
                self._safe_key_press("escape")
                return False
        else:
            # Deposit rations but preserve maple leaves in slot 0
            if not self.deposit_items(
                {output_template: "all"}, exclude_slots=[self.CATALYST_SLOT]
            ):
                self._safe_key_press("escape")
                return False

        # Withdraw items based on what's missing
        # CRITICAL: Always withdraw catalyst (maple leaves) FIRST to ensure slot 0

        if missing_catalyst:
            self.log_msg("Withdrawing maple leaves...")
            # Use "all" for stackable items (withdraws the stack)
            if not self.withdraw_items({catalyst_template: "all"}):
                self._safe_key_press("escape")
                return False

        if missing_input:
            self.log_msg("Withdrawing cooked chicken...")
            if not self.withdraw_items({input_template: "all"}):
                self._safe_key_press("escape")
                return False

        # Close bank
        self._safe_key_press("escape")
        self.behavior.timing.sleep((0.4, 0.9))
        return True

    # ========== PINEAPPLE PIZZA MAKING METHODS ==========

    def _make_pizza_cycle(self) -> bool:
        """
        Pineapple pizza making cycle: check items -> make or bank.
        Uses mixins for all operations.
        """
        # Get template paths
        primary_template = self.PIZZA_TEMPLATES["primary"]
        secondary_template = self.PIZZA_TEMPLATES["secondary"]
        output_template = self.PIZZA_TEMPLATES["output"]

        primary_path = self.get_template_path(primary_template, category="items")
        secondary_path = self.get_template_path(secondary_template, category="items")

        # Find items in inventory
        primary_slots = self.find_items_in_inventory(primary_path, confidence=0.1)
        secondary_slots = self.find_items_in_inventory(secondary_path, confidence=0.1)

        # Check if we need to bank (missing either item)
        if not primary_slots or not secondary_slots:
            if not primary_slots:
                self.log_msg("No pineapple rings, need to visit bank...")
            if not secondary_slots:
                self.log_msg("No plain pizzas, need to visit bank...")
            return self._handle_pizza_banking(
                output_template, primary_template, secondary_template
            )

        # We have both items, let's make pizzas
        return self._make_pizza(primary_slots, secondary_slots)

    def _make_pizza(self, primary_slots: List[int], secondary_slots: List[int]) -> bool:
        """
        Make pineapple pizza by using pineapple ring on plain pizza.
        Uses ItemInteractionMixin and ActionWaitingMixin.
        """
        primary_template = self.PIZZA_TEMPLATES["primary"]
        secondary_template = self.PIZZA_TEMPLATES["secondary"]

        # Use item on item (pauses fidgeting automatically)
        if not self.use_item_on_item(primary_template, secondary_template):
            return False

        # Press spacebar to confirm
        if not self.press_space_to_confirm(delay_range=(0.5, 1.5)):
            return False

        # Wait for "Combining" to start (uses ActionWaitingMixin)
        if not self.wait_for_action_start("Combining", self._making_start_timeout):
            # Try spacebar again
            if not self.press_space_to_confirm(delay_range=(0.5, 1.5)):
                return False
            if not self.wait_for_action_start("Combining", self._making_start_timeout):
                self.log_msg("Combining did not start (no 'Combining' text).")
                return False

        # Wait for combining to end (uses ActionWaitingMixin)
        combining_success = self.wait_for_action_end(
            "Combining", self._making_end_timeout
        )

        # Notify behavior manager that we completed an inventory
        if combining_success:
            self.behavior.on_inventory_complete()

        return combining_success

    def _handle_pizza_banking(
        self,
        output_template: str,
        primary_template: str,
        secondary_template: str,
    ) -> bool:
        """
        Handle banking for pineapple pizza: deposit pizzas, withdraw ingredients.
        Uses BankingMixin.

        Args:
            output_template: Template for pineapple pizzas
            primary_template: Template for pineapple rings
            secondary_template: Template for plain pizzas
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

        # Deposit pineapple pizzas
        if not self.deposit_items({output_template: "all"}):
            self._safe_key_press("escape")
            return False

        # Withdraw pineapple rings (bank set to withdraw-14)
        self.log_msg("Withdrawing pineapple rings...")
        if not self.withdraw_items({primary_template: "all"}):
            self._safe_key_press("escape")
            return False

        # Withdraw plain pizzas (bank set to withdraw-14)
        self.log_msg("Withdrawing plain pizzas...")
        if not self.withdraw_items({secondary_template: "all"}, confidence=0.20):
            self._safe_key_press("escape")
            return False

        # Verify both items were successfully withdrawn
        primary_path = self.get_template_path(primary_template, category="items")
        secondary_path = self.get_template_path(secondary_template, category="items")

        primary_check = self.find_items_in_inventory(primary_path, confidence=0.1)
        secondary_check = self.find_items_in_inventory(secondary_path, confidence=0.20)

        if not primary_check or not secondary_check:
            self.log_msg(
                "Failed to withdraw both ingredients (bank may be empty). Stopping."
            )
            self._safe_key_press("escape")
            self.set_status(BotStatus.STOPPED)
            return False

        # Close bank
        self._safe_key_press("escape")
        self.behavior.timing.sleep((0.4, 0.9))
        return True

    # ========== YELLOWFIN GUTTING METHODS ==========

    def _gut_yellowfin_cycle(self) -> bool:
        """
        Yellowfin gutting cycle: check items -> gut or bank.
        Uses mixins for all operations.
        """
        tool_template = self.YELLOWFIN_TEMPLATES["tool"]
        input_template = self.YELLOWFIN_TEMPLATES["input"]
        output1_template = self.YELLOWFIN_TEMPLATES["output1"]
        output2_template = self.YELLOWFIN_TEMPLATES["output2"]

        # Get template paths using TemplateMixin
        # knife.png auto-detects to "tools", raw_yellowfin.png uses "items"
        tool_path = self.get_template_path(tool_template)
        input_path = self.get_template_path(input_template, category="items")

        # Find items in inventory
        tool_slots = self.find_items_in_inventory(tool_path, confidence=0.1)
        input_slots = self.find_items_in_inventory(input_path, confidence=0.1)

        # Check if we need to bank (missing either item)
        if not tool_slots or not input_slots:
            if not tool_slots:
                self.log_msg("No knife, need to visit bank...")
            if not input_slots:
                self.log_msg("No raw yellowfin, need to visit bank...")
            return self._handle_yellowfin_banking(
                tool_template, input_template, output1_template, output2_template
            )

        # We have both items, let's gut yellowfin
        return self._gut_yellowfin(tool_slots, input_slots)

    def _gut_yellowfin(self, tool_slots: List[int], input_slots: List[int]) -> bool:
        """
        Gut yellowfin by using knife on raw yellowfin.
        Uses ItemInteractionMixin and ActionWaitingMixin.

        Note: No spacebar confirmation needed - starts automatically.

        Args:
            tool_slots: List of inventory slot indices containing knife
            input_slots: List of inventory slot indices containing raw yellowfin
        """
        # Use first slot of each (use_item_on_item accepts slot indices)
        tool_slot = tool_slots[0]
        input_slot = input_slots[0]

        # Use item on item (pauses fidgeting automatically)
        if not self.use_item_on_item(tool_slot, input_slot, randomize_order=True):
            return False

        # NO spacebar press - action starts automatically (no Make-X dialog)

        # Wait for "Gutting" to start (uses ActionWaitingMixin)
        if not self.wait_for_action_start("Gutting", self._gutting_start_timeout):
            self.log_msg("Gutting did not start (no 'Gutting' text).")
            return False

        # Wait for gutting to end (uses ActionWaitingMixin)
        gutting_success = self.wait_for_action_end("Gutting", self._gutting_end_timeout)

        # Notify behavior manager that we completed an inventory
        if gutting_success:
            self.behavior.on_inventory_complete()

        return gutting_success

    def _handle_yellowfin_banking(
        self,
        tool_template: str,
        input_template: str,
        output1_template: str,
        output2_template: str,
    ) -> bool:
        """
        Handle banking for yellowfin gutting: deposit products, withdraw knife + raw yellowfin.
        Uses BankingMixin.

        Args:
            tool_template: Template for knife
            input_template: Template for raw yellowfin
            output1_template: Template for yellow fin (product 1)
            output2_template: Template for fine fish offcuts (product 2)
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

        # Deposit both product stacks (yellow fin + fine fish offcuts)
        if not self.deposit_items(
            {output1_template: "all", output2_template: "all"}, confidence=0.3
        ):
            self._safe_key_press("escape")
            return False

        # Smart tool withdrawal: only withdraw knife if not already in inventory
        # knife.png auto-detects to "tools"
        tool_path = self.get_template_path(tool_template)
        tool_check = self.find_items_in_inventory(tool_path, confidence=0.1)

        if not tool_check:
            self.log_msg("Withdrawing knife...")
            if not self.withdraw_items({tool_template: 1}, confidence=0.1):
                self._safe_key_press("escape")
                return False
        else:
            self.log_msg("Knife already in inventory, skipping...")

        # Withdraw raw yellowfin (bank set to withdraw-26, single click)
        self.log_msg("Withdrawing raw yellowfin...")
        if not self.withdraw_items({input_template: "all"}, confidence=0.1):
            self._safe_key_press("escape")
            return False

        # Verify both items were successfully withdrawn
        input_path = self.get_template_path(input_template, category="items")

        tool_verify = self.find_items_in_inventory(tool_path, confidence=0.1)
        input_verify = self.find_items_in_inventory(input_path, confidence=0.1)

        if not tool_verify or not input_verify:
            self.log_msg(
                "Failed to withdraw knife and raw yellowfin (bank may be empty). Stopping."
            )
            self._safe_key_press("escape")
            self.set_status(BotStatus.STOPPED)
            return False

        # Close bank
        self._safe_key_press("escape")
        self.behavior.timing.sleep((0.4, 0.9))
        return True

    # ========== UTILITY METHODS ==========

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
