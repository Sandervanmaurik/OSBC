"""Mouse behavior module for movement patterns."""

import random
from typing import Dict, Any, Optional, Tuple, Union

from utilities.behavior.base import BaseBehaviorModule
from utilities.geometry import Point


class MouseBehavior(BaseBehaviorModule):
    """
    Handles mouse movement behaviors.

    Provides profile-aware mouse movements with configurable speeds,
    overshoot behaviors, and movement patterns.

    Example:
        # Move with profile default speed
        self.behavior.mouse.move_to(target)

        # Override speed for this move
        self.behavior.mouse.move_to(target, mouseSpeed="slow")

        # Click at current position
        self.behavior.mouse.click()

        # Right-click
        self.behavior.mouse.right_click()
    """

    def get_default_config(self) -> Dict[str, Any]:
        """Return default mouse configuration."""
        return {
            "default_speed": "fast",
            "default_knots": None,  # Auto-calculate based on distance
            "overshoot_chance": 0.05,
            "overshoot_distance": (5, 15),
        }

    def move_to(
        self,
        destination: Union[Point, Tuple[int, int]],
        mouseSpeed: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Move mouse to destination with profile-aware settings.

        Args:
            destination: Target point (Point object or (x, y) tuple)
            mouseSpeed: Speed override ("slowest", "slow", "medium", "fast", "fastest")
                       If None, uses profile default
            **kwargs: Additional overrides (knotsCount, offsetBoundaryX, etc.)

        Example:
            # Use profile default speed
            self.behavior.mouse.move_to(target.random_point())

            # Override speed
            self.behavior.mouse.move_to(target, mouseSpeed="slow")

            # Override knots for smoother movement
            self.behavior.mouse.move_to(target, knotsCount=0)
        """
        if not self.enabled:
            return

        # Convert to tuple if Point object
        if isinstance(destination, Point):
            destination = (destination.x, destination.y)

        # Merge profile defaults with overrides
        move_kwargs = {
            "mouseSpeed": mouseSpeed or self.config.get("default_speed", "fast"),
        }

        # Add optional default knots if configured
        if "knotsCount" not in kwargs and self.config.get("default_knots") is not None:
            move_kwargs["knotsCount"] = self.config.get("default_knots")

        # Merge with any additional overrides
        move_kwargs.update(kwargs)

        # Use bot's mouse
        self.bot.mouse.move_to(destination, **move_kwargs)

    def move_rel(
        self, x: int, y: int, x_var: int = 0, y_var: int = 0, **kwargs
    ) -> None:
        """
        Move mouse relatively with profile-aware settings.

        Args:
            x: Pixels to move horizontally
            y: Pixels to move vertically
            x_var: Max random variance in x direction
            y_var: Max random variance in y direction
            **kwargs: Additional overrides for move_to

        Example:
            # Move down 50 pixels
            self.behavior.mouse.move_rel(0, 50)

            # Move with variance
            self.behavior.mouse.move_rel(10, 20, x_var=3, y_var=3)
        """
        if not self.enabled:
            return

        self.bot.mouse.move_rel(x, y, x_var, y_var, **kwargs)

    def click(self, button: str = "left", force_delay: bool = False, **kwargs) -> None:
        """
        Click at current mouse position.

        Args:
            button: Mouse button ("left" or "right")
            force_delay: Force delay between mouse down and up
            **kwargs: Additional arguments passed to mouse.click

        Example:
            self.behavior.mouse.move_to(target)
            self.behavior.mouse.click()
        """
        if not self.enabled:
            return

        self.bot.mouse.click(button=button, force_delay=force_delay, **kwargs)

    def right_click(self, force_delay: bool = False) -> None:
        """
        Right-click at current mouse position.

        Args:
            force_delay: Force delay between mouse down and up

        Example:
            self.behavior.mouse.move_to(target)
            self.behavior.mouse.right_click()
        """
        if not self.enabled:
            return

        self.bot.mouse.right_click(force_delay=force_delay)

    def should_overshoot(self) -> bool:
        """
        Determine if mouse should overshoot target.

        Returns:
            True if overshoot should occur
        """
        import utilities.random_util as rd

        return rd.random_chance(self.config.get("overshoot_chance", 0.05))

    def move_with_overshoot(
        self, destination: Union[Point, Tuple[int, int]], **kwargs
    ) -> None:
        """
        Move to destination with possible overshoot correction.

        Occasionally overshoots the target and then corrects back, simulating
        human imprecision.

        Args:
            destination: Target point
            **kwargs: Additional arguments for move_to

        Example:
            # May overshoot and correct
            self.behavior.mouse.move_with_overshoot(target)
        """
        if not self.enabled:
            return

        if isinstance(destination, Point):
            dest_x, dest_y = destination.x, destination.y
        else:
            dest_x, dest_y = destination

        if self.should_overshoot():
            # Overshoot
            overshoot_range = self.config.get("overshoot_distance", (5, 15))
            overshoot_x = random.randint(*overshoot_range) * random.choice([-1, 1])
            overshoot_y = random.randint(*overshoot_range) * random.choice([-1, 1])

            overshoot_point = (dest_x + overshoot_x, dest_y + overshoot_y)
            self.move_to(overshoot_point, **kwargs)

            # Correct back to actual target
            self.bot.behavior.timing.sleep("very_fast")
            self.move_to((dest_x, dest_y), mouseSpeed="fastest")
        else:
            # Normal movement
            self.move_to((dest_x, dest_y), **kwargs)
