"""Skills state management for OSRS bots.

This module provides a global singleton for tracking skill states across all bots.
Each skill has level, XP, XP gained, and timestamp tracking.

Usage:
    from model.skills import SkillsManager, ExperienceTable

    # Update a skill (from OCR or XP detection)
    SkillsManager().update_skill_level("fishing", 50)
    SkillsManager().update_skill_xp("fishing", 101333)

    # Get skill state
    skill = SkillsManager().get_skill("fishing")
    print(f"Level: {skill.level}, XP: {skill.xp}")

    # Get XP table info
    next_level_xp = ExperienceTable().xp_to_next_level(101333)
    progress = ExperienceTable().progress_to_next_level(101333)
"""

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from utilities.osrs_skills import SKILL_ORDER


@dataclass
class SkillState:
    """Represents the state of a single OSRS skill.

    Attributes:
        level: Current skill level (1-99)
        xp: Total experience points earned
        xp_gained: Experience gained since tracking started
        timestamp: When this skill was last updated
    """

    level: int
    xp: int = 0
    xp_gained: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def has_xp_data(self) -> bool:
        """Check if we have actual XP data (not just level from OCR).

        Returns:
            True if XP has been tracked, False if only level is known.
        """
        return self.xp > 0

    def update_timestamp(self) -> None:
        """Update the timestamp to current time."""
        self.timestamp = datetime.now()


