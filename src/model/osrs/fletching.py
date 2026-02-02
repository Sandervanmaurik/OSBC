import random
import time
from typing import Dict, List, Optional, Tuple

import utilities.color as clr
import utilities.imagesearch as imsearch
import utilities.ocr as ocr
import utilities.random_util as rd
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
from utilities.geometry import Rectangle


class OSRSFletching(OSRSBot):
    """
    Fletching bot for OSRS.

    Current method: headless arrows (combine feathers with arrow shafts).
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

        self.running_time = 60  # minutes
        self.fletching_method = "Headless arrows"

        # Enable default options - can be customized via Options button
        self.options_set = True

        self._item_confidence = 0.3
        self._missing_item_cycles = 0
        self._max_missing_cycles = 3

        self._prefer_primary_first = True
        self._order_flip_chance = 0.25

        self._next_break_at = 0.0
        self._break_min = 2.0
        self._break_max = 12.0

        self._attaching_start_timeout = 3.0
        self._attaching_end_timeout = 55.0

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

        with self.timed_session(self.running_time) as session:
            while session.running:
                if self._should_stop():
                    break

                if self._should_take_break():
                    self._take_break()

                if self.fletching_method == "Headless arrows":
                    if not self._fletch_headless_arrows_cycle():
                        self._sleep_fast(0.15, 0.4)
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
        self._sleep_fast(0.03, 0.08)
        if not self._click_inventory_slot(secondary_slot):
            return False

        if not self._press_space_to_confirm():
            return False

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
            self.mouse.move_to(
                click_point, mouseSpeed=random.choice(["fastest", "fast", "fastest"])
            )
            self._sleep_fast(0.02, 0.06)
            self.mouse.click()
            return True
        except Exception as exc:
            self.log_msg(f"Inventory click error: {exc}")
            return False

    def _sleep_fast(self, min_seconds: float, max_seconds: float) -> float:
        delay = rd.truncated_normal_sample(
            min_seconds,
            max_seconds,
            mean=(min_seconds + max_seconds) / 2,
            std=(max_seconds - min_seconds) / 5,
        )
        time.sleep(delay)
        return delay

    def _wait_for_attaching_start(self, timeout_seconds: float) -> bool:
        start = time.time()
        while time.time() - start < timeout_seconds:
            if self._should_stop():
                return False
            if self._is_attaching():
                return True
            self._sleep_fast(0.08, 0.18)
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
                last_log = time.time()
            self._sleep_fast(0.2, 0.6)
        self.log_msg("Attaching wait timed out; retrying cycle.")
        return False

    def _schedule_next_break(self) -> None:
        self._next_break_at = time.time() + rd.truncated_normal_sample(
            25, 70, mean=45, std=10
        )

    def _should_take_break(self) -> bool:
        return time.time() >= self._next_break_at

    def _take_break(self) -> None:
        break_duration = rd.truncated_normal_sample(
            self._break_min, self._break_max, mean=6.0, std=2.0
        )
        self.log_msg(f"Taking a short break ({break_duration:.1f}s)")
        end_time = time.time() + break_duration

        moves = random.randint(1, 3)
        for _ in range(moves):
            self._random_mouse_movement()
            self._sleep_fast(0.2, 0.6)

        remaining = end_time - time.time()
        if remaining > 0:
            time.sleep(remaining)

        self._schedule_next_break()

    def _random_mouse_movement(self) -> None:
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
            self.mouse.move_to(
                point, mouseSpeed=random.choice(["medium", "fast", "fastest"])
            )
        except Exception as exc:
            self.log_msg(f"Random mouse movement error: {exc}")

    def _open_inventory_tab(self) -> None:
        if len(self.win.cp_tabs) > 3:
            self.mouse.move_to(self.win.cp_tabs[3].random_point(), mouseSpeed="fast")
            self.mouse.click()
            self._sleep_fast(0.15, 0.35)

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
        self._sleep_fast(0.02, 0.06)
        if not self._safe_key_press("space"):
            self.log_msg("Failed to press space (window focus lost).")
            return False
        self._sleep_fast(0.03, 0.08)
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
