import random
import time
from typing import Dict, List, Optional

import cv2
import numpy as np
import utilities.color as clr
import utilities.game_launcher as launcher
import utilities.imagesearch as imsearch
import utilities.random_util as rd
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
from utilities.geometry import Point, RuneLiteObject
from utilities.osrs_bot_utils import OSRSBotBehaviorMixin


class OSRSMiningV2(OSRSBotBehaviorMixin, OSRSBot, launcher.Launchable):
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

    COLOR_BASES: Dict[str, tuple[int, int, int]] = {
        "Pink": (255, 0, 255),
        "Green": (0, 255, 0),
        "Cyan": (0, 255, 255),
        "Yellow": (255, 255, 0),
        "Red": (255, 0, 0),
        "White": (255, 255, 255),
    }

    PINK_TAG_RANGE = ([205, 0, 205], [255, 80, 255])

    TAG_COLOR_TOLERANCE = 35
    MIN_TAG_AREA = 60

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
        color = self._resolve_tag_color(self.ore_tag_color_name)
        rocks = self._get_tagged_rocks(color)
        return self._select_tagged_target(rocks)

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
                self._micro_behavior_during_action()
            self._sleep(0.2, 0.6)
        return True

    def _is_mining(self) -> bool:
        if self.is_player_doing_action("Mining"):
            return True
        return self._action_text_contains(["Mining", "Swinging"])


    def _stop_with_message(self, message: str) -> None:
        self.log_msg(message)
        self.set_status(BotStatus.STOPPED)

    def _resolve_tag_color(self, name: str):
        if name == "Pink":
            lower, upper = self.PINK_TAG_RANGE
            return clr.Color(lower, upper)
        rgb = self.COLOR_BASES.get(name, (255, 0, 255))
        tolerance = self.TAG_COLOR_TOLERANCE
        lower = [max(0, channel - tolerance) for channel in rgb]
        upper = [min(255, channel + tolerance) for channel in rgb]
        return clr.Color(lower, upper)

    def _get_tagged_rocks(self, color: clr.Color) -> List[RuneLiteObject]:
        rocks = self.get_all_tagged_in_rect(self.win.game_view, color)
        if rocks:
            return rocks
        self.log_msg("Fallback tag detection activated (small outlines).")
        return self._get_tagged_rocks_fallback(color)

    def _get_tagged_rocks_fallback(self, color: clr.Color) -> List[RuneLiteObject]:
        game_view = self.win.game_view
        img = game_view.screenshot()
        mask = clr.isolate_colors(img, color)
        kernel = np.ones((2, 2), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rocks: List[RuneLiteObject] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.MIN_TAG_AREA:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            obj_mask = np.zeros(mask.shape, dtype=np.uint8)
            cv2.drawContours(obj_mask, [contour], -1, 255, -1)
            indices = np.where(obj_mask == 255)
            if indices[0].size == 0:
                continue
            x_min, x_max = np.min(indices[1]), np.max(indices[1])
            y_min, y_max = np.min(indices[0]), np.max(indices[0])
            width, height = x_max - x_min, y_max - y_min
            center = [int(x_min + (width / 2)), int(y_min + (height / 2))]
            axis = np.column_stack((indices[1], indices[0]))
            rock = RuneLiteObject(x_min, x_max, y_min, y_max, width, height, center, axis)
            rock.set_rectangle_reference(game_view)
            rocks.append(rock)
        return rocks
