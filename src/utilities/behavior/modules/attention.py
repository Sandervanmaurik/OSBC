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
        self._last_tab_out = time.time()
        self._last_bank_check = time.time()

        # Generate intervals (camera interval is lazy-initialized)
        self._camera_interval = None  # Will be set on first access
        self._skill_interval = self._random_interval("skill_check")
        self._mouse_interval = self._random_interval("mouse_movement")
        self._inventory_interval = self._random_interval("inventory_check")
        self._tab_out_interval = self._random_interval("tab_out")
        self._bank_check_interval = self._random_interval("bank_check")

    def _random_camera_interval(self) -> float:
        """Generate random camera interval from profile config."""
        import utilities.random_util as rd

        # Get camera config from BehaviorManager
        camera_cfg = self.bot.behavior.get_camera_config()
        min_int, max_int = camera_cfg.interval_range

        return rd.truncated_normal_sample(
            min_int, max_int, mean=(min_int + max_int) / 2, std=(max_int - min_int) / 6
        )

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
            "tab_out_enabled": False,
            "tab_out_interval": (180.0, 600.0),
            "tab_out_duration": (5.0, 20.0),
            "bank_check_enabled": False,
            "bank_check_interval": (120.0, 300.0),
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

        # Camera movement (using profile)
        camera_cfg = self.bot.behavior.get_camera_config()
        if camera_cfg.enabled:
            # Lazy-initialize camera interval on first use
            if self._camera_interval is None:
                self._camera_interval = self._random_camera_interval()

            if now - self._last_camera_move >= self._camera_interval:
                if random.random() < 0.7:  # Don't always move camera
                    self.random_camera_movement()
                    self.bot.behavior.increment_stat("camera")
                self._last_camera_move = now
                self._camera_interval = self._random_camera_interval()

        # Skill check
        if self.config.get("skill_check_enabled", True):
            if now - self._last_skill_check >= self._skill_interval:
                self.random_skill_check()
                self.bot.behavior.increment_stat("skill_check")
                self._last_skill_check = now
                self._skill_interval = self._random_interval("skill_check")

        # Mouse movement
        if self.config.get("mouse_movement_enabled", True):
            if now - self._last_mouse_movement >= self._mouse_interval:
                self.random_mouse_movement()
                self.bot.behavior.increment_stat("mouse_movement")
                self._last_mouse_movement = now
                self._mouse_interval = self._random_interval("mouse_movement")

        # Inventory check
        if self.config.get("inventory_check_enabled", True):
            if now - self._last_inventory_check >= self._inventory_interval:
                self.check_inventory_random()
                self.bot.behavior.increment_stat("inventory_check")
                self._last_inventory_check = now
                self._inventory_interval = self._random_interval("inventory_check")

        # Tab-out (NEW)
        if self.config.get("tab_out_enabled", False):
            if now - self._last_tab_out >= self._tab_out_interval:
                if random.random() < 0.7:  # Don't always tab out
                    self.tab_out()
                    self.bot.behavior.increment_stat("tab_out")
                self._last_tab_out = now
                self._tab_out_interval = self._random_interval("tab_out")

        # Bank check (NEW)
        if self.config.get("bank_check_enabled", False):
            if now - self._last_bank_check >= self._bank_check_interval:
                if random.random() < 0.6:  # Don't always check
                    self.random_bank_check()
                    self.bot.behavior.increment_stat("bank_check")
                self._last_bank_check = now
                self._bank_check_interval = self._random_interval("bank_check")

    def random_camera_movement(self) -> None:
        """
        Perform random camera movement using profile configuration.

        Rotates camera horizontally and sometimes vertically to simulate
        looking around.
        """
        if not self.enabled:
            return

        # Get camera config from BehaviorManager
        camera_cfg = self.bot.behavior.get_camera_config()
        if not camera_cfg.enabled:
            return

        try:
            # Use profile horizontal range
            h_range = camera_cfg.horizontal_range
            horizontal = random.randint(h_range[0], h_range[1])

            # Use profile vertical settings
            vertical = 0
            if random.random() < camera_cfg.vertical_chance:
                v_range = camera_cfg.vertical_range
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

    def tab_out(self) -> None:
        """
        Simulate tabbing out of the game.

        Moves mouse outside the game window, pauses for 5-20 seconds
        (based on profile), then returns mouse to game area.

        This simulates a player checking other applications, looking
        at Discord, browsing the web, etc.
        """
        if not self.enabled or not self.config.get("tab_out_enabled", False):
            return

        try:
            # Get game window bounds
            if not self.bot.win or not self.bot.win.game_view:
                return

            game_view = self.bot.win.game_view

            # Choose random exit side (top, bottom, left, right)
            side = random.choice(["top", "bottom", "left", "right"])

            # Calculate point 50-150 pixels outside window
            exit_distance = random.randint(50, 150)

            if side == "top":
                target_x = random.randint(game_view.left, game_view.right)
                target_y = game_view.top - exit_distance
            elif side == "bottom":
                target_x = random.randint(game_view.left, game_view.right)
                target_y = game_view.bottom + exit_distance
            elif side == "left":
                target_x = game_view.left - exit_distance
                target_y = random.randint(game_view.top, game_view.bottom)
            else:  # right
                target_x = game_view.right + exit_distance
                target_y = random.randint(game_view.top, game_view.bottom)

            from utilities.geometry import Point

            target_point = Point(target_x, target_y)

            # Move mouse outside window (medium speed - not too fast)
            self.bot.behavior.mouse.move_to(target_point, mouseSpeed="medium")

            # Wait off-screen (duration from profile config)
            min_dur, max_dur = self.config.get("tab_out_duration", (5.0, 20.0))
            duration = rd.truncated_normal_sample(
                min_dur,
                max_dur,
                mean=(min_dur + max_dur) / 2,
                std=(max_dur - min_dur) / 6,
            )

            self.bot.log_msg(f"[Tab-out] Moving {side} for {int(duration)}s...")
            time.sleep(duration)

            # Return mouse to game area (slow speed - just returned from tab)
            return_point = game_view.random_point()
            self.bot.behavior.mouse.move_to(return_point, mouseSpeed="slow")

            # Brief pause before resuming activity
            self.bot.behavior.timing.sleep((0.3, 1.2))

        except Exception as exc:
            self.bot.log_msg(f"Tab-out error: {exc}")

    def random_bank_check(self) -> None:
        """
        Randomly check bank contents.

        Opens bank interface, hovers over 2-4 random items (as if checking
        what's in the bank), then closes. Simulates a player verifying
        their bank has the items they need.

        Only works for bank-standing profiles.
        """
        if not self.enabled or not self.config.get("bank_check_enabled", False):
            return

        try:
            import utilities.color as clr

            self.bot.log_msg(f"[Bank-check] Opening bank...")

            # Find green-tagged bank
            bank_point = self.bot.get_nearest_tag(clr.GREEN)
            if not bank_point:
                self.bot.log_msg(f"[Bank-check] Bank not found (no green tag)")
                return

            # Move to and click bank
            self.bot.behavior.mouse.move_to(bank_point, mouseSpeed="medium")
            self.bot.behavior.timing.sleep((0.1, 0.3))
            self.bot.behavior.mouse.click()

            # Wait for bank interface to open
            self.bot.behavior.timing.sleep((0.8, 1.5))

            # Hover over random bank items (2-4 items)
            num_items = random.randint(2, 4)
            self.bot.log_msg(f"[Bank-check] Hovering over {num_items} items...")
            for _ in range(num_items):
                if self.bot.win.bank_slots:
                    slot = random.choice(self.bot.win.bank_slots)
                    self.bot.behavior.mouse.move_to(
                        slot.random_point(), mouseSpeed="fast"
                    )
                    self.bot.behavior.timing.sleep((0.3, 0.8))

            # Close bank (press escape)
            self.bot.keyboard.press("escape")
            self.bot.behavior.timing.sleep((0.4, 1.0))

            self.bot.log_msg(f"[Bank-check] Complete")

        except Exception as exc:
            self.bot.log_msg(f"Bank check error: {exc}")

    def thinking_pause(self) -> None:
        """
        Brief thinking pause (delegates to timing module).

        Convenience method for attention-related pauses.
        """
        if self.enabled:
            self.bot.behavior.timing.thinking_pause()
