"""
ActionWaitingMixin - Shared action waiting operations for OSRS bots.

Provides common action detection/waiting functionality:
- Wait for action to start (e.g., "Cooking", "Cutting")
- Wait for action to end
- Check if performing an action

Uses BotSessionState and ActionWatcher for background monitoring.

Extracted from cooking/crafting bots to eliminate duplication.
"""

import time
from typing import TYPE_CHECKING

from model.bot import BotStatus

if TYPE_CHECKING:
    from utilities.behavior import BehaviorManager


class ActionWaitingMixin:
    """
    Mixin providing shared action waiting operations.

    This mixin expects to be mixed into a bot class that provides:
    - self.behavior: BehaviorManager
    - self.status: BotStatus
    - self.log_msg()
    """

    # Type hints for attributes/methods provided by the bot class
    if TYPE_CHECKING:
        behavior: "BehaviorManager"
        status: BotStatus

        def log_msg(self, msg: str, overwrite: bool = False) -> None: ...


import time
from typing import Optional

from model.bot import BotStatus


class ActionWaitingMixin:
    """
    Mixin providing shared action state detection.

    Uses the background ActionWatcher (via BotSessionState) for efficient
    action text detection without per-cycle OCR overhead.

    Requires the following from the bot class:
    - self.behavior (BehaviorManager instance)
    - self.log_msg() method
    - self.status (BotStatus)
    """

    def wait_for_action_start(
        self, action_name: str, timeout_seconds: float = 4.0
    ) -> bool:
        """
        Wait for a specific action to start.

        Uses background ActionWatcher to detect action text (e.g., "Cooking", "Cutting").

        Args:
            action_name: Expected action text (e.g., "Cooking", "Cutting", "Attaching")
            timeout_seconds: Maximum time to wait in seconds

        Returns:
            True if action started, False if timeout
        """
        from model.bot_session_state import BotSessionState

        start = time.time()
        while time.time() - start < timeout_seconds:
            if self.status != BotStatus.RUNNING:
                return False

            # Read current action from background watcher's state
            current_action = BotSessionState().get_current_action()
            if current_action == action_name:
                self.log_msg(
                    f"[WATCHER] {action_name} started (detected by background watcher)"
                )
                return True

            # Poll delay
            self.behavior.timing.sleep((0.08, 0.18))

        return False

    def wait_for_action_end(
        self, action_name: str, timeout_seconds: float = 60.0, log_interval: float = 6.0
    ) -> bool:
        """
        Wait for a specific action to end.

        Uses background ActionWatcher to detect when action text disappears.
        Logs periodic progress updates and XP gains.

        Args:
            action_name: Expected action text (e.g., "Cooking", "Cutting", "Attaching")
            timeout_seconds: Maximum time to wait in seconds
            log_interval: Seconds between progress log messages

        Returns:
            True if action ended, False if timeout
        """
        from model.bot_session_state import BotSessionState
        from model.skills import SkillsManager

        start = time.time()
        last_log = 0.0

        while time.time() - start < timeout_seconds:
            if self.status != BotStatus.RUNNING:
                return False

            # Read current action from background watcher's state
            current_action = BotSessionState().get_current_action()
            if current_action != action_name:
                self.log_msg(
                    f"[WATCHER] {action_name} completed (detected by background watcher)"
                )
                return True

            # Periodic progress logging
            if time.time() - last_log > log_interval:
                self.log_msg(f"{action_name}... waiting for completion.")

                # Check if XP was gained (updated by background XP watcher)
                if hasattr(self, "primary_skill") and self.primary_skill:
                    skill = SkillsManager().get_skill(self.primary_skill.capitalize())
                    if skill and skill.xp_gained > 0:
                        self.log_msg(
                            f"[WATCHER] XP gained: {skill.xp_gained} (total: {skill.xp})"
                        )

                last_log = time.time()

            # Poll delay
            self.behavior.timing.sleep((0.2, 0.6))

        self.log_msg(f"{action_name} wait timed out; retrying cycle.")
        return False

    def is_performing_action(self, action_name: str) -> bool:
        """
        Check if bot is currently performing a specific action.

        Args:
            action_name: Action text to check for

        Returns:
            True if currently performing action, False otherwise
        """
        from model.bot_session_state import BotSessionState

        current_action = BotSessionState().get_current_action()
        return current_action == action_name
