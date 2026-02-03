import math
import random
import time
from typing import List, Optional

import cv2
import numpy as np
import pyautogui as pag
import utilities.color as clr
import utilities.game_launcher as launcher
import utilities.imagesearch as imsearch
import utilities.ocr as ocr
import utilities.random_util as rd
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
from utilities.geometry import Point, Rectangle, RuneLiteObject
from utilities.osrs_bot_utils import OSRSBotBehaviorMixin

# === Import behavior system ===
from utilities.behavior import BehaviorManager
from utilities.behavior.profiles import MouseProfile, CameraProfile


class OSRSFishing(OSRSBotBehaviorMixin, OSRSBot, launcher.Launchable):
    """
    Human-like fishing bot using pink fishing spot tiles.

    How to use:
    - Enable fishing spot tiles (pink outline) with pink fish labels above the spot.
    - Stand near fishing spots and keep the inventory tab available (default layout).
    - Raw shrimp only for now.
    """

    FISH_TYPES = ["Raw shrimp"]
    INVENTORY_MODES = ["Drop"]

    FISH_TEMPLATES = {
        "Raw shrimp": "raw_shrimp.png",
    }

    SPOT_COLOR = clr.Color([138, 0, 148], [198, 60, 208])
    LABEL_COLOR = clr.Color([138, 0, 148], [198, 60, 208])
    TAG_MIN_AREA = 40
    TAG_MIN_WIDTH = 12
    TAG_MIN_HEIGHT = 12
    PLAYER_TILE_PADDING = 6
    PLAYER_TILE_RADIUS = 28
    LABEL_HEIGHT_ABOVE = 80
    LABEL_HEIGHT_BELOW = 6
    LABEL_HALF_WIDTH = 140

    def __init__(self) -> None:
        bot_title = "Fishing"
        description = (
            "Human-like fishing using light blue fishing spot tiles. "
            "Supports dropping raw shrimp. Uses behavior system for natural actions."
        )
        super().__init__(bot_title=bot_title, description=description)

        self.running_time = 60  # minutes
        self.take_breaks = False
        self.fish_type = "Raw shrimp"
        self.inventory_mode = "Drop"

        # Enable default options - can be customized via Options button
        self.options_set = True

        self._last_camera_move = 0.0
        self._last_random_action = 0.0
        self._camera_interval = 0.0
        self._action_interval = 0.0
        self._recovery_stage = 0
        self._idle_timeout = 25.0
        self._progress_timeout = 90.0
        self._last_offscreen_time = 0.0
        self._offscreen_interval = 0.0
        self._state = "idle"

        # === Initialize behavior system ===
        self.behavior = BehaviorManager(
            bot=self,
            profile="low-active",  # Balanced for active gameplay
            mouse_profile=MouseProfile.ACTIVE,
            camera_profile=CameraProfile.ACTIVE,
            custom_config={
                "timing": {
                    "speed_multiplier": 1.0,  # Normal speed for fishing
                },
                "mouse": {
                    "default_speed": "fast",
                },
                "action": {
                    "misclick_chance": 0.08,  # Match current 8%
                    "hesitation_chance": 0.10,
                },
                "attention": {
                    "camera_enabled": True,
                    "skill_check_enabled": True,
                    "mouse_movement_enabled": True,
                    "inventory_check_enabled": True,
                },
                "breaks": {
                    "enabled": False,  # Keep custom break logic
                },
            },
        )

    def create_options(self) -> None:
        self.options_builder.add_slider_option(
            "running_time", "How long to run (minutes)?", 1, 500
        )
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])
        self.options_builder.add_dropdown_option(
            "fish_type", "Fish type", self.FISH_TYPES
        )
        self.options_builder.add_dropdown_option(
            "inventory_mode", "Inventory handling", self.INVENTORY_MODES
        )

    def save_options(self, options: dict) -> None:
        for option in options:
            if option == "running_time":
                self.running_time = int(options[option])
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            elif option == "fish_type":
                self.fish_type = options[option]
            elif option == "inventory_mode":
                self.inventory_mode = options[option]
            else:
                self.log_msg(f"Unknown option: {option}")
                self.options_set = False
                return

        self.log_msg(f"Running time: {self.running_time} minutes")
        self.log_msg(f"Take breaks: {self.take_breaks}")
        self.log_msg(f"Fish type: {self.fish_type}")
        self.log_msg(f"Inventory mode: {self.inventory_mode}")
        self.options_set = True

    def main_loop(self) -> None:
        self._set_state("starting")
        self.log_msg("Starting fishing bot...")
        self._open_inventory_tab()
        self._reset_random_intervals()
        self._reset_timeouts()
        self._reset_offscreen_interval()

        # === Initialize behavior display ===
        self.behavior.log_stats_summary(self.log_msg)
        if hasattr(self, "controller") and self.controller:
            self.controller.update_behavior_display()

        # Track time for periodic stats logging
        last_stats_log = time.time()
        stats_log_interval = 300.0  # 5 minutes

        last_action_time = time.time()
        last_progress_time = time.time()
        last_inventory_count = self.count_inventory_items_visual()
        search_failures = 0

        with self.timed_session(self.running_time) as session:
            self.behavior.start_fidgeting(self)
            try:
                while session.running:
                    if self._should_stop():
                        break

                    self._set_state("scanning")
                    # === Use behavior system for random behaviors ===
                    self.behavior.attention.perform_random_behaviors()
                    self._maybe_offscreen_afk()
                    self._maybe_take_break()

                    # === Periodic stats logging ===
                    now = time.time()
                    if now - last_stats_log >= stats_log_interval:
                        self.behavior.log_stats_summary(self.log_msg)
                        if hasattr(self, "controller") and self.controller:
                            stats = self.behavior.get_stats_summary()
                            self.controller.update_behavior_display(stats=stats)
                        last_stats_log = now

                    if self._inventory_is_full():
                        self._set_state("inventory_full")
                        self.log_msg("Inventory full, handling...")
                        handled = self._handle_inventory_full()
                        if handled:
                            last_progress_time = time.time()
                            last_inventory_count = self.count_inventory_items_visual()
                            search_failures = 0
                            self._reset_timeouts()
                            self._recovery_stage = 0
                        # === Use behavior system for sleep ===
                        self.behavior.timing.sleep((0.4, 1.2))
                        continue

                    if self._is_fishing():
                        self._set_state("fishing")
                        last_action_time = time.time()
                        if not self._wait_while_fishing():
                            self._run_recovery("fishing timeout")
                        else:
                            new_count = self.count_inventory_items_visual()
                            if new_count > last_inventory_count:
                                last_inventory_count = new_count
                                last_progress_time = time.time()
                            self._reset_timeouts()
                        self._recovery_stage = 0
                        continue

                    target = self._select_fishing_target()
                    if target is None:
                        self._set_state("no_spot_found")
                        search_failures += 1
                        self.log_msg(f"No fishing spots found (#{search_failures})")
                        if search_failures >= 3:
                            self._run_recovery("no fishing spots found")
                            search_failures = 0
                        # === Use behavior system for sleep ===
                        self.behavior.timing.sleep((0.5, 1.4))
                        if self._check_stuck(last_action_time, last_progress_time):
                            last_action_time = time.time()
                            last_progress_time = time.time()
                        continue

                    search_failures = 0
                    if self._attempt_fish(target):
                        self._set_state("clicking_spot")
                        self.log_msg(
                            "Clicked fishing spot; waiting for fishing to start."
                        )
                        self._set_state("waiting_for_fish")
                        if self._wait_for_fish_start():
                            last_action_time = time.time()
                            session.increment("spots_clicked")
                            if not self._wait_while_fishing():
                                self._run_recovery("fishing timeout")
                            else:
                                new_count = self.count_inventory_items_visual()
                                if new_count > last_inventory_count:
                                    last_inventory_count = new_count
                                    last_progress_time = time.time()
                                self._reset_timeouts()
                                self._recovery_stage = 0
                        else:
                            self._run_recovery("fishing did not start")
                    else:
                        self._set_state("spot_click_failed")
                        # === Use behavior system for sleep ===
                        self.behavior.timing.sleep((0.2, 0.9))

                    if self._check_stuck(last_action_time, last_progress_time):
                        last_action_time = time.time()
                        last_progress_time = time.time()
            finally:
                self.behavior.stop_fidgeting()

        self._set_state("finished")
        self.log_msg("Fishing session complete.")

    def _handle_inventory_full(self) -> bool:
        self.log_msg(f"Handling full inventory with mode: {self.inventory_mode}")
        if self.inventory_mode == "Drop":
            return self._drop_inventory()
        self.log_msg(f"Unknown inventory mode: {self.inventory_mode}")
        return False

    def _drop_inventory(self) -> bool:
        template_path = self._get_fish_template_path()
        if template_path is None:
            self._stop_with_message(
                f"No template available for fish type '{self.fish_type}'. Stopping."
            )
            return False

        slots = self.find_item_in_inventory_visual(template_path, confidence=0.8)
        if not slots:
            self._stop_with_message(
                f"Inventory full but no {self.fish_type} detected to drop. Stopping."
            )
            return False

        self.log_msg(f"Dropping {self.fish_type} from slots: {slots}")
        self._drop_slots_fast(slots)
        # === Use behavior system for sleep ===
        self.behavior.timing.sleep((0.15, 0.45))

        if self.is_inventory_full_visual():
            self._stop_with_message(
                f"Inventory still full after dropping {self.fish_type}. Stopping."
            )
            return False

        return True

    def _drop_slots_fast(self, slots: List[int]) -> None:
        if not slots:
            return
        if not self._safe_key_down("shift"):
            self.log_msg("Failed to start drop: window focus lost")
            return
        try:
            self.behavior.pause_fidgeting()
            total_slots = len(self.win.inventory_slots)
            if total_slots == 0:
                return
            slots_per_row = 4
            total_rows = (total_slots + slots_per_row - 1) // slots_per_row
            drop_set = {int(slot) for slot in slots}

            def _click_slot(slot_idx: int) -> None:
                slot = self.win.inventory_slots[slot_idx]
                p = slot.random_point()
                # === Use behavior system for mouse movement ===
                self.behavior.mouse.move_to(
                    (p[0], p[1]),
                    mouseSpeed="fastest",
                    knotsCount=1,
                    offsetBoundaryX=12,
                    offsetBoundaryY=12,
                )
                # === Use behavior system for timing ===
                self.behavior.timing.sleep((0.01, 0.04))
                self.behavior.mouse.click()
                self.behavior.timing.sleep((0.01, 0.03))

            for pair_start in range(0, total_rows, 2):
                for col in range(slots_per_row):
                    idx_a = pair_start * slots_per_row + col
                    idx_b = (pair_start + 1) * slots_per_row + col

                    clicked = False
                    if idx_a < total_slots and idx_a in drop_set:
                        _click_slot(idx_a)
                        clicked = True
                    if idx_b < total_slots and idx_b in drop_set:
                        _click_slot(idx_b)
                        clicked = True

                    if clicked:
                        # === Use behavior system for sleep ===
                        self.behavior.timing.sleep((0.04, 0.12))

                # === Use behavior system for sleep ===
                self.behavior.timing.sleep((0.06, 0.18))
        finally:
            self.behavior.resume_fidgeting()
            self._safe_key_up("shift")

    def _reset_offscreen_interval(self) -> None:
        now = time.time()
        self._last_offscreen_time = now
        self._offscreen_interval = rd.truncated_normal_sample(80, 220, mean=140, std=30)

    def _maybe_offscreen_afk(self) -> None:
        now = time.time()
        if now - self._last_offscreen_time < self._offscreen_interval:
            return
        self._set_state("offscreen_afk")
        target = self._random_offscreen_point()
        if target is None:
            self._reset_offscreen_interval()
            return
        duration = rd.truncated_normal_sample(2.0, 10.0, mean=3.5, std=1.5)
        try:
            self.log_msg(f"Offscreen AFK for {duration:.1f}s.")
            # === Use behavior system for mouse movement ===
            self.behavior.mouse.move_to(target, mouseSpeed="slow")
            time.sleep(duration)
        except Exception as exc:
            self.log_msg(f"Offscreen afk error: {exc}")
        finally:
            self._reset_offscreen_interval()

    def _random_offscreen_point(self) -> Optional[Point]:
        try:
            screen_w, screen_h = pag.size()
        except Exception:
            return None

        win_rect = self.win.rectangle()
        left_space = win_rect.left
        right_space = screen_w - (win_rect.left + win_rect.width)
        top_space = win_rect.top
        bottom_space = screen_h - (win_rect.top + win_rect.height)

        candidates: List[str] = []
        if left_space > 20:
            candidates.append("left")
        if right_space > 20:
            candidates.append("right")
        if top_space > 20:
            candidates.append("top")
        if bottom_space > 20:
            candidates.append("bottom")

        if not candidates:
            return None

        margin = random.randint(25, 80)
        side = random.choice(candidates)

        if side == "left":
            x = max(0, win_rect.left - margin)
            y = random.randint(win_rect.top + 10, win_rect.top + win_rect.height - 10)
        elif side == "right":
            x = min(screen_w - 1, win_rect.left + win_rect.width + margin)
            y = random.randint(win_rect.top + 10, win_rect.top + win_rect.height - 10)
        elif side == "top":
            x = random.randint(win_rect.left + 10, win_rect.left + win_rect.width - 10)
            y = max(0, win_rect.top - margin)
        else:
            x = random.randint(win_rect.left + 10, win_rect.left + win_rect.width - 10)
            y = min(screen_h - 1, win_rect.top + win_rect.height + margin)

        return Point(int(x), int(y))

    def _get_fish_template_path(self) -> Optional[str]:
        filename = self.FISH_TEMPLATES.get(self.fish_type)
        if not filename:
            return None
        return str(imsearch.get_template_path("fishing_spots", filename))

    def _select_fishing_target(self) -> Optional[RuneLiteObject]:
        spots = self._get_tagged_spots(self.SPOT_COLOR)
        if not spots:
            self.log_msg("No tagged fishing spots found.")
            return None
        self.log_msg(f"Tagged fishing spots found: {len(spots)}")

        template_path = self._get_fish_template_path()
        if template_path is None:
            self.log_msg(f"No template for fish type '{self.fish_type}'.")
            return None

        return self._select_spot_candidate(spots)

    def _select_spot_candidate(
        self, spots: List[RuneLiteObject]
    ) -> Optional[RuneLiteObject]:
        if not spots:
            return None
        valid = [spot for spot in spots if self._is_valid_spot(spot)]
        if not valid:
            valid = spots
        valid.sort(key=RuneLiteObject.distance_from_rect_center)
        selection_pool = valid[: min(3, len(valid))]
        if random.random() < 0.7:
            return selection_pool[0]
        return random.choice(selection_pool)

    def _is_valid_spot(self, spot: RuneLiteObject) -> bool:
        if spot._width < self.TAG_MIN_WIDTH or spot._height < self.TAG_MIN_HEIGHT:
            return False
        area = spot._width * spot._height
        if area < self.TAG_MIN_AREA:
            return False
        if spot._height <= 0:
            return False
        aspect = spot._width / spot._height
        return 0.15 < aspect < 8.0

    def _spot_has_fish_icon(self, spot: RuneLiteObject, template_path: str) -> bool:
        search_rect = self._spot_search_rect(spot, padding=4)
        if search_rect is None:
            return False
        return (
            imsearch.search_img_in_rect(template_path, search_rect, confidence=0.7)
            is not None
        )

    # def _spot_has_shrimp_label(self, spot: RuneLiteObject) -> bool:
    #     self.log_msg("Checking spot label for shrimp...")
    #     label_rect = self._spot_label_rect(spot)
    #     if label_rect is None:
    #         self.log_msg("Label rectangle is None.")
    #         return False
    #     try:
    #         words = ["Shrimp"]
    #         colors = [self.LABEL_COLOR, clr.PINK, clr.PURPLE]
    #         if ocr.find_text(words, label_rect, ocr.PLAIN_12, colors):
    #             return True
    #         if ocr.find_text(words, label_rect, ocr.BOLD_12, colors):
    #             return True
    #     except Exception as exc:
    #         self.log_msg(f"Label OCR error: {exc}")
    #     return False

    def _spot_search_rect(
        self, spot: RuneLiteObject, padding: int = 0
    ) -> Optional[Rectangle]:
        rect = spot.rect or self.win.game_view
        view = self.win.game_view

        left = rect.left + spot._x_min - padding
        top = rect.top + spot._y_min - padding
        right = rect.left + spot._x_max + padding
        bottom = rect.top + spot._y_max + padding

        left = max(view.left, left)
        top = max(view.top, top)
        right = min(view.left + view.width, right)
        bottom = min(view.top + view.height, bottom)

        width = right - left
        height = bottom - top
        if width <= 1 or height <= 1:
            return None
        return Rectangle(left, top, width, height)

    def _spot_label_rect(self, spot: RuneLiteObject) -> Optional[Rectangle]:
        rect = spot.rect or self.win.game_view
        view = self.win.game_view

        center = spot.center()
        left = center.x - self.LABEL_HALF_WIDTH
        right = center.x + self.LABEL_HALF_WIDTH
        bottom = rect.top + spot._y_min
        top = bottom - self.LABEL_HEIGHT_ABOVE
        bottom = bottom + self.LABEL_HEIGHT_BELOW

        left = max(view.left, left)
        right = min(view.left + view.width, right)
        top = max(view.top, top)
        bottom = min(view.top + view.height, bottom)

        width = right - left
        height = bottom - top
        if width <= 1 or height <= 1:
            return None
        return Rectangle(left, top, width, height)

    def _get_tagged_spots(self, color: clr.Color) -> List[RuneLiteObject]:
        spots = self.get_all_tagged_in_rect(self.win.game_view, color)
        if spots:
            return spots
        self.log_msg("Fallback tag detection activated (small outlines).")
        return self._get_tagged_spots_fallback(color)

    def _get_tagged_spots_fallback(self, color: clr.Color) -> List[RuneLiteObject]:
        game_view = self.win.game_view
        img = game_view.screenshot()
        mask = clr.isolate_colors(img, color)
        kernel = np.ones((2, 2), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        spots: List[RuneLiteObject] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.TAG_MIN_AREA:
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
            spot = RuneLiteObject(
                x_min, x_max, y_min, y_max, width, height, center, axis
            )
            spot.set_rectangle_reference(game_view)
            spots.append(spot)
        return spots

    def _attempt_fish(self, target: RuneLiteObject) -> bool:
        try:
            self.behavior.pause_fidgeting()
            click_point = target.random_point()
            # === Use behavior system for misclick simulation ===
            if self.behavior.action.should_misclick():
                self.behavior.action.execute_misclick(target)

            # === Use behavior system for mouse movement ===
            self.behavior.mouse.move_to(
                click_point, mouseSpeed=random.choice(["slow", "medium", "fast"])
            )
            # === Use behavior system for sleep ===
            self.behavior.timing.sleep((0.1, 0.4))

            if not self._is_fish_hover():
                self.log_msg("Hover text did not match fishing spot; retrying.")
                return False

            # === Use behavior system for clicking ===
            self.behavior.mouse.click()
            # === Use behavior system for sleep ===
            self.behavior.timing.sleep((0.2, 0.6))
            return True
        except Exception as exc:
            self.log_msg(f"Fishing attempt error: {exc}")
            return False
        finally:
            self.behavior.resume_fidgeting()

    def _is_fish_hover(self) -> bool:
        if not self.mouseover_text(contains="Fishing spot"):
            return False
        if random.random() < 0.6:
            return self.mouseover_text(contains=["Net", "Bait"])
        return True

    def _wait_for_fish_start(self) -> bool:
        timeout = rd.truncated_normal_sample(1.5, 4.0, mean=2.6, std=0.6)
        start = time.time()
        last_log = start
        self.log_msg("Waiting for fishing to start...")
        while time.time() - start < timeout:
            if self.status != BotStatus.RUNNING:
                return False
            if self._is_fishing():
                self._set_state("fishing")
                self.log_msg("Fishing started.")
                return True
            if time.time() - last_log > 1.5:
                self.log_msg("Still waiting for fishing to start...")
                last_log = time.time()
            # === Use behavior system for sleep ===
            self.behavior.timing.sleep((0.08, 0.25))
        self._log_action_text_debug("fish_start_timeout")
        self.log_msg("Timed out waiting for fishing to start.")
        return False

    def _wait_while_fishing(self) -> bool:
        start = time.time()
        last_log = start
        self._set_state("fishing")
        while self._is_fishing():
            if self.status != BotStatus.RUNNING:
                return False
            if random.random() < 0.12:
                self._micro_behavior_during_action()
            if time.time() - last_log > 6.0:
                self.log_msg("Still fishing...")
                last_log = time.time()
            # === Use behavior system for sleep ===
            self.behavior.timing.sleep((0.2, 0.6))
        self.log_msg("Fishing stopped; searching for a new spot.")
        return True

    def _is_fishing(self) -> bool:
        if self.is_player_doing_action("Fishing"):
            return True
        return self._action_text_contains(["Fishing"])

    def _set_state(self, state: str) -> None:
        if state == self._state:
            return
        self._state = state
        self.set_state(self._state)

    def _stop_with_message(self, message: str) -> None:
        self.log_msg(message)
        self.set_status(BotStatus.STOPPED)


FishingBot = OSRSFishing
