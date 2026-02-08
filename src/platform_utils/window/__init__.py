"""
Platform-specific window abstraction.

This module provides a unified interface for window operations across
different platforms, using native APIs where available for best performance.

Usage:
    from platform_utils.window import create_window
    
    window = create_window("RuneLite")
    if not window.is_active():
        window.activate()
    rect = window.get_rect()
"""
from typing import Union
from ..detection import get_platform
from .types import Rect
from .protocol import WindowBackend
from .pywinctl_backend import PyWinCtlBackend

# Import AppKit backend only on macOS
if get_platform() == "darwin":
    try:
        from .appkit_backend import AppKitBackend
        APPKIT_AVAILABLE = True
    except ImportError:
        APPKIT_AVAILABLE = False
else:
    APPKIT_AVAILABLE = False


class PlatformWindow:
    """
    Platform-agnostic window wrapper.
    
    This class provides a consistent API across platforms while using
    the most efficient backend for each platform.
    """

    def __init__(self, backend: WindowBackend):
        """
        Initialize with a backend implementation.
        
        Args:
            backend: Platform-specific backend instance
        """
        self._backend = backend

    def get_rect(self) -> Rect:
        """Get window rectangle (position and size)."""
        return self._backend.get_rect()

    def is_active(self) -> bool:
        """Check if window is currently focused/active."""
        return self._backend.is_active()

    def activate(self) -> None:
        """Bring window to front and focus it."""
        self._backend.activate()

    def is_minimized(self) -> bool:
        """Check if window is minimized."""
        return self._backend.is_minimized()

    def restore(self) -> None:
        """Restore window if minimized."""
        self._backend.restore()

    @property
    def title(self) -> str:
        """Get window title."""
        return self._backend.title

    # Compatibility properties for existing code
    @property
    def box(self) -> Rect:
        """Alias for get_rect() for pywinctl compatibility."""
        return self.get_rect()

    @property
    def isActive(self) -> bool:
        """Alias for is_active() for pywinctl compatibility."""
        return self.is_active()

    @property
    def isMinimized(self) -> bool:
        """Alias for is_minimized() for pywinctl compatibility."""
        return self.is_minimized()


def create_window(window_title: str, force_backend: str = None) -> PlatformWindow:
    """
    Create a platform-appropriate window instance.
    
    Args:
        window_title: Title of the window to control
        force_backend: Force a specific backend ('appkit', 'pywinctl') for testing
        
    Returns:
        PlatformWindow instance using the best available backend
        
    Raises:
        ImportError: If required backend dependencies are missing
    """
    platform = get_platform()
    
    # Determine which backend to use
    use_appkit = False
    if force_backend == "appkit":
        use_appkit = True
    elif force_backend == "pywinctl":
        use_appkit = False
    elif platform == "darwin" and APPKIT_AVAILABLE:
        use_appkit = True

    # Create appropriate backend
    if use_appkit:
        backend = AppKitBackend(window_title)
    else:
        backend = PyWinCtlBackend(window_title)

    return PlatformWindow(backend)


__all__ = [
    "PlatformWindow",
    "create_window",
    "Rect",
    "WindowBackend",
]
