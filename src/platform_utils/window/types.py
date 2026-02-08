"""
Shared types for window abstraction.
"""
from dataclasses import dataclass


@dataclass
class Rect:
    """Window rectangle with position and size."""
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height
