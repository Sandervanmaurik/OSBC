"""
Example of migrating a bot to use the new behavior system.

This file shows a minimal example bot that demonstrates how to integrate
the behavior system into an existing bot.

Before migration:
- Used direct time.sleep() calls
- Used _sleep() helper method
- Manual misclick implementation
- Direct mouse movement calls
- Custom random behavior methods

After migration:
- Uses self.behavior.timing.sleep()
- Uses self.behavior.mouse.move_to()
- Uses self.behavior.action for misclicks
- Uses self.behavior.attention for random behaviors
- Cleaner, more maintainable code
"""

import time
from typing import Optional

from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
from utilities.behavior import BehaviorManager
from utilities.geometry import RuneLiteObject
import utilities.color as clr


class ExampleBot(OSRSBot):
    """Example bot demonstrating behavior system usage."""

    def __init__(self) -> None:
        bot_title = "Example Bot"
        description = "Demonstrates the behavior system"
        super().__init__(bot_title=bot_title, description=description)

        self.running_time = 60
        self.options_set = True

        # === NEW: Initialize behavior system ===
        self.behavior = BehaviorManager(
            bot=self,
            profile="experienced",  # or "cautious", "focused"
            custom_config={
                # Customize for this specific bot
                "attention": {
                    "camera_enabled": True,  # Enable camera for this bot
                    "skill_check_enabled": True,
                },
                "breaks": {
                    "enabled": False,  # Disable breaks by default
                },
            },
        )

    def create_options(self) -> None:
        """Create bot options."""
        self.options_builder.add_slider_option(
            "running_time", "How long to run (minutes)?", 1, 500
        )

    def save_options(self, options: dict) -> None:
        """Save bot options."""
        self.running_time = int(options.get("running_time", 60))
        self.options_set = True

    def main_loop(self) -> None:
        """Main bot loop demonstrating behavior system usage."""
        self.log_msg("Starting example bot...")

        # Open inventory
        self._open_inventory_tab()

        last_action_time = time.time()

        with self.timed_session(self.running_time) as session:
            while session.running:
                if self.status != BotStatus.RUNNING:
                    break

                # === NEW: Use attention behaviors ===
                # This handles camera movement, skill checks, etc.
                self.behavior.attention.perform_random_behaviors()

                # === NEW: Use break behavior ===
                if self.behavior.breaks.should_take_break():
                    self.behavior.breaks.take_break()

                # Find target
                target = self._find_target()
                if target is None:
                    self.log_msg("No target found")
                    # === NEW: Use timing behavior instead of time.sleep() ===
                    self.behavior.timing.sleep("medium")
                    continue

                # Click target with realistic behavior
                if self._click_target(target):
                    last_action_time = time.time()
                    session.increment("targets_clicked")

                # === NEW: Use timing behavior ===
                self.behavior.timing.sleep("short")

        self.log_msg("Example bot session complete.")

    def _open_inventory_tab(self) -> None:
        """Open inventory tab."""
        if len(self.win.cp_tabs) > 3:
            # === NEW: Use mouse behavior ===
            self.behavior.mouse.move_to(
                self.win.cp_tabs[3].random_point(), mouseSpeed="fast"
            )
            self.behavior.mouse.click()
            # === NEW: Use timing behavior ===
            self.behavior.timing.sleep("fast")

    def _find_target(self) -> Optional[RuneLiteObject]:
        """Find a target to click."""
        # Example: find pink-tagged objects
        targets = self.get_all_tagged_in_rect(self.win.game_view, clr.PINK)
        if not targets:
            return None

        # Return nearest target
        targets.sort(key=RuneLiteObject.distance_from_rect_center)
        return targets[0]

    def _click_target(self, target: RuneLiteObject) -> bool:
        """
        Click a target with realistic human behavior.

        OLD WAY:
            click_point = target.random_point()
            if random.random() < 0.08:
                # Misclick
                miss = Point(click_point.x + random.randint(-12, 12), ...)
                self.mouse.move_to(miss, mouseSpeed="fast")
                self.mouse.click()
                time.sleep(rd.truncated_normal_sample(0.2, 0.6))

            self.mouse.move_to(click_point, mouseSpeed="fast")
            time.sleep(rd.truncated_normal_sample(0.1, 0.4))
            self.mouse.click()

        NEW WAY (much cleaner!):
        """
        click_point = target.random_point()

        # === NEW: Use action behavior for realistic clicking ===
        return self.behavior.action.execute_click_sequence(
            click_point, mouseSpeed="fast"
        )

        # Or manual control:
        # if self.behavior.action.should_misclick():
        #     self.behavior.action.execute_misclick(click_point)
        #     return True
        #
        # self.behavior.mouse.move_to(click_point, mouseSpeed="fast")
        # self.behavior.action.pre_click_delay()
        #
        # if self.behavior.action.should_hesitate():
        #     self.behavior.action.hesitate()
        #
        # self.behavior.mouse.click()
        # return True


# ============================================================================
# MIGRATION COMPARISON
# ============================================================================


class OldStyleBot(OSRSBot):
    """Example of old-style bot code (before behavior system)."""

    def __init__(self):
        super().__init__("Old Bot", "Before migration")
        self.options_set = True
        # No behavior system initialization

    def main_loop(self):
        import random
        import utilities.random_util as rd

        while True:
            # OLD: Direct sleep calls
            time.sleep(rd.truncated_normal_sample(0.2, 0.6))

            # OLD: Direct mouse calls
            target = self._find_target()
            if target:
                click_point = target.random_point()

                # OLD: Manual misclick implementation
                if random.random() < 0.08:
                    from utilities.geometry import Point

                    miss = Point(
                        click_point.x + random.randint(-12, 12),
                        click_point.y + random.randint(-12, 12),
                    )
                    self.mouse.move_to(miss, mouseSpeed="fast")
                    self.mouse.click()
                    time.sleep(rd.truncated_normal_sample(0.2, 0.6))

                # OLD: Manual movement and click
                self.mouse.move_to(
                    click_point, mouseSpeed=random.choice(["medium", "fast"])
                )
                time.sleep(rd.truncated_normal_sample(0.1, 0.4))
                self.mouse.click()

            # OLD: Custom random behavior implementation
            if random.random() < 0.05:
                # Camera movement
                h = random.randint(-120, 120)
                self.move_camera(horizontal=h)
                time.sleep(rd.truncated_normal_sample(0.2, 0.6))


class NewStyleBot(OSRSBot):
    """Example of new-style bot code (after migration)."""

    def __init__(self):
        super().__init__("New Bot", "After migration")
        self.options_set = True

        # NEW: Initialize behavior system
        self.behavior = BehaviorManager(bot=self, profile="experienced")

    def main_loop(self):
        while True:
            # NEW: Clean timing call
            self.behavior.timing.sleep("short")

            # NEW: Random behaviors handled automatically
            self.behavior.attention.perform_random_behaviors()

            # NEW: Simplified click sequence
            target = self._find_target()
            if target:
                click_point = target.random_point()

                # NEW: All behaviors (misclick, hesitation, etc.) in one call
                self.behavior.action.execute_click_sequence(click_point)
