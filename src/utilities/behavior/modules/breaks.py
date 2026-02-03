"""Break behavior module for break timing and patterns."""

from typing import Dict, Any

import utilities.random_util as rd
from utilities.behavior.base import BaseBehaviorModule


class BreakBehavior(BaseBehaviorModule):
    """
    Handles break timing and patterns.

    Simulates human break-taking behavior with configurable frequency
    and duration. Breaks are triggered randomly based on configured
    probability.

    Example:
        # In bot main loop
        if self.behavior.breaks.should_take_break():
            self.behavior.breaks.take_break()

        # Enable breaks
        self.behavior.breaks.enable()
        self.behavior.breaks.update_config(chance_per_check=0.03)
    """

    def get_default_config(self) -> Dict[str, Any]:
        """Return default break configuration."""
        return {
            "enabled": False,
            "chance_per_check": 0.02,
            "duration_min": 8.0,
            "duration_max": 35.0,
            "duration_mean": 16.0,
            "duration_std": 6.0,
        }

    def should_take_break(self) -> bool:
        """
        Determine if a break should be taken.

        Call this periodically (e.g., in main loop) to check if it's time
        for a break.

        Returns:
            True if break should be taken

        Example:
            if self.behavior.breaks.should_take_break():
                self.behavior.breaks.take_break()
        """
        if not self.enabled or not self.config.get("enabled", False):
            return False

        chance = self.config.get("chance_per_check", 0.02)
        return rd.random_chance(chance)

    def take_break(self) -> float:
        """
        Take a break for a random duration.

        The bot will pause for the break duration, logging progress.

        Returns:
            Actual break duration in seconds

        Example:
            duration = self.behavior.breaks.take_break()
            self.bot.log_msg(f"Took {int(duration)}s break")
        """
        if not self.enabled:
            return 0.0

        # Generate break duration
        duration = rd.truncated_normal_sample(
            self.config.get("duration_min", 8.0),
            self.config.get("duration_max", 35.0),
            mean=self.config.get("duration_mean", 16.0),
            std=self.config.get("duration_std", 6.0),
        )

        duration_int = int(duration)
        self.bot.log_msg(f"Taking a short break ({duration_int}s)...")

        # Sleep for break duration with countdown
        import time

        for i in range(duration_int):
            self.bot.log_msg(
                f"Taking a break... {duration_int - i}s remaining", overwrite=True
            )
            time.sleep(1)

        self.bot.log_msg(f"Break complete ({duration_int}s)", overwrite=True)
        return duration

    def take_custom_break(
        self, min_seconds: float, max_seconds: float, message: str = "Taking a break"
    ) -> float:
        """
        Take a break with custom duration range.

        Args:
            min_seconds: Minimum break duration
            max_seconds: Maximum break duration
            message: Message to display during break

        Returns:
            Actual break duration in seconds

        Example:
            # Long break
            self.behavior.breaks.take_custom_break(60, 180, "Taking lunch break")
        """
        if not self.enabled:
            return 0.0

        duration = rd.truncated_normal_sample(min_seconds, max_seconds)
        duration_int = int(duration)

        self.bot.log_msg(f"{message} ({duration_int}s)...")

        import time

        for i in range(duration_int):
            self.bot.log_msg(
                f"{message}... {duration_int - i}s remaining", overwrite=True
            )
            time.sleep(1)

        self.bot.log_msg(f"{message} complete ({duration_int}s)", overwrite=True)
        return duration
