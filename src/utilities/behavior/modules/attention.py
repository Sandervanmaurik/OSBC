"""Attention behavior module for random attention patterns."""

import random
import time
from typing import Dict, Any

import utilities.random_util as rd
from utilities.behavior.base import BaseBehaviorModule


class AttentionBehavior(BaseBehaviorModule):
    """
    Handles random attention behaviors.

    Simulates human attention patterns like looking around (camera movement),
    checking stats, moving mouse randomly, etc. These behaviors occur
    periodically in the background to make bot activity appear more natural.

    Example:
        # In bot main loop
        self.behavior.attention.perform_random_behaviors()

        # Disable camera for specific bot (e.g., fletching at bank)
        self.behavior.attention.update_config(camera_enabled=False)
    """

    def __init__(self, config: Dict[str, Any], bot):
        """Initialize attention behavior with timing tracking."""
        super().__init__(config, bot)

        # Track last execution times
        self._last_camera_move = time.time()
        self._last_skill_check = time.time()
        self._last_mouse_movement = time.time()
        self._last_inventory_check = time.time()

        # Generate intervals
        self._camera_interval = self._random_interval("camera")
        self._skill_interval = self._random_interval("skill_check")
        self._mouse_interval = self._random_interval("mouse_movement")
        self._inventory_interval = self._random_interval("inventory_check")

    def get_default_config(self) -> Dict[str, Any]:
        """Return default attention configuration."""
        return {
            "camera_enabled": True,
            "camera_interval": (30.0, 90.0),
            "camera_horizontal_range": (-120, 120),
            "camera_vertical_range": (-20, 20),
            "camera_vertical_chance": 0.3,
            "skill_check_enabled": True,
            "skill_check_interval": (60.0, 180.0),
            "mouse_movement_enabled": True,
            "mouse_movement_interval": (45.0, 120.0),
            "inventory_check_enabled": True,
            "inventory_check_interval": (40.0, 100.0),
        }

    def _random_interval(self, behavior_type: str) -> float:
        """
        Generate random interval for a behavior type.

        Args:
            behavior_type: "camera", "skill_check", "mouse_movement", "inventory_check"

        Returns:
            Random interval in seconds
        """
        interval_key = f"{behavior_type}_interval"
        interval_range = self.config.get(interval_key, (30.0, 90.0))
        min_interval, max_interval = interval_range

        # Use truncated normal with mean and std
        mean = (min_interval + max_interval) / 2
        std = (max_interval - min_interval) / 6
        return rd.truncated_normal_sample(
            min_interval, max_interval, mean=mean, std=std
        )

    def perform_random_behaviors(self) -> None:
        """
        Check and perform all random behaviors based on their intervals.

        Call this periodically in your bot's main loop.

        Example:
            while session.running:
                self.behavior.attention.perform_random_behaviors()
                # ... rest of bot logic
        """
        if not self.enabled:
            return

        now = time.time()

        # Camera movement
        if self.config.get("camera_enabled", True):
            if now - self._last_camera_move >= self._camera_interval:
                if random.random() < 0.7:  # Don't always move camera
                    self.random_camera_movement()
                self._last_camera_move = now
                self._camera_interval = self._random_interval("camera")

        # Skill check
        if self.config.get("skill_check_enabled", True):
            if now - self._last_skill_check >= self._skill_interval:
                self.random_skill_check()
                self._last_skill_check = now
                self._skill_interval = self._random_interval("skill_check")

        # Mouse movement
        if self.config.get("mouse_movement_enabled", True):
            if now - self._last_mouse_movement >= self._mouse_interval:
                self.random_mouse_movement()
                self._last_mouse_movement = now
                self._mouse_interval = self._random_interval("mouse_movement")

        # Inventory check
        if self.config.get("inventory_check_enabled", True):
            if now - self._last_inventory_check >= self._inventory_interval:
                self.check_inventory_random()
                self._last_inventory_check = now
                self._inventory_interval = self._random_interval("inventory_check")

    def random_camera_movement(self) -> None:
        """
        Perform random camera movement.

        Rotates camera horizontally and sometimes vertically to simulate
        looking around.
        """
        if not self.enabled or not self.config.get("camera_enabled", True):
            return

        try:
            h_range = self.config.get("camera_horizontal_range", (-120, 120))
            horizontal = random.randint(h_range[0], h_range[1])

            vertical = 0
            if random.random() < self.config.get("camera_vertical_chance", 0.3):
                v_range = self.config.get("camera_vertical_range", (-20, 20))
                vertical = random.randint(v_range[0], v_range[1])

            if horizontal == 0 and vertical == 0:
                return

            self.bot.move_camera(horizontal=horizontal, vertical=vertical)
            self.bot.behavior.timing.sleep((0.2, 0.6))
        except Exception as exc:
            self.bot.log_msg(f"Camera move error: {exc}")

    def mini_camera_adjust(self) -> None:
        """
        Small camera adjustment (less rotation than full movement).

        Useful for subtle "looking around" during activities.
        """
        if not self.enabled or not self.config.get("camera_enabled", True):
            return

        try:
            horizontal = random.randint(-45, 45)
            self.bot.move_camera(horizontal=horizontal)
            self.bot.behavior.timing.sleep((0.15, 0.45))
        except Exception as exc:
            self.bot.log_msg(f"Mini camera adjust error: {exc}")

    def random_mouse_movement(self) -> None:
        """
        Move mouse to random location on game screen.

        Simulates idle mouse movements humans make.
        """
        if not self.enabled or not self.config.get("mouse_movement_enabled", True):
            return

        try:
            point = self.bot.win.game_view.random_point()
            speed = random.choice(["medium", "fast", "fastest"])
            self.bot.behavior.mouse.move_to(point, mouseSpeed=speed)
            self.bot.behavior.timing.sleep((0.2, 0.7))
        except Exception as exc:
            self.bot.log_msg(f"Random mouse movement error: {exc}")

    def check_inventory_random(self) -> None:
        """
        Randomly check inventory (open tab and hover over item).

        Simulates checking inventory status.
        """
        if not self.enabled or not self.config.get("inventory_check_enabled", True):
            return

        try:
            # Click inventory tab
            if len(self.bot.win.cp_tabs) > 3:
                self.bot.behavior.mouse.move_to(
                    self.bot.win.cp_tabs[3].random_point(), mouseSpeed="fast"
                )
                self.bot.behavior.mouse.click()
                self.bot.behavior.timing.sleep((0.2, 0.6))

            # Hover over random item
            if self.bot.win.inventory_slots:
                slot = random.choice(self.bot.win.inventory_slots)
                self.bot.behavior.mouse.move_to(
                    slot.random_point(), mouseSpeed="medium"
                )
                self.bot.behavior.timing.sleep((0.3, 0.9))
        except Exception as exc:
            self.bot.log_msg(f"Inventory check error: {exc}")

    def random_skill_check(self) -> None:
        """
        Randomly check skill levels.

        Opens skills tab, waits briefly, then returns to inventory.
        """
        if not self.enabled or not self.config.get("skill_check_enabled", True):
            return

        try:
            if len(self.bot.win.cp_tabs) <= 3:
                return

            # Check if bot has refresh_skill_levels method
            if hasattr(self.bot, "refresh_skill_levels"):
                self.bot.refresh_skill_levels(open_tab=True, return_to_inventory=True)
            else:
                # Fallback: manually open skills tab
                self.bot.behavior.mouse.move_to(
                    self.bot.win.cp_tabs[1].random_point(), mouseSpeed="fast"
                )
                self.bot.behavior.mouse.click()
                self.bot.behavior.timing.sleep((0.7, 1.8))

                # Return to inventory
                self.bot.behavior.mouse.move_to(
                    self.bot.win.cp_tabs[3].random_point(), mouseSpeed="fast"
                )
                self.bot.behavior.mouse.click()
                self.bot.behavior.timing.sleep((0.2, 0.6))
        except Exception as exc:
            self.bot.log_msg(f"Skill check error: {exc}")

    def thinking_pause(self) -> None:
        """
        Brief thinking pause (delegates to timing module).

        Convenience method for attention-related pauses.
        """
        if self.enabled:
            self.bot.behavior.timing.thinking_pause()
