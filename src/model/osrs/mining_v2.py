import random
import time
from typing import Dict, List, Optional

import pyautogui as pag

import utilities.color as clr
import utilities.game_launcher as launcher
import utilities.imagesearch as imsearch
import utilities.ocr as ocr
import utilities.random_util as rd
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
from utilities.geometry import Point, RuneLiteObject


class OSRSMiningV2(OSRSBot, launcher.Launchable):
    """
    Human-like mining bot using tagged rocks.

    How to use:
    - Stand near rocks and tag them with the chosen ore tag color (default pink).
    - If using bank mode later, tag a bank with the chosen bank tag color (default green).
    - Keep the inventory tab available (default layout).
    """

    COLOR_OPTIONS: Dict[str, clr.Color] = {
        "Pink": clr.PINK,
        "Green": clr.GREEN,
        "Cyan": clr.CYAN,
        "Yellow": clr.YELLOW,
        "Red": clr.RED,
        "White": clr.WHITE,
    }

    INVENTORY_MODES = [
        "Bank (tagged)",
        "Drop",
    ]

    ORE_TYPES = [
        "Any",
        "Copper",
        "Tin",
        "Iron",
    ]

    ORE_TEMPLATES = {
        "Copper": "copper_ore.png",
        "Tin": "tin_ore.png",
        "Iron": "iron_ore.png",
    }

    def __init__(self) -> None:
        bot_title = "Mining v2"
        description = (
            "Human-like mining with recovery logic. Tag rocks (pink) and banks (green). "
            "Supports dropping inventory; banking is reserved for a later version."
        )
        super().__init__(bot_title=bot_title, description=description)

        self.running_time = 180  # minutes
        self.take_breaks = False
        self.ore_type = "Any"
        self.ore_tag_color_name = "Pink"
        self.bank_tag_color_name = "Green"
        self.inventory_mode = "Drop"

        self._last_camera_move = 0.0
        self._last_random_action = 0.0
        self._camera_interval = 0.0
        self._action_interval = 0.0
        self._recovery_stage = 0
        self._idle_timeout = 25.0
        self._progress_timeout = 90.0

    def create_options(self) -> None:
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 500)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])
        self.options_builder.add_dropdown_option("ore_type", "Ore type", self.ORE_TYPES)
        self.options_builder.add_dropdown_option("ore_tag_color_name", "Ore tag color", list(self.COLOR_OPTIONS.keys()))
        self.options_builder.add_dropdown_option("inventory_mode", "Inventory handling", self.INVENTORY_MODES)
        self.options_builder.add_dropdown_option("bank_tag_color_name", "Bank tag color", list(self.COLOR_OPTIONS.keys()))

    def save_options(self, options: dict) -> None:
        for option in options:
            if option == "running_time":
                self.running_time = int(options[option])
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            elif option == "ore_type":
                self.ore_type = options[option]
            elif option == "ore_tag_color_name":
                self.ore_tag_color_name = options[option]
            elif option == "inventory_mode":
                self.inventory_mode = options[option]
            elif option == "bank_tag_color_name":
                self.bank_tag_color_name = options[option]
            else:
                self.log_msg(f"Unknown option: {option}")
                self.options_set = False
                return

        self.log_msg(f"Running time: {self.running_time} minutes")
        self.log_msg(f"Take breaks: {self.take_breaks}")
        self.log_msg(f"Ore type: {self.ore_type}")
        self.log_msg(f"Ore tag color: {self.ore_tag_color_name}")
        self.log_msg(f"Inventory mode: {self.inventory_mode}")
        self.log_msg(f"Bank tag color: {self.bank_tag_color_name}")
        self.options_set = True

    def main_loop(self) -> None:
        self.log_msg("Starting Mining v2...")
        self._open_inventory_tab()
        self._reset_random_intervals()
        self._reset_timeouts()

        last_action_time = time.time()
        last_progress_time = time.time()
        last_inventory_count = self.count_inventory_items_visual()
        search_failures = 0

        with self.timed_session(self.running_time) as session:
            while session.running:
                if self._should_stop():
                    break

                self._perform_random_behaviors()
                self._maybe_take_break()

                if self._inventory_is_full():
                    self.log_msg("Inventory full, handling...")
                    handled = self._handle_inventory_full()
                    if handled:
                        last_progress_time = time.time()
                        last_inventory_count = self.count_inventory_items_visual()
                        search_failures = 0
                        self._reset_timeouts()
                        self._recovery_stage = 0
                    self._sleep(0.4, 1.2)
                    continue

                if self._is_mining():
                    last_action_time = time.time()
                    if not self._wait_while_mining():
                        self._run_recovery("mining timeout")
                    else:
                        new_count = self.count_inventory_items_visual()
                        if new_count > last_inventory_count:
                            last_inventory_count = new_count
                            last_progress_time = time.time()
                        self._reset_timeouts()
                        self._recovery_stage = 0
                    continue

                target = self._select_rock_target()
                if target is None:
                    search_failures += 1
                    self.log_msg(f"No tagged rocks found (#{search_failures})")
                    if search_failures >= 3:
                        self._run_recovery("no rocks found")
                        search_failures = 0
                    self._sleep(0.5, 1.4)
                    if self._check_stuck(last_action_time, last_progress_time):
                        last_action_time = time.time()
                        last_progress_time = time.time()
                    continue

                search_failures = 0
                if self._attempt_mine(target):
                    if self._wait_for_mine_start():
                        last_action_time = time.time()
                        session.increment("rocks_clicked")
                        if not self._wait_while_mining():
                            self._run_recovery("mining timeout")
                        else:
                            new_count = self.count_inventory_items_visual()
                            if new_count > last_inventory_count:
                                last_inventory_count = new_count
                                last_progress_time = time.time()
                            self._reset_timeouts()
                            self._recovery_stage = 0
                    else:
                        self._run_recovery("mine did not start")
                else:
                    self._sleep(0.2, 0.9)

                if self._check_stuck(last_action_time, last_progress_time):
                    last_action_time = time.time()
                    last_progress_time = time.time()

        self.log_msg("Mining v2 session complete.")

    def _sleep(self, min_seconds: float, max_seconds: float, mean: Optional[float] = None, std: Optional[float] = None) -> float:
        delay = rd.truncated_normal_sample(min_seconds, max_seconds, mean=mean, std=std)
        time.sleep(delay)
        return delay

    def _should_stop(self) -> bool:
        if self.status != BotStatus.RUNNING:
            return True
        if self.thread is None or not self.thread.is_alive():
            return True
        return False

    def _reset_random_intervals(self) -> None:
        now = time.time()
        self._last_camera_move = now
        self._last_random_action = now
        self._camera_interval = rd.truncated_normal_sample(30, 90, mean=55, std=12)
        self._action_interval = rd.truncated_normal_sample(45, 120, mean=75, std=15)

    def _reset_timeouts(self) -> None:
        self._idle_timeout = rd.truncated_normal_sample(18, 35, mean=26, std=4)
        self._progress_timeout = rd.truncated_normal_sample(60, 140, mean=95, std=18)

    def _perform_random_behaviors(self) -> None:
        now = time.time()
        if now - self._last_camera_move >= self._camera_interval:
            if random.random() < 0.7:
                self._random_camera_movement()
            self._last_camera_move = now
            self._camera_interval = rd.truncated_normal_sample(30, 90, mean=55, std=12)

        if now - self._last_random_action >= self._action_interval:
            actions = [
                self._random_skill_check,
                self._random_mouse_movement,
                self._check_inventory_random,
                self._mini_camera_adjust,
                self._thinking_pause,
            ]
            random.choice(actions)()
            self._last_random_action = now
            self._action_interval = rd.truncated_normal_sample(45, 120, mean=75, std=15)

    def _random_camera_movement(self) -> None:
        try:
            horizontal = random.randint(-120, 120)
            vertical = random.randint(-20, 20) if random.random() < 0.3 else 0
            if horizontal == 0 and vertical == 0:
                return
            self.move_camera(horizontal=horizontal, vertical=vertical)
            self._sleep(0.2, 0.6)
        except Exception as exc:
            self.log_msg(f"Camera move error: {exc}")

    def _mini_camera_adjust(self) -> None:
        try:
            horizontal = random.randint(-45, 45)
            self.move_camera(horizontal=horizontal)
            self._sleep(0.15, 0.45)
        except Exception as exc:
            self.log_msg(f"Mini camera adjust error: {exc}")

    def _random_mouse_movement(self) -> None:
        try:
            point = self.win.game_view.random_point()
            self.mouse.move_to(point, mouseSpeed=random.choice(["slow", "medium", "fast"]))
            self._sleep(0.2, 0.7)
        except Exception as exc:
            self.log_msg(f"Random mouse movement error: {exc}")

    def _check_inventory_random(self) -> None:
        try:
            if len(self.win.cp_tabs) > 3:
                self.mouse.move_to(self.win.cp_tabs[3].random_point(), mouseSpeed="fast")
                self.mouse.click()
                self._sleep(0.2, 0.6)
            if self.win.inventory_slots:
                slot = random.choice(self.win.inventory_slots)
                self.mouse.move_to(slot.random_point(), mouseSpeed="medium")
                self._sleep(0.3, 0.9)
        except Exception as exc:
            self.log_msg(f"Inventory check error: {exc}")

    def _random_skill_check(self) -> None:
        try:
            if len(self.win.cp_tabs) > 1 and len(self.win.cp_tabs) > 3:
                self.mouse.move_to(self.win.cp_tabs[1].random_point(), mouseSpeed="fast")
                self.mouse.click()
                self._sleep(0.7, 1.8)
                self.mouse.move_to(self.win.cp_tabs[3].random_point(), mouseSpeed="fast")
                self.mouse.click()
                self._sleep(0.2, 0.6)
        except Exception as exc:
            self.log_msg(f"Skill check error: {exc}")

    def _thinking_pause(self) -> None:
        self._sleep(0.4, 1.6, mean=0.9, std=0.3)

    def _maybe_take_break(self) -> None:
        if not self.take_breaks:
            return
        if random.random() < 0.02:
            break_length = rd.truncated_normal_sample(8, 35, mean=16, std=6)
            self.log_msg(f"Taking a short break ({int(break_length)}s)")
            self._sleep(break_length * 0.9, break_length * 1.1)

    def _open_inventory_tab(self) -> None:
        if len(self.win.cp_tabs) > 3:
            self.mouse.move_to(self.win.cp_tabs[3].random_point(), mouseSpeed="fast")
            self.mouse.click()
            self._sleep(0.2, 0.5)

    def _inventory_is_full(self) -> bool:
        return self.is_inventory_full_visual()

    def _handle_inventory_full(self) -> bool:
        self.log_msg(f"Handling full inventory with mode: {self.inventory_mode}")
        if self.inventory_mode == "Drop":
            return self._drop_inventory()
        if self.inventory_mode == "Bank (tagged)":
            self._stop_with_message("Banking is not implemented yet. Stopping Mining v2.")
            return False
        self.log_msg(f"Unknown inventory mode: {self.inventory_mode}")
        return False

    def _drop_inventory(self) -> bool:
        if self.ore_type == "Any":
            self.log_msg("Dropping inventory...")
            self.drop_all()
            self._sleep(0.6, 1.4)
            return True

        return self._drop_specific_ore()

    def _drop_specific_ore(self) -> bool:
        template_path = self._get_ore_template_path()
        if template_path is None:
            self._stop_with_message(f"No template available for ore type '{self.ore_type}'. Stopping.")
            return False

        slots = self.find_item_in_inventory_visual(template_path, confidence=0.8)
        if not slots:
            self._stop_with_message(
                f"Inventory is full but no {self.ore_type} ore detected to drop. Stopping."
            )
            return False

        self.log_msg(f"Dropping {self.ore_type} ore from slots: {slots}")
        self.drop(slots)
        self._sleep(0.4, 1.0)

        if self.is_inventory_full_visual():
            self._stop_with_message(
                f"Inventory still full after dropping {self.ore_type} ore. Stopping."
            )
            return False

        return True

    def _get_ore_template_path(self) -> Optional[str]:
        filename = self.ORE_TEMPLATES.get(self.ore_type)
        if not filename:
            return None
        return str(imsearch.get_template_path("mining", filename))

    def _select_rock_target(self) -> Optional[RuneLiteObject]:
        color = self.COLOR_OPTIONS.get(self.ore_tag_color_name, clr.PINK)
        rocks = self.get_all_tagged_in_rect(self.win.game_view, color)
        if not rocks:
            return None
        valid = [rock for rock in rocks if self._is_valid_target(rock)]
        if not valid:
            valid = rocks
        valid.sort(key=RuneLiteObject.distance_from_rect_center)
        selection_pool = valid[: min(3, len(valid))]
        if random.random() < 0.7:
            return selection_pool[0]
        return random.choice(selection_pool)

    def _is_valid_target(self, target: RuneLiteObject) -> bool:
        area = target._width * target._height
        if area < 250 or area > 120000:
            return False
        if target._height <= 0:
            return False
        aspect = target._width / target._height
        return 0.2 < aspect < 5.0

    def _attempt_mine(self, target: RuneLiteObject) -> bool:
        try:
            click_point = target.random_point()
            if random.random() < 0.08:
                miss = Point(click_point.x + random.randint(-12, 12), click_point.y + random.randint(-12, 12))
                self.mouse.move_to(miss, mouseSpeed="fast")
                self.mouse.click()
                self._sleep(0.2, 0.6)

            self.mouse.move_to(click_point, mouseSpeed=random.choice(["slow", "medium", "fast"]))
            self._sleep(0.1, 0.4)

            if not self._is_mine_hover():
                return False

            self.mouse.click()
            self._sleep(0.2, 0.6)
            return True
        except Exception as exc:
            self.log_msg(f"Mine attempt error: {exc}")
            return False

    def _is_mine_hover(self) -> bool:
        if not self.mouseover_text(contains="Mine"):
            return False
        if self.ore_type == "Any":
            return True
        if random.random() < 0.6:
            return self.mouseover_text(contains=self.ore_type)
        return True

    def _wait_for_mine_start(self) -> bool:
        timeout = rd.truncated_normal_sample(1.5, 4.0, mean=2.5, std=0.6)
        start = time.time()
        while time.time() - start < timeout:
            if self.status != BotStatus.RUNNING:
                return False
            if self._is_mining():
                return True
            self._sleep(0.08, 0.25)
        self._log_action_text_debug("mine_start_timeout")
        return False

    def _wait_while_mining(self) -> bool:
        timeout = rd.truncated_normal_sample(12, 45, mean=26, std=7)
        start = time.time()
        while self._is_mining():
            if self.status != BotStatus.RUNNING:
                return False
            if time.time() - start > timeout:
                self._log_action_text_debug("mine_timeout")
                return False
            if random.random() < 0.12:
                self._micro_behavior_during_mine()
            self._sleep(0.2, 0.6)
        return True

    def _is_mining(self) -> bool:
        if self.is_player_doing_action("Mining"):
            return True
        return self._action_text_contains(["Mining", "Swinging"])

    def _action_text_contains(self, words: List[str]) -> bool:
        try:
            colors = [clr.GREEN, clr.OFF_GREEN, clr.OFF_WHITE, clr.OFF_YELLOW]
            rects = ocr.find_text(words, self.win.current_action, ocr.PLAIN_12, colors)
            if rects:
                return True
            extracted = ocr.extract_text(self.win.current_action, ocr.PLAIN_12, colors)
            if not extracted:
                return False
            hay = extracted.lower()
            return any(word.replace(" ", "").lower() in hay for word in words)
        except Exception as exc:
            self.log_msg(f"Action text check error: {exc}")
            return False

    def _log_action_text_debug(self, reason: str) -> None:
        try:
            colors = [clr.GREEN, clr.OFF_GREEN, clr.OFF_WHITE, clr.OFF_YELLOW]
            extracted = ocr.extract_text(self.win.current_action, ocr.PLAIN_12, colors)
            rect = self.win.current_action
            self.log_msg(
                f"Action text debug ({reason}): '{extracted}' "
                f"rect=({rect.left},{rect.top},{rect.width},{rect.height})"
            )
        except Exception as exc:
            self.log_msg(f"Action text debug failed: {exc}")

    def _micro_behavior_during_mine(self) -> None:
        actions = [
            self._mini_camera_adjust,
            self._random_mouse_movement,
            self._thinking_pause,
        ]
        random.choice(actions)()

    def _check_stuck(self, last_action_time: float, last_progress_time: float) -> bool:
        now = time.time()
        if now - last_action_time > self._idle_timeout:
            self._run_recovery("idle too long")
            self._reset_timeouts()
            return True
        if now - last_progress_time > self._progress_timeout:
            self._run_recovery("no progress")
            self._reset_timeouts()
            return True
        return False

    def _run_recovery(self, reason: str) -> None:
        self.log_msg(f"Recovery step {self._recovery_stage + 1}: {reason}")
        plan = [
            self._zoom_out,
            self._open_inventory_tab,
            self._mini_camera_adjust,
            self._rotate_camera_search,
            self._click_ground_near_center,
            self.set_compass_north,
        ]
        step = plan[min(self._recovery_stage, len(plan) - 1)]
        step()
        self._sleep(0.4, 1.2)
        self._recovery_stage += 1

        if self._recovery_stage >= len(plan) + 2:
            self.log_msg("Recovery escalated, taking longer pause.")
            self._sleep(3.5, 7.5)
            self._recovery_stage = 0

    def _rotate_camera_search(self) -> None:
        try:
            horizontal = random.choice([-1, 1]) * random.randint(120, 180)
            vertical = random.randint(-15, 15) if random.random() < 0.6 else 0
            self.move_camera(horizontal=horizontal, vertical=vertical)
            self._sleep(0.2, 0.7)
        except Exception as exc:
            self.log_msg(f"Camera rotate error: {exc}")

    def _zoom_out(self) -> None:
        self.log_msg("Zooming out for better view...")
        try:
            if not self._ensure_focus():
                self.log_msg("Cannot zoom out, game not focused.")
                return
            center = self.win.game_view.get_center()
            self.mouse.move_to(center, mouseSpeed="fast")
            self._sleep(0.1, 0.25)
            scroll_clicks = random.randint(3, 6)
            for _ in range(scroll_clicks):
                pag.scroll(-240)
                self._sleep(0.05, 0.12)
            self._sleep(0.2, 0.5)
        except Exception as exc:
            self.log_msg(f"Zoom error: {exc}")

    def _click_ground_near_center(self) -> None:
        try:
            center = self.win.game_view.get_center()
            target = Point(
                center.x + random.randint(-90, 90),
                center.y + random.randint(-60, 60),
            )
            self.mouse.move_to(target, mouseSpeed="fast")
            self._sleep(0.1, 0.3)
            self.mouse.click()
            self._sleep(0.3, 0.8)
        except Exception as exc:
            self.log_msg(f"Ground click error: {exc}")

    def _stop_with_message(self, message: str) -> None:
        self.log_msg(message)
        self.set_status(BotStatus.STOPPED)