class ExperienceTable:
    """Singleton for OSRS experience table lookups.

    Provides conversions between levels and XP, and progress calculations.
    Loads data from src/utilities/api/experience-table.csv on first access.
    """

    _instance: Optional["ExperienceTable"] = None

    def __init__(self):
        """Initialize the experience table. Use get_instance() instead."""
        # Only initialize if this is a new instance (not already initialized)
        if not hasattr(self, "_level_to_xp_map"):
            self._level_to_xp_map: Dict[int, int] = {}
            self._xp_to_level_map: List[tuple[int, int]] = []  # [(min_xp, level), ...]
            self._load_table()

    @classmethod
    def get_instance(cls) -> "ExperienceTable":
        """Get the singleton instance of ExperienceTable."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __new__(cls):
        """Singleton pattern: return existing instance if available."""
        if cls._instance is None:
            instance = super().__new__(cls)
            cls._instance = instance
            return instance
        return cls._instance

    def _load_table(self) -> None:
        """Load the experience table from CSV file."""
        csv_path = (
            Path(__file__).parent.parent / "utilities" / "api" / "experience-table.csv"
        )

        if not csv_path.exists():
            raise FileNotFoundError(f"Experience table not found at {csv_path}")

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                level = int(row["Level"])
                xp = int(row["Exp"])

                # Build lookup maps
                self._level_to_xp_map[level] = xp
                self._xp_to_level_map.append((xp, level))

        # Sort XP to level map for binary search
        self._xp_to_level_map.sort(key=lambda x: x[0])

    def level_to_xp(self, level: int) -> int:
        """Get the minimum XP required for a level.

        Args:
            level: The level (1-99)

        Returns:
            Minimum XP required for that level

        Raises:
            ValueError: If level is out of bounds (1-99)
        """
        if level < 1 or level > 99:
            raise ValueError(f"Level must be between 1 and 99, got {level}")
        return self._level_to_xp_map[level]

    def xp_to_level(self, xp: int) -> int:
        """Get the level corresponding to an XP amount.

        Args:
            xp: Total experience points

        Returns:
            Current level for that XP amount
        """
        if xp < 0:
            return 1

        # Binary search through sorted XP thresholds
        level = 1
        for threshold_xp, threshold_level in self._xp_to_level_map:
            if xp >= threshold_xp:
                level = threshold_level
            else:
                break

        return min(level, 99)  # Cap at 99

    def xp_to_next_level(self, current_xp: int) -> int:
        """Get the XP required for the next level.

        Args:
            current_xp: Current total XP

        Returns:
            XP threshold for next level, or current XP if already level 99
        """
        current_level = self.xp_to_level(current_xp)

        # Already max level
        if current_level >= 99:
            return self._level_to_xp_map[99]

        return self._level_to_xp_map[current_level + 1]

    def progress_to_next_level(self, current_xp: int) -> float:
        """Calculate progress to next level as a percentage.

        Args:
            current_xp: Current total XP

        Returns:
            Progress from 0.0 to 1.0 (0% to 100%)
        """
        current_level = self.xp_to_level(current_xp)

        # Already max level
        if current_level >= 99:
            return 1.0

        current_level_xp = self._level_to_xp_map[current_level]
        next_level_xp = self._level_to_xp_map[current_level + 1]

        xp_into_level = current_xp - current_level_xp
        xp_needed_for_level = next_level_xp - current_level_xp

        if xp_needed_for_level == 0:
            return 1.0

        progress = xp_into_level / xp_needed_for_level
        return max(0.0, min(1.0, progress))  # Clamp to [0, 1]


class SkillsManager:
    """Singleton manager for all OSRS skill states.

    Maintains a global state of all 24 skills with level, XP, and tracking data.
    Implements observer pattern to notify UI when skills are updated.
    """

    _instance: Optional["SkillsManager"] = None

    def __init__(self):
        """Initialize the skills manager. Use get_instance() instead."""
        # Only initialize if this is a new instance (not already initialized)
        if not hasattr(self, "_skills"):
            self._skills: Dict[str, SkillState] = {}
            self._observers: List[Callable[[], None]] = []
            self._initialize_skills()

    @classmethod
    def get_instance(cls) -> "SkillsManager":
        """Get the singleton instance of SkillsManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __new__(cls):
        """Singleton pattern: return existing instance if available."""
        if cls._instance is None:
            instance = super().__new__(cls)
            cls._instance = instance
            return instance
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton (mainly for testing)."""
        cls._instance = None

    def _initialize_skills(self) -> None:
        """Initialize all skills to level -1 (unread) with no XP."""
        for skill_name in SKILL_ORDER:
            self._skills[skill_name] = SkillState(
                level=-1, xp=0, xp_gained=0, timestamp=datetime.now()
            )

    def get_skill(self, skill_name: str) -> SkillState:
        """Get the state of a skill.

        Args:
            skill_name: Name of the skill (case-insensitive)

        Returns:
            SkillState for the requested skill

        Raises:
            ValueError: If skill name is invalid
        """
        normalized = skill_name.lower()
        if normalized not in self._skills:
            raise ValueError(
                f"Unknown skill '{skill_name}'. Valid skills: {', '.join(SKILL_ORDER)}"
            )
        return self._skills[normalized]

    def update_skill_level(self, skill_name: str, level: int) -> None:
        """Update a skill's level (typically from OCR).

        This updates the level and estimates XP based on the level threshold.
        For accurate XP tracking, use update_skill_xp() instead.

        Args:
            skill_name: Name of the skill (case-insensitive)
            level: New level (1-99, or -1 for unreadable)
        """
        if level < -1 or level == 0 or level > 99:
            raise ValueError(f"Level must be -1 or between 1 and 99, got {level}")

        normalized = skill_name.lower()
        skill = self.get_skill(normalized)

        old_level = skill.level
        skill.level = level

        # If we don't have XP data yet, estimate XP based on level
        # Only set XP if level is valid (not -1)
        if not skill.has_xp_data() and level > 0:
            skill.xp = ExperienceTable().level_to_xp(level)

        skill.update_timestamp()

        # Only notify if level actually changed
        if old_level != level:
            self.notify_observers()

    def update_skill_xp(
        self, skill_name: str, xp: int
    ) -> None:
        """Update a skill's XP (from XP watcher or API).

        This is the preferred method for accurate skill tracking.
        Automatically updates level based on XP.

        Args:
            skill_name: Name of the skill (case-insensitive)
            xp: Total XP for the skill
        """
        if xp < 0:
            raise ValueError(f"XP cannot be negative, got {xp}")

        normalized = skill_name.lower()
        skill = self.get_skill(normalized)

        # Update state
        old_xp = skill.xp
        skill.xp = xp
        skill.level = ExperienceTable().xp_to_level(xp)
        skill.update_timestamp()

        # Only notify if XP actually changed
        if old_xp != xp:
            self.notify_observers()

    def get_all_skills(self) -> Dict[str, SkillState]:
        """Get all skill states.

        Returns:
            Dictionary mapping skill names to SkillState objects
        """
        return dict(self._skills)

    def add_observer(self, callback: Callable[[], None]) -> None:
        """Register an observer to be notified when skills change.

        Args:
            callback: Function to call when any skill is updated
        """
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback: Callable[[], None]) -> None:
        """Unregister an observer.

        Args:
            callback: Function to remove from observers
        """
        if callback in self._observers:
            self._observers.remove(callback)

    def notify_observers(self) -> None:
        """Notify all observers that skills have been updated."""
        for callback in self._observers:
            try:
                callback()
            except Exception as e:
                # Don't let observer errors crash the manager
                print(f"Error in SkillsManager observer: {e}")
