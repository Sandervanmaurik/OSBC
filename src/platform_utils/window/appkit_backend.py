"""
AppKit/Quartz-based window backend for macOS.

This backend uses native macOS APIs for much faster window operations
compared to pywinctl (~50ms vs ~1500ms).
"""
from typing import Optional
import time

try:
    from Cocoa import NSWorkspace
    from AppKit import NSApplicationActivateIgnoringOtherApps
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID,
        kCGWindowOwnerName,
        kCGWindowName,
        kCGWindowNumber,
        kCGWindowBounds,
        kCGWindowLayer,
    )
    APPKIT_AVAILABLE = True
except ImportError:
    APPKIT_AVAILABLE = False

from .types import Rect


class AppKitBackend:
    """Window backend using native macOS AppKit/Quartz APIs."""

    def __init__(self, window_title: str):
        """
        Initialize backend with window title.
        
        Args:
            window_title: Title of the window to control
            
        Raises:
            ImportError: If pyobjc is not installed
        """
        if not APPKIT_AVAILABLE:
            raise ImportError(
                "pyobjc-framework-Cocoa and pyobjc-framework-Quartz required for macOS. "
                "Install with: pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz"
            )
        
        self._window_title = window_title
        self._cached_window_info: Optional[dict] = None
        self._cache_time: float = 0
        self._cache_ttl: float = 0.5  # Cache window info for 500ms

    def _get_window_info(self, use_cache: bool = True) -> Optional[dict]:
        """
        Get window info from Quartz window list.
        
        Args:
            use_cache: Whether to use cached window info if available
            
        Returns:
            Window info dict or None if not found
        """
        # Return cached info if still valid
        if use_cache and self._cached_window_info:
            age = time.time() - self._cache_time
            if age < self._cache_ttl:
                return self._cached_window_info

        # Get all on-screen windows
        window_list = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )

        # Find window by matching title
        for window in window_list:
            # Try both window name and owner name
            window_name = window.get(kCGWindowName, "")
            owner_name = window.get(kCGWindowOwnerName, "")
            
            # Match if title is in window name or owner name
            if self._window_title in window_name or self._window_title in owner_name:
                self._cached_window_info = window
                self._cache_time = time.time()
                return window

        # Not found
        self._cached_window_info = None
        return None

    def _get_app_for_window(self) -> Optional[object]:
        """Get NSRunningApplication for the window's owner."""
        window_info = self._get_window_info()
        if not window_info:
            return None

        owner_name = window_info.get(kCGWindowOwnerName, "")
        workspace = NSWorkspace.sharedWorkspace()
        
        # Find running application by name
        for app in workspace.runningApplications():
            if app.localizedName() == owner_name:
                return app
        
        return None

    def get_rect(self) -> Rect:
        """Get window rectangle."""
        window_info = self._get_window_info(use_cache=False)
        if not window_info:
            raise RuntimeError(f"Window '{self._window_title}' not found")

        bounds = window_info[kCGWindowBounds]
        return Rect(
            left=int(bounds['X']),
            top=int(bounds['Y']),
            width=int(bounds['Width']),
            height=int(bounds['Height'])
        )

    def is_active(self) -> bool:
        """Check if window is active."""
        app = self._get_app_for_window()
        if not app:
            return False
        return app.isActive()

    def activate(self) -> None:
        """Activate window."""
        app = self._get_app_for_window()
        if not app:
            raise RuntimeError(f"Window '{self._window_title}' not found")
        
        # Activate with options to bring all windows forward
        app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

    def is_minimized(self) -> bool:
        """
        Check if window is minimized.
        
        Note: This is approximate on macOS. We check if the window
        is in the window list (visible). Minimized windows typically
        have a layer value < 0.
        """
        window_info = self._get_window_info()
        if not window_info:
            return True  # Not visible = minimized
        
        # Check window layer (minimized windows have negative layer)
        layer = window_info.get(kCGWindowLayer, 0)
        return layer < 0

    def restore(self) -> None:
        """
        Restore window if minimized.
        
        Note: On macOS, activating the app typically restores minimized windows.
        """
        self.activate()

    @property
    def title(self) -> str:
        """Get window title."""
        return self._window_title
