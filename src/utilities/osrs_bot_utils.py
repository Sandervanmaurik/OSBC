import random
import time
from typing import List, Optional

import pyautogui as pag

import utilities.color as clr
import utilities.ocr as ocr
import utilities.random_util as rd
from model.bot import BotStatus
from utilities.geometry import Point, RuneLiteObject


class OSRSBotBehaviorMixin:
    """Shared human-like behavior and recovery helpers for OSRS bots.

    Expects the consuming bot to provide:
    - win, mouse, move_camera, set_compass_north
    - _ensure_focus, _safe_key_press, _safe_key_down, _safe_key_up
    - status, thread, log_msg
    - state fields: _last_camera_move, _last_random_action, _camera_interval,
      _action_interval, _recovery_stage, _idle_timeout, _progress_timeout
    - config field: take_breaks
    """

    def _sleep(
        self,
        min_seconds: float,
        max_seconds: float,
        mean: Optional[float] = None,
        std: Optional[float] = None,
    ) -> float:
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

    def _micro_behavior_during_action(self) -> None:
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

    def _select_tagged_target(self, targets: List[RuneLiteObject]) -> Optional[RuneLiteObject]:
        if not targets:
            return None
        valid = [target for target in targets if self._is_valid_target(target)]
        if not valid:
            valid = targets
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
