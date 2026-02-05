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
    - Starting XP values for each skill (first XP detected)
    - Observer callbacks for UI updates

    Usage:
        # Get singleton instance
        state = BotSessionState()

        # Update action (notifies observers)
        state.set_action("Cutting")

        # Record starting XP (first time only)
        state.record_starting_xp("crafting", 1000)

        # Get XP gained
        xp_gained = state.get_xp_gained("crafting")

        # Subscribe to changes
        state.add_observer(my_callback)
    """

    _instance: Optional["BotSessionState"] = None
    
    # Instance attributes with type annotations
    current_action: Optional[str]
    _starting_xp: Dict[str, int]
    _observers: List[Callable[[], None]]

    def __new__(cls):
        """Singleton pattern - only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize state on first creation
            cls._instance.current_action = None
            cls._instance._starting_xp = {}
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

    def record_starting_xp(self, skill: str, xp: int) -> None:
        """
        Record starting XP (only first time per skill).

        Args:
            skill: Skill name (e.g., "crafting", "fletching")
            xp: XP amount to record as starting value
        """
        skill_lower = skill.lower()
        if skill_lower not in self._starting_xp:
            self._starting_xp[skill_lower] = xp
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
        Get total XP gained across all tracked skills.

        Returns:
            Sum of XP gained for all skills with recorded starting XP
        """
        return sum(self.get_xp_gained(skill) for skill in self._starting_xp)

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
