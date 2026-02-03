"""Predefined behavior profiles."""

from typing import Dict, Any


class BehaviorProfiles:
    """
    Predefined behavior profiles for different playstyles.

    Each profile defines a complete set of behavior configurations that
    can be used as-is or customized further.

    Profiles:
        - CAUTIOUS: Slower, more deliberate. Maximum human-like behavior.
        - EXPERIENCED: Balanced, efficient gameplay. (Recommended default)
        - FOCUSED: Fast, minimal distractions. Good for short sessions.

    Example:
        # Use predefined profile
        manager = BehaviorManager(bot, profile="experienced")

        # Customize profile
        manager = BehaviorManager(
            bot,
            profile="cautious",
            custom_config={"timing": {"speed_multiplier": 1.5}}
        )
    """

    CAUTIOUS = {
        "name": "Cautious",
        "description": "Slower, more deliberate actions. Maximum human-like behavior.",
        "timing": {
            "speed_multiplier": 1.3,  # 30% slower than base
            "reaction_min": 0.2,
            "reaction_max": 0.6,
        },
        "mouse": {
            "default_speed": "medium",
            "default_knots": None,  # Auto-calculate based on distance
            "overshoot_chance": 0.08,
        },
        "action": {
            "misclick_chance": 0.12,
            "misclick_distance": (-12, 12),
            "hesitation_chance": 0.25,
            "hesitation_duration": (0.3, 0.9),
            "pre_click_delay_chance": 0.4,
        },
        "attention": {
            "camera_enabled": True,
            "camera_interval": (25.0, 70.0),
            "camera_horizontal_range": (-120, 120),
            "camera_vertical_range": (-20, 20),
            "camera_vertical_chance": 0.35,
            "skill_check_enabled": True,
            "skill_check_interval": (50.0, 150.0),
            "mouse_movement_enabled": True,
            "mouse_movement_interval": (35.0, 100.0),
            "inventory_check_enabled": True,
            "inventory_check_interval": (30.0, 90.0),
        },
        "breaks": {
            "enabled": True,
            "chance_per_check": 0.03,
            "duration_min": 10.0,
            "duration_max": 40.0,
            "duration_mean": 20.0,
            "duration_std": 7.0,
        },
    }

    EXPERIENCED = {
        "name": "Experienced",
        "description": "Balanced, efficient gameplay. Recommended for most bots.",
        "timing": {
            "speed_multiplier": 1.0,  # Base speed
            "reaction_min": 0.15,
            "reaction_max": 0.45,
        },
        "mouse": {
            "default_speed": "fast",
            "default_knots": None,
            "overshoot_chance": 0.05,
        },
        "action": {
            "misclick_chance": 0.08,
            "misclick_distance": (-12, 12),
            "hesitation_chance": 0.15,
            "hesitation_duration": (0.2, 0.7),
            "pre_click_delay_chance": 0.3,
        },
        "attention": {
            "camera_enabled": True,
            "camera_interval": (30.0, 90.0),
            "camera_horizontal_range": (-120, 120),
            "camera_vertical_range": (-20, 20),
            "camera_vertical_chance": 0.3,
            "skill_check_enabled": True,
            "skill_check_interval": (60.0, 180.0),
            "mouse_movement_enabled": True,
            "mouse_movement_interval": (45.0, 120.0),
            "inventory_check_enabled": True,
            "inventory_check_interval": (40.0, 100.0),
        },
        "breaks": {
            "enabled": False,
            "chance_per_check": 0.02,
            "duration_min": 8.0,
            "duration_max": 35.0,
            "duration_mean": 16.0,
            "duration_std": 6.0,
        },
    }

    FOCUSED = {
        "name": "Focused",
        "description": "Fast, minimal distractions. Good for short, efficient sessions.",
        "timing": {
            "speed_multiplier": 0.85,  # 15% faster than base
            "reaction_min": 0.1,
            "reaction_max": 0.35,
        },
        "mouse": {
            "default_speed": "fast",
            "default_knots": None,
            "overshoot_chance": 0.03,
        },
        "action": {
            "misclick_chance": 0.05,
            "misclick_distance": (-8, 8),
            "hesitation_chance": 0.08,
            "hesitation_duration": (0.15, 0.5),
            "pre_click_delay_chance": 0.2,
        },
        "attention": {
            "camera_enabled": True,
            "camera_interval": (45.0, 120.0),
            "camera_horizontal_range": (-90, 90),
            "camera_vertical_range": (-15, 15),
            "camera_vertical_chance": 0.2,
            "skill_check_enabled": False,  # Too focused to check stats frequently
            "skill_check_interval": (120.0, 300.0),
            "mouse_movement_enabled": True,
            "mouse_movement_interval": (60.0, 150.0),
            "inventory_check_enabled": True,
            "inventory_check_interval": (50.0, 120.0),
        },
        "breaks": {
            "enabled": False,
            "chance_per_check": 0.01,
            "duration_min": 5.0,
            "duration_max": 20.0,
            "duration_mean": 10.0,
            "duration_std": 4.0,
        },
    }

    @classmethod
    def get(cls, profile_name: str) -> Dict[str, Any]:
        """
        Get a profile by name (case-insensitive).

        Args:
            profile_name: Name of the profile ("cautious", "experienced", "focused")

        Returns:
            Profile configuration dictionary

        Raises:
            ValueError: If profile name is not recognized

        Example:
            profile = BehaviorProfiles.get("experienced")
        """
        profile_map = {
            "cautious": cls.CAUTIOUS,
            "experienced": cls.EXPERIENCED,
            "focused": cls.FOCUSED,
        }

        key = profile_name.lower()
        if key not in profile_map:
            raise ValueError(
                f"Unknown profile '{profile_name}'. "
                f"Valid profiles: {', '.join(profile_map.keys())}"
            )

        # Return a copy to avoid mutations
        import copy

        return copy.deepcopy(profile_map[key])

    @classmethod
    def list_profiles(cls) -> list:
        """
        Get list of available profile names.

        Returns:
            List of profile names
        """
        return ["cautious", "experienced", "focused"]

    @classmethod
    def get_profile_description(cls, profile_name: str) -> str:
        """
        Get description for a profile.

        Args:
            profile_name: Name of the profile

        Returns:
            Profile description
        """
        profile = cls.get(profile_name)
        return profile.get("description", "")
