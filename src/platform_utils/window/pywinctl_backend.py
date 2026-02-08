"""
PyWinCtl-based window backend for Windows and Linux.
"""
import pywinctl
from typing import Optional
from .types import Rect


class PyWinCtlBackend:
    """Window backend using pywinctl library (Windows/Linux)."""

    def __init__(self, window_title: str):
        """
        Initialize backend with window title.
        
        Args:
            window_title: Title of the window to control
        """
        self._window_title = window_title
        self._window: Optional[pywinctl.Window] = None
        self._refresh_window()

    def _refresh_window(self) -> None:
        """Refresh the window reference by searching for it."""
        windows = pywinctl.getWindowsWithTitle(self._window_title)
        self._window = windows[0] if windows else None

    def get_rect(self) -> Rect:
        """Get window rectangle."""
        self._refresh_window()
        if not self._window:
            raise RuntimeError(f"Window '{self._window_title}' not found")
        
        box = self._window.box
        return Rect(
            left=box.left,
            top=box.top,
            width=box.width,
            height=box.height
        )

    def is_active(self) -> bool:
        """Check if window is active."""
        self._refresh_window()
        if not self._window:
            return False
        return self._window.isActive

    def activate(self) -> None:
        """Activate window."""
        self._refresh_window()
        if not self._window:
            raise RuntimeError(f"Window '{self._window_title}' not found")
        self._window.activate()

    def is_minimized(self) -> bool:
        """Check if window is minimized."""
        self._refresh_window()
        if not self._window:
            return False
        return self._window.isMinimized

    def restore(self) -> None:
        """Restore window."""
        self._refresh_window()
        if not self._window:
            raise RuntimeError(f"Window '{self._window_title}' not found")
        self._window.restore()

    @property
    def title(self) -> str:
        """Get window title."""
        return self._window_title
