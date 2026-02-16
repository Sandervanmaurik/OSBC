"""
Behavior profiles for mouse and camera movement.

Defines activity profiles that control mouse fidgeting behavior and
camera movement patterns independently.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Dict, Any
import copy


class MouseProfile(Enum):
    """Mouse activity behavior profiles."""

    BANK_STANDING = "bank_standing"
    LOW_ACTIVE = "low_active"
    ACTIVE = "active"
    HIGH_ACTIVE = "high_active"
    AFK = "afk"


class CameraProfile(Enum):
    """Camera movement behavior profiles."""

    BANK_STANDING = "bank_standing"
    LOW_ACTIVE = "low_active"
    ACTIVE = "active"
    HIGH_ACTIVE = "high_active"
    AFK = "afk"


class ActivityProfile(Enum):
    """
    Context-aware activity profiles for human-like behavior.

    These profiles replace the legacy BehaviorProfiles system with
    semantically meaningful profiles based on player activity type.
    """

    BANK_STANDING_AFK = "bank_standing_afk"
    BANK_STANDING_ACTIVE = "bank_standing_active"
    SKILLING_AFK = "skilling_afk"
    SKILLING_ACTIVE = "skilling_active"

    @classmethod
    def from_display_name(cls, display_name: str) -> "ActivityProfile":
        """
        Convert GUI display name to ActivityProfile enum.

        Args:
            display_name: Display name from GUI dropdown

        Returns:
            ActivityProfile enum value

        Example:
            profile = ActivityProfile.from_display_name("Bank Standing (Active)")
            # Returns ActivityProfile.BANK_STANDING_ACTIVE
        """
        display_map = {
            "Bank Standing (AFK)": cls.BANK_STANDING_AFK,
            "Bank Standing (Active)": cls.BANK_STANDING_ACTIVE,
            "Skilling (AFK)": cls.SKILLING_AFK,
            "Skilling (Active)": cls.SKILLING_ACTIVE,
        }

        if display_name in display_map:
            return display_map[display_name]

        # Fallback: try to match by profile value
        for profile in cls:
            if profile.value == display_name.lower().replace(" ", "_").replace(
                "(", ""
            ).replace(")", ""):
                return profile

        # Default to skilling active
        return cls.SKILLING_ACTIVE


@dataclass
class MouseProfileConfig:
    """Configuration for mouse behavior."""

    fidget_enabled: bool
    fidget_interval_range: Tuple[float, float]  # seconds (min, max)
    fidget_distance_range: Tuple[int, int]  # pixels (min, max)
    click_delay_multiplier: float  # multiply base delays
    misclick_chance: float  # 0.0 to 1.0


@dataclass
class CameraProfileConfig:
    """Configuration for camera behavior."""

    enabled: bool
    interval_range: Tuple[float, float]  # seconds (min, max)
    horizontal_range: Tuple[int, int]  # degrees
    vertical_range: Tuple[int, int]  # degrees
    vertical_chance: float  # 0.0 to 1.0


# Mouse activity profiles
MOUSE_PROFILES = {
    MouseProfile.BANK_STANDING: MouseProfileConfig(
        fidget_enabled=True,
        fidget_interval_range=(1.0, 15.0),  # Continuous subtle movements
        fidget_distance_range=(10, 28),  # small
        click_delay_multiplier=1.2,  # Slightly slower reactions
        misclick_chance=0.01,
    ),
    MouseProfile.LOW_ACTIVE: MouseProfileConfig(
        fidget_enabled=True,
        fidget_interval_range=(10.0, 20.0),  # Slower fidgeting
        fidget_distance_range=(10, 28),  # Small movements
        click_delay_multiplier=1.5,  # Slower reactions
        misclick_chance=0.02,
    ),
    MouseProfile.ACTIVE: MouseProfileConfig(
        fidget_enabled=True,
        fidget_interval_range=(5.0, 15.0),  # Regular fidgeting
        fidget_distance_range=(10, 50),  # Medium movements
        click_delay_multiplier=1.0,  # Normal speed
        misclick_chance=0.03,
    ),
    MouseProfile.HIGH_ACTIVE: MouseProfileConfig(
        fidget_enabled=True,
        fidget_interval_range=(3.0, 8.0),  # Very frequent fidgeting
        fidget_distance_range=(15, 50),  # Larger movements
        click_delay_multiplier=0.8,  # Faster reactions
        misclick_chance=0.05,
    ),
    MouseProfile.AFK: MouseProfileConfig(
        fidget_enabled=True,
        fidget_interval_range=(30.0, 90.0),  # Very slow fidgeting
        fidget_distance_range=(5, 20),  # Small movements
        click_delay_multiplier=2.0,  # Much slower reactions
        misclick_chance=0.01,
    ),
}


# Camera movement profiles
CAMERA_PROFILES = {
    CameraProfile.BANK_STANDING: CameraProfileConfig(
        enabled=False,  # No camera movement
        interval_range=(60.0, 1200.0),  # Not used when disabled
        horizontal_range=(0, 0),  # Not used when disabled
        vertical_range=(0, 0),  # Not used when disabled
        vertical_chance=0.0,  # Not used when disabled
    ),
    CameraProfile.LOW_ACTIVE: CameraProfileConfig(
        enabled=True,
        interval_range=(25.0, 70.0),  # Rare adjustments
        horizontal_range=(-120, 120),
        vertical_range=(-20, 20),
        vertical_chance=0.35,
    ),
    CameraProfile.ACTIVE: CameraProfileConfig(
        enabled=True,
        interval_range=(30.0, 90.0),  # Occasional adjustments
        horizontal_range=(-120, 120),
        vertical_range=(-20, 20),
        vertical_chance=0.3,
    ),
    CameraProfile.HIGH_ACTIVE: CameraProfileConfig(
        enabled=True,
        interval_range=(45.0, 120.0),  # Frequent adjustments
        horizontal_range=(-90, 90),
        vertical_range=(-15, 15),
        vertical_chance=0.2,
    ),
    CameraProfile.AFK: CameraProfileConfig(
        enabled=True,
        interval_range=(120.0, 300.0),  # Very rare (2-5 minutes)
        horizontal_range=(-120, 120),
        vertical_range=(-20, 20),
        vertical_chance=0.4,
    ),
}


# ======================================================================
# Activity Profile Configurations
# ======================================================================
# Complete behavior configurations for context-aware activity profiles.
# These replace the legacy BehaviorProfiles system with semantically
# meaningful profiles based on player activity type.
# ======================================================================

ACTIVITY_PROFILE_CONFIGS: Dict[ActivityProfile, Dict[str, Any]] = {
    ActivityProfile.BANK_STANDING_AFK: {
        "name": "Bank Standing AFK",
        "description": "Semi-AFK bank standing. Frequent tab-outs, many breaks, slow reactions.",
        "timing": {
            "speed_multiplier": 1.8,  # 80% slower than base (very slow)
            "reaction_min": 0.4,
            "reaction_max": 1.0,
        },
        "mouse": {
            "default_speed": "slow",
            "default_knots": None,
            "overshoot_chance": 0.15,  # More human-like errors
        },
        "action": {
            "misclick_chance": 0.15,  # Higher misclick (distracted)
            "misclick_distance": (-15, 15),
            "hesitation_chance": 0.35,  # Lots of hesitation
            "hesitation_duration": (0.5, 1.5),
            "pre_click_delay_chance": 0.5,
        },
        "attention": {
            "camera_enabled": False,  # No camera movement at bank
            "camera_interval": (120.0, 300.0),  # Not used
            "camera_horizontal_range": (0, 0),
            "camera_vertical_range": (0, 0),
            "camera_vertical_chance": 0.0,
            "skill_check_enabled": False,  # Too AFK to check stats
            "skill_check_interval": (180.0, 420.0),
            "mouse_movement_enabled": True,
            "mouse_movement_interval": (90.0, 240.0),  # Infrequent
            "inventory_check_enabled": False,  # Too AFK
            "inventory_check_interval": (120.0, 300.0),
            # NEW: Tab-out simulation
            "tab_out_enabled": True,
            "tab_out_interval": (60.0, 180.0),  # Frequent tab-outs (1-3 min)
            "tab_out_duration": (10.0, 20.0),  # Longer off-screen time
            # NEW: Bank checking
            "bank_check_enabled": True,
            "bank_check_interval": (120.0, 300.0),  # Check bank 2-5 min
        },
        "breaks": {
            "enabled": True,
            "chance_per_check": 0.08,  # Higher break chance
            "duration_min": 15.0,
            "duration_max": 60.0,
            "duration_mean": 30.0,
            "duration_std": 10.0,
        },
        # Cycle switching settings
        "cycle_switch_chance": 0.05,  # 5% chance to switch after inventory
        "cycle_weights": {
            "bank_standing_afk": 0.3,
            "bank_standing_active": 0.7,
        },
    },
    ActivityProfile.BANK_STANDING_ACTIVE: {
        "name": "Bank Standing Active",
        "description": "Active bank standing. Fast reactions, minimal distractions, fewer tab-outs.",
        "timing": {
            "speed_multiplier": 0.9,  # 10% faster than base
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
            "camera_enabled": False,  # No camera movement at bank
            "camera_interval": (120.0, 300.0),  # Not used
            "camera_horizontal_range": (0, 0),
            "camera_vertical_range": (0, 0),
            "camera_vertical_chance": 0.0,
            "skill_check_enabled": True,
            "skill_check_interval": (90.0, 240.0),  # Check stats occasionally
            "mouse_movement_enabled": True,
            "mouse_movement_interval": (60.0, 150.0),
            "inventory_check_enabled": True,
            "inventory_check_interval": (50.0, 120.0),
            # NEW: Tab-out simulation
            "tab_out_enabled": True,
            "tab_out_interval": (180.0, 600.0),  # Less frequent (3-10 min)
            "tab_out_duration": (5.0, 12.0),  # Shorter off-screen time
            # NEW: Bank checking
            "bank_check_enabled": False,  # Too focused to randomly check bank
        },
        "breaks": {
            "enabled": False,  # Active players don't break as often
            "chance_per_check": 0.02,
            "duration_min": 5.0,
            "duration_max": 20.0,
            "duration_mean": 10.0,
            "duration_std": 4.0,
        },
        # Cycle switching settings
        "cycle_switch_chance": 0.05,  # 5% chance to switch after inventory
        "cycle_weights": {
            "bank_standing_afk": 0.4,
            "bank_standing_active": 0.6,
        },
    },
    ActivityProfile.SKILLING_AFK: {
        "name": "Skilling AFK",
        "description": "Semi-AFK skilling/combat. Occasional camera, tab-outs, many breaks.",
        "timing": {
            "speed_multiplier": 1.5,  # 50% slower than base
            "reaction_min": 0.3,
            "reaction_max": 0.8,
        },
        "mouse": {
            "default_speed": "medium",
            "default_knots": None,
            "overshoot_chance": 0.10,
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
            "camera_interval": (90.0, 240.0),  # Rare camera moves
            "camera_horizontal_range": (-120, 120),
            "camera_vertical_range": (-20, 20),
            "camera_vertical_chance": 0.4,
            "skill_check_enabled": True,
            "skill_check_interval": (120.0, 300.0),  # Infrequent
            "mouse_movement_enabled": True,
            "mouse_movement_interval": (90.0, 240.0),
            "inventory_check_enabled": True,
            "inventory_check_interval": (120.0, 300.0),
            # NEW: Tab-out simulation
            "tab_out_enabled": True,
            "tab_out_interval": (120.0, 360.0),  # Moderate frequency (2-6 min)
            "tab_out_duration": (8.0, 20.0),
            # NEW: Bank checking
            "bank_check_enabled": False,  # Not at bank
        },
        "breaks": {
            "enabled": True,
            "chance_per_check": 0.05,
            "duration_min": 15.0,
            "duration_max": 60.0,
            "duration_mean": 30.0,
            "duration_std": 10.0,
        },
        # Cycle switching settings
        "cycle_switch_chance": 0.04,  # 4% chance to switch after inventory
        "cycle_weights": {
            "skilling_afk": 0.4,
            "skilling_active": 0.6,
        },
    },
    ActivityProfile.SKILLING_ACTIVE: {
        "name": "Skilling Active",
        "description": "Active skilling/combat. Focused, efficient, regular camera moves.",
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
            "camera_interval": (30.0, 90.0),  # Regular camera moves
            "camera_horizontal_range": (-120, 120),
            "camera_vertical_range": (-20, 20),
            "camera_vertical_chance": 0.3,
            "skill_check_enabled": True,
            "skill_check_interval": (60.0, 180.0),
            "mouse_movement_enabled": True,
            "mouse_movement_interval": (45.0, 120.0),
            "inventory_check_enabled": True,
            "inventory_check_interval": (40.0, 100.0),
            # NEW: Tab-out simulation
            "tab_out_enabled": True,
            "tab_out_interval": (240.0, 600.0),  # Less frequent (4-10 min)
            "tab_out_duration": (5.0, 15.0),
            # NEW: Bank checking
            "bank_check_enabled": False,  # Not at bank
        },
        "breaks": {
            "enabled": False,
            "chance_per_check": 0.02,
            "duration_min": 8.0,
            "duration_max": 35.0,
            "duration_mean": 16.0,
            "duration_std": 6.0,
        },
        # Cycle switching settings
        "cycle_switch_chance": 0.05,  # 5% chance to switch after inventory
        "cycle_weights": {
            "skilling_afk": 0.3,
            "skilling_active": 0.7,
        },
    },
}


# ======================================================================
# Backward Compatibility: Old BehaviorProfiles Class
# ======================================================================
# This class provides the original behavior profile system for timing,
# mouse, action, attention, and breaks configuration. It's kept for
# backward compatibility with existing bots that don't use the new
# MouseProfile/CameraProfile system yet.
# ======================================================================


class BehaviorProfiles:
    """
    DEPRECATED: Predefined behavior profiles for different playstyles.

    This class is deprecated in favor of ActivityProfile and ACTIVITY_PROFILE_CONFIGS.
    Use the new activity-based profiles for better semantic meaning:
    - ActivityProfile.BANK_STANDING_AFK
    - ActivityProfile.BANK_STANDING_ACTIVE
    - ActivityProfile.SKILLING_AFK
    - ActivityProfile.SKILLING_ACTIVE

    Legacy profiles (kept for backward compatibility):
        - LOW_ACTIVE: Slower, more deliberate. Maximum human-like behavior.
        - ACTIVE: Balanced, efficient gameplay. (Recommended default)
        - HIGH_ACTIVE: Fast, minimal distractions. Good for short sessions.
        - AFK: Very slow, minimal attention. For semi-AFK activities.

    Example (DEPRECATED):
        # Old way (still works but deprecated)
        manager = BehaviorManager(bot, profile="active")

    Example (RECOMMENDED):
        # New way with activity profiles
        from utilities.behavior.profiles import ActivityProfile
        manager = BehaviorManager(bot, activity_profile=ActivityProfile.SKILLING_ACTIVE)
    """

    # Migration map: old profile names -> new ActivityProfile
    _MIGRATION_MAP = {
        "low-active": ActivityProfile.SKILLING_AFK,
        "active": ActivityProfile.SKILLING_ACTIVE,
        "high-active": ActivityProfile.BANK_STANDING_ACTIVE,
        "afk": ActivityProfile.SKILLING_AFK,
    }

    LOW_ACTIVE = {
        "name": "Low-Active",
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

    ACTIVE = {
        "name": "Active",
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

    HIGH_ACTIVE = {
        "name": "High-Active",
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

    AFK = {
        "name": "AFK",
        "description": "Very slow, minimal attention. For semi-AFK activities.",
        "timing": {
            "speed_multiplier": 1.8,  # 80% slower than base (very slow)
            "reaction_min": 0.3,
            "reaction_max": 0.9,
        },
        "mouse": {
            "default_speed": "slow",
            "default_knots": None,
            "overshoot_chance": 0.15,  # More human-like errors
        },
        "action": {
            "misclick_chance": 0.18,  # Higher misclick (distracted)
            "misclick_distance": (-15, 15),
            "hesitation_chance": 0.35,  # Lots of hesitation
            "hesitation_duration": (0.5, 1.5),
            "pre_click_delay_chance": 0.5,
        },
        "attention": {
            "camera_enabled": True,
            "camera_interval": (120.0, 300.0),  # Very infrequent (2-5 minutes)
            "camera_horizontal_range": (-120, 120),
            "camera_vertical_range": (-20, 20),
            "camera_vertical_chance": 0.4,
            "skill_check_enabled": True,
            "skill_check_interval": (180.0, 420.0),  # Very infrequent (3-7 minutes)
            "mouse_movement_enabled": True,
            "mouse_movement_interval": (90.0, 240.0),  # Infrequent (1.5-4 minutes)
            "inventory_check_enabled": True,
            "inventory_check_interval": (120.0, 300.0),  # Infrequent (2-5 minutes)
        },
        "breaks": {
            "enabled": True,
            "chance_per_check": 0.05,  # More frequent breaks
            "duration_min": 15.0,
            "duration_max": 60.0,
            "duration_mean": 30.0,
            "duration_std": 10.0,
        },
    }

    @classmethod
    def get(cls, profile_name: str) -> Dict[str, Any]:
        """
        Get a profile by name (case-insensitive).

        DEPRECATED: Use ActivityProfile and ACTIVITY_PROFILE_CONFIGS instead.

        Args:
            profile_name: Name of the profile ("low-active", "active", "high-active", "afk")

        Returns:
            Profile configuration dictionary

        Raises:
            ValueError: If profile name is not recognized

        Example (DEPRECATED):
            profile = BehaviorProfiles.get("active")

        Example (RECOMMENDED):
            from utilities.behavior.profiles import ActivityProfile, ACTIVITY_PROFILE_CONFIGS
            profile = ACTIVITY_PROFILE_CONFIGS[ActivityProfile.SKILLING_ACTIVE]
        """
        import warnings

        warnings.warn(
            "BehaviorProfiles.get() is deprecated. Use ActivityProfile and ACTIVITY_PROFILE_CONFIGS instead. "
            "See profiles.py for migration guide.",
            DeprecationWarning,
            stacklevel=2,
        )

        profile_map = {
            "low-active": cls.LOW_ACTIVE,
            "active": cls.ACTIVE,
            "high-active": cls.HIGH_ACTIVE,
            "afk": cls.AFK,
        }

        key = profile_name.lower()
        if key not in profile_map:
            raise ValueError(
                f"Unknown profile '{profile_name}'. "
                f"Valid profiles: {', '.join(profile_map.keys())}"
            )

        # Return a copy to avoid mutations
        return copy.deepcopy(profile_map[key])

    @classmethod
    def list_profiles(cls) -> list:
        """
        Get list of available profile names.

        Returns:
            List of profile names
        """
        return ["low-active", "active", "high-active", "afk"]

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
