"""
ActionWatcher Service for Auto-OSBC

Monitors the action text area (top-left of game view) to detect current activity.
Simpler than XPWatcher - just tracks what action is being performed.

Usage:
    from utilities.action_watcher import ActionWatcher

    # Initialize watcher with window reference
    watcher = ActionWatcher(bot.win)

    # In bot main loop
    current_action = watcher.check()  # Returns "Attaching", "Cutting", or None

    # Check if specific action is active
    if watcher.check() == "Cutting":
        # Cutting in progress
"""

import time
from typing import Optional

import utilities.color as clr
import utilities.ocr as ocr
from utilities.geometry import Rectangle
from utilities.window import Window
from utilities.watcher_base import BackgroundWatcher


class ActionWatcher(BackgroundWatcher):
    """
    Watches the action text area for current activity.

    The action text appears in the top-left of the game view when performing activities.
    Format: "Attaching feathers to arrow shafts..." or "Cutting a gem..."
    """

    # Check interval (seconds) - how often to check for action text
    CHECK_INTERVAL = 0.5

    # Background polling interval (matches CHECK_INTERVAL)
    POLL_INTERVAL = 0.5

    # Known actions to detect (extensible - add more as needed)
    KNOWN_ACTIONS = ["Attaching", "Cutting", "Cooking", "Making", "Combining"]

    def __init__(self, window: Window):
        """
        Initialize the Action watcher.

        Args:
            window: Window instance with initialized game client
        """
        super().__init__(window)
        self._last_check_time = 0.0
        self._action_rect: Optional[Rectangle] = None

        # Calculate action detection area
        self._calculate_action_rect()

    def _calculate_action_rect(self) -> None:
        """
        Calculate the action text detection area based on game view.

        Action text appears in the top-left corner of the game view:
        - Width: ~320 pixels
        - Height: ~90 pixels
        """
        if not self.window or not self.window.game_view:
            return

        gv = self.window.game_view

        # Action text area configuration
        action_width = min(320, gv.width)
        action_height = min(90, gv.height)

        self._action_rect = Rectangle(
            left=gv.left, top=gv.top, width=action_width, height=action_height
        )

    def _poll(self) -> None:
        """
        Background poll implementation.

        Called automatically by the background thread at POLL_INTERVAL.
        Delegates to the existing check() method.
        """
        result = self.check()
        # Log every poll for debugging (will show polling is active)
        # print(f"[ActionWatcher] Poll cycle complete, current action: {result}")

    def check(self) -> Optional[str]:
        """
        Check the action area for current activity text.

        This method is throttled to CHECK_INTERVAL to reduce overhead.
        If called too frequently, returns the cached current action.

        Returns:
            Current action name ("Attaching", "Cutting") or None if idle
        """
        from model.bot_session_state import BotSessionState

        state = BotSessionState()

        # Throttle checks to reduce overhead
        current_time = time.time()
        if current_time - self._last_check_time < self.CHECK_INTERVAL:
            return state.current_action  # Return cached value

        self._last_check_time = current_time

        # Detect current action via OCR
        action = self._detect_action()

        # Update state (triggers observer notifications if changed)
        prev_action = state.current_action
        if action != prev_action:
            print(f"[ActionWatcher] Action changed: {prev_action} → {action}")

        state.set_action(action)

        return action

    def _detect_action(self) -> Optional[str]:
        """
        Detect action text via OCR.

        Searches for known action keywords in the action text area.

        Returns:
            Action name if detected, None otherwise
        """
        if not self._action_rect:
            return None

        # Text colors in action area
        colors = [clr.WHITE, clr.OFF_WHITE, clr.OFF_YELLOW]

        # Try different fonts
        for font in (ocr.BOLD_12, ocr.PLAIN_12):
            text = ocr.extract_text(self._action_rect, font, colors)
            if not text:
                continue

            # Check for known actions
            for action in self.KNOWN_ACTIONS:
                if action in text:
                    return action

        return None
