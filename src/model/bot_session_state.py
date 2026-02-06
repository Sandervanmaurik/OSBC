"""
Simple session state singleton for tracking bot activity.
Provides observer pattern for UI updates.
"""

from typing import Callable, Dict, List, Optional


class BotSessionState:
    """
    Tracks current session state with observer notifications.

    This is a singleton that stores:
    - Current action being performed ("Attaching", "Cutting", etc.)
    - Starting XP values for each skill (first XP detected in current script run)
    - Session starting XP values (first XP detected since app opened, persists across script runs)
    - Observer callbacks for UI updates

    Usage:
        # Get singleton instance
        state = BotSessionState()

        # Update action (notifies observers)
        state.set_action("Cutting")

        # Record starting XP (first time only)
        state.record_starting_xp("crafting", 1000)

        # Get XP gained (current script run)
        xp_gained = state.get_xp_gained("crafting")

        # Get XP gained (since app opened)
        session_xp = state.get_session_xp_gained("crafting")

        # Subscribe to changes
        state.add_observer(my_callback)
    """

    _instance: Optional["BotSessionState"] = None

    # Instance attributes with type annotations
    current_action: Optional[str]
    _starting_xp: Dict[str, int]
    _session_starting_xp: Dict[str, int]
    _observers: List[Callable[[], None]]

    def __new__(cls):
        """Singleton pattern - only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize state on first creation
            cls._instance.current_action = None
            cls._instance._starting_xp = {}
            cls._instance._session_starting_xp = {}  # Session-level, persists across script runs
            cls._instance._observers = []
        return cls._instance

    def set_action(self, action: Optional[str]) -> None:
        """
        Update current action, notify observers if changed.

        Args:
            action: Action name ("Attaching", "Cutting") or None for idle
        """
        if self.current_action != action:
            self.current_action = action
            self.notify_observers()

    def get_current_action(self) -> Optional[str]:
        """
        Get current action.

        Returns:
            Current action name or None if idle
        """
        return self.current_action

    def record_starting_xp(self, skill: str, xp: int) -> None:
        """
        Record starting XP (only first time per skill).
        Also records session starting XP if this is the first time seeing this skill in the app session.

        Args:
            skill: Skill name (e.g., "crafting", "fletching")
            xp: XP amount to record as starting value
        """
        skill_lower = skill.lower()
        if skill_lower not in self._starting_xp:
            self._starting_xp[skill_lower] = xp
            self.notify_observers()

        # Also record session-level starting XP (first time only across all script runs)
        if skill_lower not in self._session_starting_xp:
            self._session_starting_xp[skill_lower] = xp
            self.notify_observers()

    def get_xp_gained(self, skill: str) -> int:
        """
        Get XP gained for a skill (current - starting).

        Args:
            skill: Skill name

        Returns:
            XP gained since session start (0 if no starting XP recorded)
        """
        from model.skills import SkillsManager

        skill_lower = skill.lower()
        current_xp = SkillsManager().get_skill(skill).xp
        starting_xp = self._starting_xp.get(skill_lower, current_xp)
        return max(0, current_xp - starting_xp)

    def get_total_xp_gained(self) -> int:
        """
        Get total XP gained across all tracked skills (current script run).

        Returns:
            Sum of XP gained for all skills with recorded starting XP
        """
        return sum(self.get_xp_gained(skill) for skill in self._starting_xp)

    def get_session_xp_gained(self, skill: str) -> int:
        """
        Get XP gained for a skill since the app opened (session-level).

        Args:
            skill: Skill name

        Returns:
            XP gained since app opened (0 if no session starting XP recorded)
        """
        from model.skills import SkillsManager

        skill_lower = skill.lower()
        current_xp = SkillsManager().get_skill(skill).xp
        session_starting_xp = self._session_starting_xp.get(skill_lower, current_xp)
        return max(0, current_xp - session_starting_xp)

    def get_total_session_xp_gained(self) -> int:
        """
        Get total XP gained across all tracked skills since app opened (session-level).

        Returns:
            Sum of session XP gained for all skills
        """
        return sum(
            self.get_session_xp_gained(skill) for skill in self._session_starting_xp
        )

    def add_observer(self, callback: Callable[[], None]) -> None:
        """
        Add observer callback to be notified on state changes.

        Args:
            callback: Function to call when state changes (no arguments)
        """
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback: Callable[[], None]) -> None:
        """
        Remove observer callback.

        Args:
            callback: Previously registered callback to remove
        """
        if callback in self._observers:
            self._observers.remove(callback)

    def notify_observers(self) -> None:
        """Notify all observers of state change."""
        for callback in self._observers:
            try:
                callback()
            except Exception as e:
                print(f"[BotSessionState] Observer error: {e}")

    def reset(self) -> None:
        """Reset state for new session."""
        self.current_action = None
        self._starting_xp.clear()
        self.notify_observers()

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        cls._instance = None
