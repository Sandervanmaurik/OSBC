import random
import time
from typing import Dict, List, Optional, Tuple

import utilities.color as clr
import utilities.imagesearch as imsearch
import utilities.ocr as ocr
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
from utilities.geometry import Rectangle

# === NEW: Import behavior system ===
from utilities.behavior import BehaviorManager


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

    FLETCHING_METHODS = ["Headless arrows"]

    ITEM_TEMPLATES: Dict[str, Tuple[str, str]] = {
        "Headless arrows": ("feather.png", "arrow_shaft.png"),
    }

    def __init__(self) -> None:
        bot_title = "Fletching"
        description = (
            "Fletches headless arrows by combining feathers with arrow shafts. "
            "Fast, human-like clicking with short breaks and no camera movement."
        )
        super().__init__(bot_title=bot_title, description=description)
        self.primary_skill = "fletching"

        self.running_time = 60  # minutes
        self.fletching_method = "Headless arrows"

        # Enable default options - can be customized via Options button
        self.options_set = True

        self._item_confidence = 0.3
        self._missing_item_cycles = 0
        self._max_missing_cycles = 3

        self._prefer_primary_first = True
        self._order_flip_chance = 0.25

        # Break timing
        self._next_break_at = 0.0
        self._break_min = 2.0
        self._break_max = 12.0

        # Fletching timeouts
        self._attaching_start_timeout = 3.0
        self._attaching_end_timeout = 55.0

        # === NEW: Initialize behavior system ===
        # Use "high-active" profile with customizations for fletching
        self.behavior = BehaviorManager(
            bot=self,
            profile="high-active",  # Fast, efficient profile
            custom_config={
                "timing": {
                    "speed_multiplier": 0.8,  # Even faster for fletching
                },
                "mouse": {
                    "default_speed": "fastest",  # Fast clicks for fletching
                },
                "action": {
                    "misclick_chance": 0.03,  # Very low misclick (repetitive task)
                    "hesitation_chance": 0.05,  # Low hesitation
                },
                "attention": {
                    # Disable attention behaviors - standing at bank
                    "camera_enabled": False,
                    "skill_check_enabled": False,
                    "mouse_movement_enabled": True,  # Keep mouse movements
                    "mouse_movement_interval": (60.0, 180.0),  # Less frequent
                    "inventory_check_enabled": False,  # Not needed
                },
                "breaks": {
                    "enabled": False,  # We have custom break logic
                },
            },
        )

    def create_options(self) -> None:
        self.options_builder.add_slider_option(
            "running_time", "How long to run (minutes)?", 50, 500
        )
        self.options_builder.add_dropdown_option(
            "fletching_method", "Fletching method", self.FLETCHING_METHODS
        )

    def save_options(self, options: dict) -> None:
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
        self._schedule_next_break()

        # === Initialize behavior display ===
        self.behavior.log_stats_summary(self.log_msg)
        if hasattr(self, "controller") and self.controller:
            self.controller.update_behavior_display()

        # Track time for periodic stats logging
        import time

        last_stats_log = time.time()
        stats_log_interval = 300.0  # 5 minutes

        with self.timed_session(self.running_time) as session:
            while session.running:
                if self._should_stop():
                    break

                # === NEW: Use attention behaviors (mouse movement only) ===
                self.behavior.attention.perform_random_behaviors()

                # === Periodic stats logging (every 5 minutes) ===
                now = time.time()
                if now - last_stats_log >= stats_log_interval:
                    self.behavior.log_stats_summary(self.log_msg)
                    if hasattr(self, "controller") and self.controller:
                        stats = self.behavior.get_stats_summary()
                        self.controller.update_behavior_display(stats=stats)
                    last_stats_log = now

                if self._should_take_break():
                    self._take_break()

                if self.fletching_method == "Headless arrows":
                    if not self._fletch_headless_arrows_cycle():
                        # === NEW: Use behavior system for sleep ===
                        self.behavior.timing.sleep((0.15, 0.4))
                        continue
                else:
                    self._stop_with_message(
                        f"Unsupported method: {self.fletching_method}"
                    )
                    break

                session.increment("cycles")

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

        # Pause fidgeting for the entire item interaction sequence
        # to prevent mouse movement from interrupting the "use item on item" action
        self.behavior.pause_fidgeting()

        try:
            if random.random() < self._order_flip_chance:
                self._prefer_primary_first = not self._prefer_primary_first

            if self._prefer_primary_first:
                primary_slots, secondary_slots = feather_slots, shaft_slots
            else:
                primary_slots, secondary_slots = shaft_slots, feather_slots

            primary_slot = random.choice(primary_slots)
            secondary_slot = random.choice(secondary_slots)

            if not self._click_inventory_slot(primary_slot):
                return False
            # === NEW: Use behavior system for micro-delay ===
            self.behavior.timing.sleep((0.03, 0.08))
            if not self._click_inventory_slot(secondary_slot):
                return False

            if not self._press_space_to_confirm():
                return False
        finally:
            # Resume fidgeting after item interaction is complete
            self.behavior.resume_fidgeting()

        if not self._wait_for_attaching_start(
            timeout_seconds=self._attaching_start_timeout
        ):
            if not self._press_space_to_confirm():
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

        feather_template = self._get_item_template_path(templates[0])
        shaft_template = self._get_item_template_path(templates[1])

        feather_slots = self.find_item_in_inventory_visual(
            feather_template, confidence=self._item_confidence
        )
        shaft_slots = self.find_item_in_inventory_visual(
            shaft_template, confidence=self._item_confidence
        )
        return (feather_slots, shaft_slots)

    def _get_item_template_path(self, filename: str) -> str:
        return str(imsearch.get_template_path("items", filename))

    def _click_inventory_slot(self, slot_index: int) -> bool:
        if not self.win.inventory_slots or slot_index >= len(self.win.inventory_slots):
            return False

        slot = self.win.inventory_slots[slot_index]
        try:
            click_point = slot.random_point()
            # === NEW: Use behavior system for mouse movement ===
            # Profile already configured for "fastest" speed
            self.behavior.mouse.move_to(
                click_point, mouseSpeed=random.choice(["fastest", "fast", "fastest"])
            )
            # === NEW: Use behavior system for pre-click delay ===
            self.behavior.timing.sleep((0.02, 0.06))
            # === NEW: Use behavior system for clicking ===
            self.behavior.mouse.click()
            return True
        except Exception as exc:
            self.log_msg(f"Inventory click error: {exc}")
            return False

    # === REMOVED: _sleep_fast() - now using behavior.timing.sleep() ===

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

    def _press_space_to_confirm(self) -> bool:
        # === NEW: Use behavior system for delay ===
        self.behavior.timing.sleep((0.02, 0.06))
        if not self._safe_key_press("space"):
            self.log_msg("Failed to press space (window focus lost).")
            return False
        # === NEW: Use behavior system for delay ===
        self.behavior.timing.sleep((0.03, 0.08))
        return True

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
