"""Timing behavior module for sleep patterns and delays."""

import time
from typing import Dict, Any, Union, Tuple, Optional

import utilities.random_util as rd
from utilities.behavior.base import BaseBehaviorModule


class TimingBehavior(BaseBehaviorModule):
    """
    Handles all timing-related behaviors.

    Provides human-like delays, sleep patterns, and reaction times with
    configurable speed multipliers and preset durations.

    Example:
        # Use preset
        self.behavior.timing.sleep("short")

        # Use custom range
        self.behavior.timing.sleep((0.2, 0.6))

        # Use fixed duration
        self.behavior.timing.sleep(0.5)

        # Simulate reaction time
        self.behavior.timing.reaction_delay()
    """

    # Preset sleep durations (min, max) in seconds
    PRESETS = {
        "instant": (0.01, 0.03),
        "very_fast": (0.02, 0.08),
        "fast": (0.05, 0.15),
        "short": (0.1, 0.4),
        "medium": (0.3, 0.8),
        "long": (0.6, 1.5),
        "very_long": (1.5, 3.5),
    }

    def get_default_config(self) -> Dict[str, Any]:
        """Return default timing configuration."""
        return {
            "speed_multiplier": 1.0,
            "reaction_min": 0.15,
            "reaction_max": 0.45,
            "reaction_mean": None,  # Auto-calculate from min/max
            "reaction_std": None,  # Auto-calculate from min/max
        }

    def sleep(
        self,
        duration: Union[str, Tuple[float, float], float],
        mean: Optional[float] = None,
        std: Optional[float] = None,
    ) -> float:
        """
        Sleep for a variable duration with human-like randomness.

        Args:
            duration: Either:
                - Preset name: "instant", "very_fast", "fast", "short", "medium", "long", "very_long"
                - Tuple of (min, max) in seconds
                - Fixed float in seconds (no randomization)
            mean: Optional mean for the distribution (default: midpoint)
            std: Optional standard deviation (default: auto-calculated)

        Returns:
            Actual sleep duration in seconds

        Example:
            # Preset
            self.behavior.timing.sleep("short")  # 0.1-0.4s

            # Custom range
            self.behavior.timing.sleep((0.5, 1.2))

            # Custom range with mean
            self.behavior.timing.sleep((0.2, 0.8), mean=0.4)

            # Fixed duration
            self.behavior.timing.sleep(0.5)  # Exactly 0.5s
        """
        if not self.enabled:
            return 0.0

        # Handle different duration types
        if isinstance(duration, str):
            if duration not in self.PRESETS:
                raise ValueError(
                    f"Unknown preset '{duration}'. "
                    f"Valid presets: {', '.join(self.PRESETS.keys())}"
                )
            min_s, max_s = self.PRESETS[duration]
        elif isinstance(duration, (tuple, list)):
            min_s, max_s = duration
        else:
            # Fixed duration, no randomization
            time.sleep(duration)
            return duration

        # Apply speed multiplier from profile
        multiplier = self.config.get("speed_multiplier", 1.0)
        min_s *= multiplier
        max_s *= multiplier

        # Generate random sleep duration
        delay = rd.truncated_normal_sample(min_s, max_s, mean=mean, std=std)
        time.sleep(delay)
        return delay

    def reaction_delay(self) -> float:
        """
        Simulate human reaction time.

        This is the delay between seeing something and reacting to it
        (e.g., between a tree falling and clicking the next tree).

        Returns:
            Actual delay in seconds

        Example:
            # Wait for human reaction time before acting
            self.behavior.timing.reaction_delay()
            self.mouse.click()
        """
        if not self.enabled:
            return 0.0

        min_s = self.config.get("reaction_min", 0.15)
        max_s = self.config.get("reaction_max", 0.45)
        mean = self.config.get("reaction_mean")
        std = self.config.get("reaction_std")

        delay = rd.truncated_normal_sample(min_s, max_s, mean=mean, std=std)
        time.sleep(delay)
        return delay

    def micro_delay(self) -> float:
        """
        Very short delay for micro-actions (between rapid clicks, etc.).

        Returns:
            Actual delay in seconds

        Example:
            for slot in slots:
                self.mouse.move_to(slot)
                self.behavior.timing.micro_delay()
                self.mouse.click()
        """
        return self.sleep("very_fast")

    def thinking_pause(self) -> float:
        """
        Simulate a "thinking" pause - brief hesitation while deciding.

        Returns:
            Actual delay in seconds

        Example:
            # Pause before making decision
            self.behavior.timing.thinking_pause()
            if should_continue:
                self.do_action()
        """
        return self.sleep((0.4, 1.6), mean=0.9, std=0.3)

    def get_preset_range(self, preset: str) -> Tuple[float, float]:
        """
        Get the min/max range for a preset, adjusted by speed multiplier.

        Args:
            preset: Preset name

        Returns:
            Tuple of (min, max) in seconds
        """
        if preset not in self.PRESETS:
            raise ValueError(f"Unknown preset '{preset}'")

        min_s, max_s = self.PRESETS[preset]
        multiplier = self.config.get("speed_multiplier", 1.0)
        return (min_s * multiplier, max_s * multiplier)
