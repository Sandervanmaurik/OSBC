import random
import time
from typing import Dict, List, Optional, Tuple

import utilities.color as clr
import utilities.imagesearch as imsearch
import utilities.ocr as ocr
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
from utilities.geometry import Rectangle

# === Import behavior system ===
from utilities.behavior.config import BotBehaviorConfig


class OSRSFletching(OSRSBot):
    """
    Fletching bot for OSRS.

    Current method: headless arrows (combine feathers with arrow shafts).

    MIGRATED TO BEHAVIOR SYSTEM:
    - Uses BehaviorManager with "focused" profile
    - Camera and skill checks disabled (standing at bank)
    - Fast timing behaviors for rapid clicking
    - Custom break patterns integrated
    """

    FLETCHING_METHODS = ["Headless arrows", "Maple longbow", "Ruby bolt tips"]

    ITEM_TEMPLATES: Dict[str, Tuple[str, str]] = {
        "Headless arrows": ("feather.png", "arrow_shaft.png"),
    }

    # Maple longbow templates: (primary, secondary, output)
    LONGBOW_TEMPLATES = {
        "primary": "maple_longbow_(u).png",
        "secondary": "bow_string.png",
        "output": "maple_longbow.png",
    }

    # Ruby bolt tips templates: (tool, input, output)
    RUBY_BOLT_TIPS_TEMPLATES = {
        "tool": "chisel.png",
        "input": "ruby.png",
        "output": "ruby_bolt_tips.png",
    }

    def __init__(self) -> None:
        bot_title = "Fletching"
        description = (
            "Fletches headless arrows or strings maple longbows. "
            "Bank-standing with human-like behavior. "
            "Maple longbow requires GREEN-tagged bank."
        )

        # === Configure behavior system ===
        # Bank-standing profile (works for both methods)
        behavior_config = BotBehaviorConfig.bank_standing(
            active=True,
            cycle=True,
        )

        super().__init__(
            bot_title=bot_title,
            description=description,
            behavior_config=behavior_config,
        )
        self.primary_skill = "fletching"

        self.options = {}  # Initialize for reload_model() check
        self.running_time = 60  # minutes
        self.fletching_method = "Headless arrows"

        # Enable default options - can be customized via Options button
        self.options_set = True

        self._item_confidence = 0.3
        self._missing_item_cycles = 0
        self._max_missing_cycles = 3

        self._prefer_primary_first = True
        self._order_flip_chance = 0.25

        # Break timing (headless arrows only)
        self._next_break_at = 0.0
        self._break_min = 2.0
        self._break_max = 12.0

        # Fletching timeouts
        self._attaching_start_timeout = 3.0
        self._attaching_end_timeout = 55.0

        # Maple longbow stringing timeouts
        self._stringing_start_timeout = 4.0
        self._stringing_end_timeout = 90.0

        # Ruby bolt tips cutting timeouts
        self._cutting_start_timeout = 3.0
        self._cutting_end_timeout = 90.0

    def create_options(self) -> None:
        self.options_builder.add_slider_option(
            "running_time", "How long to run (minutes)?", 50, 500
        )
        self.options_builder.add_dropdown_option(
            "fletching_method", "Fletching method", self.FLETCHING_METHODS
        )

    def save_options(self, options: dict) -> None:
        self.options = options  # CRITICAL: Store for reload_model() to transfer options

        for option in options:
            if option == "running_time":
                self.running_time = int(options[option])
            elif option == "fletching_method":
                self.fletching_method = options[option]
            else:
                self.log_msg(f"Unknown option: {option}")
                self.options_set = False
                return

        self.log_msg(f"Running time: {self.running_time} minutes")
        self.log_msg(f"Fletching method: {self.fletching_method}")
        self.options_set = True

    def main_loop(self) -> None:
        self.log_msg("Starting fletching bot...")

        if not self._ensure_inventory_ready():
            self._stop_with_message(
                "Inventory slots unavailable. Open the inventory tab and try again."
            )
            return

        self._open_inventory_tab()

        # Only schedule breaks for headless arrows
        if self.fletching_method == "Headless arrows":
            self._schedule_next_break()

        # === Initialize behavior display ===
        self.behavior.log_stats_summary(self.log_msg)
        if hasattr(self, "controller") and self.controller:
            self.controller.update_behavior_display()

        # Track time for periodic stats logging
        last_stats_log = time.time()
        stats_log_interval = (
            300.0 if self.fletching_method == "Headless arrows" else 30.0
        )

        with self.timed_session(self.running_time) as session:
            if self.fletching_method == "Headless arrows":
                self.behavior.start_fidgeting(self)
            try:
                while session.running:
                    if self._should_stop():
                        break

                    # === NEW: Use attention behaviors (mouse movement only) ===
                    self.behavior.attention.perform_random_behaviors()

                    # === Periodic stats logging ===
                    now = time.time()
                    if now - last_stats_log >= stats_log_interval:
                        self.behavior.log_stats_summary(self.log_msg)
                        if hasattr(self, "controller") and self.controller:
                            stats = self.behavior.get_stats_summary()
                            self.controller.update_behavior_display(stats=stats)
                        last_stats_log = now

                    if self.fletching_method == "Headless arrows":
                        if self._should_take_break():
                            self._take_break()

                        if not self._fletch_headless_arrows_cycle():
                            # === NEW: Use behavior system for sleep ===
                            self.behavior.timing.sleep((0.15, 0.4))
                            continue

                    elif self.fletching_method == "Maple longbow":
                        cycle_success = self._string_longbow_cycle()
                        if not cycle_success:
                            self.behavior.timing.sleep((0.15, 0.4))
                            continue

                    elif self.fletching_method == "Ruby bolt tips":
                        cycle_success = self._cut_ruby_bolt_tips_cycle()
                        if not cycle_success:
                            self.behavior.timing.sleep((0.15, 0.4))
                            continue

                    else:
                        self._stop_with_message(
                            f"Unsupported method: {self.fletching_method}"
                        )
                        break

                    session.increment("cycles")
            finally:
                if self.fletching_method == "Headless arrows":
                    self.behavior.stop_fidgeting()

        self.log_msg("Fletching session complete.")
        if self.status == BotStatus.RUNNING:
            self.set_status(BotStatus.STOPPED)

    def _fletch_headless_arrows_cycle(self) -> bool:
        feather_slots, shaft_slots = self._find_fletching_slots()
        if not feather_slots or not shaft_slots:
            self._missing_item_cycles += 1
            self.log_msg(
                f"Missing items (feathers={len(feather_slots)}, shafts={len(shaft_slots)}) "
                f"[{self._missing_item_cycles}/{self._max_missing_cycles}]"
            )
            if self._missing_item_cycles >= self._max_missing_cycles:
                self._stop_with_message(
                    "Required items not found. Stopping fletching bot."
                )
            return False

        self._missing_item_cycles = 0

        # Randomly flip item click order
        if random.random() < self._order_flip_chance:
            self._prefer_primary_first = not self._prefer_primary_first

        if self._prefer_primary_first:
            primary_slots, secondary_slots = feather_slots, shaft_slots
        else:
            primary_slots, secondary_slots = shaft_slots, feather_slots

        primary_slot = random.choice(primary_slots)
        secondary_slot = random.choice(secondary_slots)

        # Use item on item (auto-pauses fidgeting) - ItemInteractionMixin
        if not self.use_item_on_item(
            primary_slot, secondary_slot, randomize_order=False
        ):
            return False

        # Press spacebar - ItemInteractionMixin
        if not self.press_space_to_confirm():
            return False

        # Wait for "Attaching" to start (custom logic)
        if not self._wait_for_attaching_start(
            timeout_seconds=self._attaching_start_timeout
        ):
            if not self.press_space_to_confirm():
                return False
            if not self._wait_for_attaching_start(
                timeout_seconds=self._attaching_start_timeout
            ):
                self.log_msg("Fletching did not start (no 'Attaching' text).")
                return False

        return self._wait_for_attaching_end(timeout_seconds=self._attaching_end_timeout)

    def _find_fletching_slots(self) -> Tuple[List[int], List[int]]:
        if not self.win.inventory_slots:
            return ([], [])

        templates = self.ITEM_TEMPLATES.get(self.fletching_method)
        if not templates:
            return ([], [])

        # Use TemplateMixin to get paths
        feather_template = self.get_template_path(templates[0])
        shaft_template = self.get_template_path(templates[1])

        feather_slots = self.find_item_in_inventory_visual(
            feather_template, confidence=self._item_confidence
        )
        shaft_slots = self.find_item_in_inventory_visual(
            shaft_template, confidence=self._item_confidence
        )
        return (feather_slots, shaft_slots)

    # ========== MAPLE LONGBOW STRINGING METHODS ==========

    def _string_longbow_cycle(self) -> bool:
        """
        Maple longbow stringing cycle: check items -> string or bank.
        Uses mixins for all operations.
        """
        primary_template = self.LONGBOW_TEMPLATES["primary"]
        secondary_template = self.LONGBOW_TEMPLATES["secondary"]
        output_template = self.LONGBOW_TEMPLATES["output"]

        primary_path = self.get_template_path(primary_template, category="items")
        secondary_path = self.get_template_path(secondary_template, category="items")

        # Find items in inventory (higher confidence = more lenient matching)
        primary_slots = self.find_items_in_inventory(primary_path, confidence=0.6)
        secondary_slots = self.find_items_in_inventory(secondary_path, confidence=0.6)

        # Check if we need to bank (missing either item)
        if not primary_slots or not secondary_slots:
            if not secondary_slots:
                self.log_msg("No bow strings, need to visit bank...")
            if not primary_slots:
                self.log_msg("No maple longbow (u), need to visit bank...")

            return self._handle_longbow_banking(
                output_template, primary_template, secondary_template
            )

        # We have both items, let's string bows
        return self._string_longbow(primary_slots, secondary_slots)

    def _string_longbow(
        self, primary_slots: List[int], secondary_slots: List[int]
    ) -> bool:
        """
        String maple longbow by using maple longbow (u) on bow string.
        Uses ItemInteractionMixin and ActionWaitingMixin.
        """
        # Use the already-found slots (efficient, avoids re-searching)
        primary_slot = random.choice(primary_slots)
        secondary_slot = random.choice(secondary_slots)

        # Use item on item (pauses fidgeting automatically)
        if not self.use_item_on_item(
            primary_slot, secondary_slot, randomize_order=True
        ):
            return False

        # Press spacebar to confirm
        if not self.press_space_to_confirm(delay_range=(0.5, 1.5)):
            return False

        # Wait for "Stringing" to start (uses ActionWaitingMixin)
        if not self.wait_for_action_start("Stringing", self._stringing_start_timeout):
            # Try spacebar again
            if not self.press_space_to_confirm(delay_range=(0.5, 1.5)):
                return False
            if not self.wait_for_action_start(
                "Stringing", self._stringing_start_timeout
            ):
                self.log_msg("Stringing did not start (no 'Stringing' text).")
                return False

        # Wait for stringing to end (uses ActionWaitingMixin)
        stringing_success = self.wait_for_action_end(
            "Stringing", self._stringing_end_timeout
        )

        # Notify behavior manager that we completed an inventory
        if stringing_success:
            self.behavior.on_inventory_complete()

        return stringing_success

    def _handle_longbow_banking(
        self,
        output_template: str,
        primary_template: str,
        secondary_template: str,
    ) -> bool:
        """
        Handle banking for maple longbow: deposit longbows, withdraw ingredients.
        Uses BankingMixin.

        Args:
            output_template: Template for maple longbows (finished product)
            primary_template: Template for maple longbow (u)
            secondary_template: Template for bow strings
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

        # Deposit maple longbows (finished product)
        if not self.deposit_items({output_template: "all"}, confidence=0.8):
            self._safe_key_press("escape")
            return False

        # Withdraw maple longbow (u) (bank set to withdraw-14)
        self.log_msg("Withdrawing maple longbow (u)...")
        if not self.withdraw_items({primary_template: "all"}, confidence=0.6):
            self._safe_key_press("escape")
            return False

        # Withdraw bow strings (bank set to withdraw-14)
        self.log_msg("Withdrawing bow strings...")
        if not self.withdraw_items({secondary_template: "all"}, confidence=0.4):
            self._safe_key_press("escape")
            return False

        # Verify both items were successfully withdrawn
        primary_path = self.get_template_path(primary_template, category="items")
        secondary_path = self.get_template_path(secondary_template, category="items")

        primary_check = self.find_items_in_inventory(primary_path, confidence=0.6)
        secondary_check = self.find_items_in_inventory(secondary_path, confidence=0.4)

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

    # ========== RUBY BOLT TIPS CUTTING METHODS ==========

    def _cut_ruby_bolt_tips_cycle(self) -> bool:
        """
        Ruby bolt tips cutting cycle: check items -> cut or bank.
        Uses mixins for all operations.
        """
        tool_template = self.RUBY_BOLT_TIPS_TEMPLATES["tool"]
        input_template = self.RUBY_BOLT_TIPS_TEMPLATES["input"]
        output_template = self.RUBY_BOLT_TIPS_TEMPLATES["output"]

        # Get template paths using TemplateMixin
        tool_path = self.get_template_path(tool_template)
        input_path = self.get_template_path(input_template)

        # Find items in inventory (confidence tuned for gems/tools)
        tool_slots = self.find_items_in_inventory(tool_path, confidence=0.1)
        input_slots = self.find_items_in_inventory(input_path, confidence=0.1)

        # Check if we need to bank (missing either item)
        if not tool_slots or not input_slots:
            if not tool_slots:
                self.log_msg("No chisel, need to visit bank...")
            if not input_slots:
                self.log_msg("No rubies, need to visit bank...")

            return self._handle_ruby_banking(
                tool_template, input_template, output_template
            )

        # We have both items, let's cut bolt tips
        return self._cut_ruby_bolt_tips(tool_slots, input_slots)

    def _cut_ruby_bolt_tips(
        self, tool_slots: List[int], input_slots: List[int]
    ) -> bool:
        """
        Cut ruby bolt tips by using chisel on ruby.
        Uses ItemInteractionMixin and ActionWaitingMixin.
        """
        # Randomly flip item click order (human behavior)
        if random.random() < self._order_flip_chance:
            self._prefer_primary_first = not self._prefer_primary_first

        if self._prefer_primary_first:
            primary_slots, secondary_slots = tool_slots, input_slots
        else:
            primary_slots, secondary_slots = input_slots, tool_slots

        # Pick random slots
        primary_slot = random.choice(primary_slots)
        secondary_slot = random.choice(secondary_slots)

        # Use item on item (pauses fidgeting automatically)
        if not self.use_item_on_item(
            primary_slot, secondary_slot, randomize_order=False
        ):
            return False

        # Press spacebar to confirm
        if not self.press_space_to_confirm(delay_range=(0.5, 1.5)):
            return False

        # Wait for "Cutting" to start (uses ActionWaitingMixin)
        if not self.wait_for_action_start("Cutting", self._cutting_start_timeout):
            # Try spacebar again
            if not self.press_space_to_confirm(delay_range=(0.5, 1.5)):
                return False
            if not self.wait_for_action_start("Cutting", self._cutting_start_timeout):
                self.log_msg("Cutting did not start (no 'Cutting' text).")
                return False

        # Wait for cutting to end (uses ActionWaitingMixin)
        cutting_success = self.wait_for_action_end("Cutting", self._cutting_end_timeout)

        # Notify behavior manager that we completed an inventory
        if cutting_success:
            self.behavior.on_inventory_complete()

        return cutting_success

    def _handle_ruby_banking(
        self,
        tool_template: str,
        input_template: str,
        output_template: str,
    ) -> bool:
        """
        Handle banking for ruby bolt tips: deposit bolt tips, withdraw chisel + rubies.
        Uses BankingMixin.

        Args:
            tool_template: Template for chisel
            input_template: Template for rubies
            output_template: Template for ruby bolt tips (finished product)
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

        # Deposit ruby bolt tips (finished product)
        if not self.deposit_items({output_template: "all"}, confidence=0.3):
            self._safe_key_press("escape")
            return False

        # Smart tool withdrawal: only withdraw if not already in inventory
        tool_path = self.get_template_path(tool_template)
        tool_check = self.find_items_in_inventory(tool_path, confidence=0.1)

        if not tool_check:
            self.log_msg("Withdrawing chisel...")
            if not self.withdraw_items({tool_template: 1}, confidence=0.1):
                self._safe_key_press("escape")
                return False
        else:
            self.log_msg("Chisel already in inventory, skipping...")

        # Withdraw rubies (bank set to withdraw-all or withdraw-X)
        self.log_msg("Withdrawing rubies...")
        if not self.withdraw_items({input_template: "all"}, confidence=0.1):
            self._safe_key_press("escape")
            return False

        # Verify both items were successfully withdrawn
        input_path = self.get_template_path(input_template)

        tool_verify = self.find_items_in_inventory(tool_path, confidence=0.1)
        input_verify = self.find_items_in_inventory(input_path, confidence=0.1)

        if not tool_verify or not input_verify:
            self.log_msg(
                "Failed to withdraw chisel and rubies (bank may be empty). Stopping."
            )
            self._safe_key_press("escape")
            self.set_status(BotStatus.STOPPED)
            return False

        # Close bank
        self._safe_key_press("escape")
        self.behavior.timing.sleep((0.4, 0.9))
        return True

    # ===== REMOVED: _click_inventory_slot() - now using ItemInteractionMixin.click_inventory_slot() =====
    # === REMOVED: _get_item_template_path() - now using TemplateMixin.get_template_path() ===
    # === REMOVED: _press_space_to_confirm() - now using ItemInteractionMixin.press_space_to_confirm() ===

    def _wait_for_attaching_start(self, timeout_seconds: float) -> bool:
        start = time.time()
        while time.time() - start < timeout_seconds:
            if self._should_stop():
                return False
            if self._is_attaching():
                return True
            # === NEW: Use behavior system for polling delay ===
            self.behavior.timing.sleep((0.08, 0.18))
        return False

    def _wait_for_attaching_end(self, timeout_seconds: float) -> bool:
        start = time.time()
        last_log = 0.0
        while time.time() - start < timeout_seconds:
            if self._should_stop():
                return False
            if not self._is_attaching():
                return True
            if time.time() - last_log > 6.0:
                self.log_msg("Attaching... waiting for completion.")
                if self.check_xp_watcher():
                    self.log_msg("XP gained!")
                last_log = time.time()
            # === NEW: Use behavior system for polling delay ===
            self.behavior.timing.sleep((0.2, 0.6))
        self.log_msg("Attaching wait timed out; retrying cycle.")
        return False

    def _schedule_next_break(self) -> None:
        # === NEW: Use behavior system's random utilities ===
        import utilities.random_util as rd

        self._next_break_at = time.time() + rd.truncated_normal_sample(
            25, 70, mean=45, std=10
        )

    def _should_take_break(self) -> bool:
        return time.time() >= self._next_break_at

    def _take_break(self) -> None:
        # === NEW: Use behavior system for break duration ===
        import utilities.random_util as rd

        break_duration = rd.truncated_normal_sample(
            self._break_min, self._break_max, mean=6.0, std=2.0
        )
        self.log_msg(f"Taking a short break ({break_duration:.1f}s)")
        end_time = time.time() + break_duration

        # Random mouse movements during break
        moves = random.randint(1, 3)
        for _ in range(moves):
            self._random_mouse_movement()
            # === NEW: Use behavior system for delay ===
            self.behavior.timing.sleep((0.2, 0.6))

        remaining = end_time - time.time()
        if remaining > 0:
            time.sleep(remaining)

        self._schedule_next_break()

    def _random_mouse_movement(self) -> None:
        """Random mouse movement during breaks (uses behavior system)."""
        if not self.win:
            return
        try:
            if random.random() < 0.7 and self.win.game_view:
                point = self.win.game_view.random_point()
            elif self.win.inventory_slots:
                slot = random.choice(self.win.inventory_slots)
                point = slot.random_point()
            else:
                return
            # === NEW: Use behavior system for mouse movement ===
            self.behavior.mouse.move_to(
                point, mouseSpeed=random.choice(["medium", "fast", "fastest"])
            )
        except Exception as exc:
            self.log_msg(f"Random mouse movement error: {exc}")

    def _open_inventory_tab(self) -> None:
        if len(self.win.cp_tabs) > 3:
            # === NEW: Use behavior system for mouse movement ===
            self.behavior.mouse.move_to(
                self.win.cp_tabs[3].random_point(), mouseSpeed="fast"
            )
            self.behavior.mouse.click()
            # === NEW: Use behavior system for delay ===
            self.behavior.timing.sleep((0.15, 0.35))

    def _ensure_inventory_ready(self) -> bool:
        if not self.win or not self.win.inventory_slots:
            return False
        return True

    def _should_stop(self) -> bool:
        if self.status != BotStatus.RUNNING:
            return True
        if self.thread is None or not self.thread.is_alive():
            return True
        return False

    def _stop_with_message(self, message: str) -> None:
        self.log_msg(message)
        self.set_status(BotStatus.STOPPED)

    def _get_action_text_rect(self) -> Optional[Rectangle]:
        if hasattr(self.win, "current_action") and self.win.current_action:
            return self.win.current_action
        if self.win and self.win.game_view:
            gv = self.win.game_view
            return Rectangle(gv.left, gv.top, min(260, gv.width), min(60, gv.height))
        return None

    def _is_attaching(self) -> bool:
        rects = self._get_action_text_rects()
        if not rects:
            return False

        colors = [clr.WHITE, clr.OFF_WHITE, clr.OFF_YELLOW]
        for rect in rects:
            if ocr.find_text("Attaching", rect, ocr.BOLD_12, colors):
                return True
            if ocr.find_text("Attaching", rect, ocr.PLAIN_12, colors):
                return True

            extracted = ocr.extract_text(rect, ocr.BOLD_12, colors)
            if "Attaching" in extracted:
                return True
            extracted = ocr.extract_text(rect, ocr.PLAIN_12, colors)
            if "Attaching" in extracted:
                return True

        return False

    def _get_action_text_rects(self) -> List[Rectangle]:
        rects: List[Rectangle] = []
        primary = self._get_action_text_rect()
        if primary:
            rects.append(primary)

        if self.win and self.win.game_view:
            gv = self.win.game_view
            rects.append(
                Rectangle(gv.left, gv.top, min(320, gv.width), min(90, gv.height))
            )

        return rects
