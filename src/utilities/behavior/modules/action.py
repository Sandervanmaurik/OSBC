"""Action behavior module for execution patterns."""

import random
from typing import Dict, Any, Union, Tuple

import utilities.random_util as rd
from utilities.behavior.base import BaseBehaviorModule
from utilities.geometry import Point


class ActionBehavior(BaseBehaviorModule):
    """
    Handles action execution patterns like misclicks and hesitation.

    Provides realistic human errors and decision-making delays to make
    bot actions appear more natural.

    Example:
        # Check if should misclick before clicking
        if self.behavior.action.should_misclick():
            self.behavior.action.execute_misclick(target)
        else:
            self.behavior.mouse.move_to(target)
            self.behavior.mouse.click()

        # Add hesitation before important action
        if self.behavior.action.should_hesitate():
            self.behavior.action.hesitate()
    """

    def get_default_config(self) -> Dict[str, Any]:
        """Return default action configuration."""
        return {
            "misclick_chance": 0.08,
            "misclick_distance": (-12, 12),
            "hesitation_chance": 0.15,
            "hesitation_duration": (0.2, 0.7),
            "pre_click_delay_chance": 0.3,
            "pre_click_delay": (0.05, 0.2),
        }

    def should_misclick(self) -> bool:
        """
        Determine if a misclick should occur.

        Returns:
            True if action should misclick

        Example:
            if self.behavior.action.should_misclick():
                self.behavior.action.execute_misclick(target)
            else:
                self.normal_click(target)
        """
        if not self.enabled:
            return False

        return rd.random_chance(self.config.get("misclick_chance", 0.08))

    def execute_misclick(
        self, target: Union[Point, Tuple[int, int]], correct_after: bool = True
    ) -> None:
        """
        Perform a realistic misclick near the target.

        Clicks slightly off-target, then optionally corrects to the actual
        target and clicks again.

        Args:
            target: Intended click target (Point or (x, y) tuple)
            correct_after: Whether to correct and click actual target after misclick

        Example:
            # Misclick and correct
            self.behavior.action.execute_misclick(target)

            # Just misclick without correction
            self.behavior.action.execute_misclick(target, correct_after=False)
        """
        if not self.enabled:
            return

        # Convert to Point if tuple
        if isinstance(target, tuple):
            target = Point(target[0], target[1])

        # Calculate miss point
        miss_range = self.config.get("misclick_distance", (-12, 12))
        offset_x = random.randint(miss_range[0], miss_range[1])
        offset_y = random.randint(miss_range[0], miss_range[1])
        miss_point = Point(target.x + offset_x, target.y + offset_y)

        # Execute misclick
        self.bot.behavior.mouse.move_to(miss_point, mouseSpeed="fast")
        self.bot.behavior.mouse.click()

        if correct_after:
            # Pause as if realizing the mistake
            self.bot.behavior.timing.sleep("short")

            # Correct to actual target
            self.bot.behavior.mouse.move_to(
                target, mouseSpeed=random.choice(["medium", "fast"])
            )
            self.bot.behavior.mouse.click()

    def should_hesitate(self) -> bool:
        """
        Determine if hesitation should occur before an action.

        Returns:
            True if should hesitate

        Example:
            if self.behavior.action.should_hesitate():
                self.behavior.action.hesitate()
            self.perform_action()
        """
        if not self.enabled:
            return False

        return rd.random_chance(self.config.get("hesitation_chance", 0.15))

    def hesitate(self) -> float:
        """
        Brief pause simulating uncertainty or decision-making.

        Returns:
            Actual hesitation duration in seconds

        Example:
            # Hesitate before clicking
            self.behavior.action.hesitate()
            self.mouse.click()
        """
        if not self.enabled:
            return 0.0

        duration = self.config.get("hesitation_duration", (0.2, 0.7))
        return self.bot.behavior.timing.sleep(duration)

    def pre_click_delay(self) -> float:
        """
        Small delay before clicking (hover time).

        Simulates the brief moment humans hover over something before clicking.
        Only occurs sometimes based on configuration.

        Returns:
            Actual delay in seconds (0 if no delay)

        Example:
            self.behavior.mouse.move_to(target)
            self.behavior.action.pre_click_delay()
            self.behavior.mouse.click()
        """
        if not self.enabled:
            return 0.0

        if rd.random_chance(self.config.get("pre_click_delay_chance", 0.3)):
            duration = self.config.get("pre_click_delay", (0.05, 0.2))
            return self.bot.behavior.timing.sleep(duration)
        return 0.0

    def execute_click_sequence(
        self,
        target: Union[Point, Tuple[int, int]],
        check_mouseover: bool = False,
        mouseover_check_fn: callable = None,
        **move_kwargs,
    ) -> bool:
        """
        Execute a complete click sequence with realistic human behavior.

        This is a high-level method that combines movement, potential misclick,
        hesitation, and clicking into a single realistic action.

        Args:
            target: Target to click
            check_mouseover: Whether to verify mouseover text before clicking
            mouseover_check_fn: Function that returns True if mouseover is correct
            **move_kwargs: Additional arguments for mouse movement

        Returns:
            True if click was executed, False if cancelled (e.g., wrong mouseover)

        Example:
            # Simple click
            self.behavior.action.execute_click_sequence(target)

            # With mouseover check
            def check_chop():
                return self.bot.mouseover_text(contains="Chop")

            self.behavior.action.execute_click_sequence(
                target,
                check_mouseover=True,
                mouseover_check_fn=check_chop
            )
        """
        if not self.enabled:
            # Fallback to basic click
            self.bot.behavior.mouse.move_to(target, **move_kwargs)
            self.bot.behavior.mouse.click()
            return True

        # Convert to Point if needed
        if isinstance(target, tuple):
            target = Point(target[0], target[1])

        # Chance to misclick
        if self.should_misclick():
            self.execute_misclick(target)
            return True

        # Normal movement
        self.bot.behavior.mouse.move_to(target, **move_kwargs)

        # Pre-click delay (hover time)
        self.pre_click_delay()

        # Check mouseover if required
        if check_mouseover and mouseover_check_fn:
            if not mouseover_check_fn():
                # Wrong target, don't click
                return False

        # Optional hesitation
        if self.should_hesitate():
            self.hesitate()

        # Execute click
        self.bot.behavior.mouse.click()
        return True
