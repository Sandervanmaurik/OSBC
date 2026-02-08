"""
Protocol definition for window backend implementations.
"""
from typing import Protocol, Optional
from .types import Rect


class WindowBackend(Protocol):
    """Protocol that all window backend implementations must follow."""

    def get_rect(self) -> Rect:
        """Get window rectangle (position and size)."""
        ...

    def is_active(self) -> bool:
        """Check if window is currently focused/active."""
        ...

    def activate(self) -> None:
        """Bring window to front and focus it."""
        ...

    def is_minimized(self) -> bool:
        """Check if window is minimized."""
        ...

    def restore(self) -> None:
        """Restore window if minimized."""
        ...

    @property
    def title(self) -> str:
        """Get window title."""
        ...
