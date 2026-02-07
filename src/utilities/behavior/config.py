"""Configuration dataclasses and utilities for behavior system."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from utilities.behavior.profiles import MouseProfile, CameraProfile


@dataclass
class TimingConfig:
    """Configuration for timing behaviors."""

    speed_multiplier: float = 1.0
    reaction_min: float = 0.15
    reaction_max: float = 0.45

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimingConfig":
        """Create TimingConfig from dictionary."""
        return cls(
            speed_multiplier=data.get("speed_multiplier", 1.0),
            reaction_min=data.get("reaction_min", 0.15),
            reaction_max=data.get("reaction_max", 0.45),
        )


@dataclass
class MouseConfig:
    """Configuration for mouse behaviors."""

    default_speed: str = "fast"
    default_knots: Optional[int] = None
    overshoot_chance: float = 0.05

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MouseConfig":
        """Create MouseConfig from dictionary."""
        return cls(
            default_speed=data.get("default_speed", "fast"),
            default_knots=data.get("default_knots"),
            overshoot_chance=data.get("overshoot_chance", 0.05),
        )


@dataclass
class ActionConfig:
    """Configuration for action behaviors."""

    misclick_chance: float = 0.08
    misclick_distance: Tuple[int, int] = (-12, 12)
    hesitation_chance: float = 0.15
    hesitation_duration: Tuple[float, float] = (0.2, 0.7)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionConfig":
        """Create ActionConfig from dictionary."""
        return cls(
            misclick_chance=data.get("misclick_chance", 0.08),
            misclick_distance=tuple(data.get("misclick_distance", [-12, 12])),
            hesitation_chance=data.get("hesitation_chance", 0.15),
            hesitation_duration=tuple(data.get("hesitation_duration", [0.2, 0.7])),
        )


@dataclass
class AttentionConfig:
    """Configuration for attention behaviors."""

    camera_enabled: bool = True
    camera_interval: Tuple[float, float] = (30.0, 90.0)
    camera_horizontal_range: Tuple[int, int] = (-120, 120)
    camera_vertical_range: Tuple[int, int] = (-20, 20)
    camera_vertical_chance: float = 0.3

    skill_check_enabled: bool = True
    skill_check_interval: Tuple[float, float] = (60.0, 180.0)

    mouse_movement_enabled: bool = True
    mouse_movement_interval: Tuple[float, float] = (45.0, 120.0)

    inventory_check_enabled: bool = True
    inventory_check_interval: Tuple[float, float] = (40.0, 100.0)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttentionConfig":
        """Create AttentionConfig from dictionary."""
        return cls(
            camera_enabled=data.get("camera_enabled", True),
            camera_interval=tuple(data.get("camera_interval", [30.0, 90.0])),
            camera_horizontal_range=tuple(
                data.get("camera_horizontal_range", [-120, 120])
            ),
            camera_vertical_range=tuple(data.get("camera_vertical_range", [-20, 20])),
            camera_vertical_chance=data.get("camera_vertical_chance", 0.3),
            skill_check_enabled=data.get("skill_check_enabled", True),
            skill_check_interval=tuple(data.get("skill_check_interval", [60.0, 180.0])),
            mouse_movement_enabled=data.get("mouse_movement_enabled", True),
            mouse_movement_interval=tuple(
                data.get("mouse_movement_interval", [45.0, 120.0])
            ),
            inventory_check_enabled=data.get("inventory_check_enabled", True),
            inventory_check_interval=tuple(
                data.get("inventory_check_interval", [40.0, 100.0])
            ),
        )


@dataclass
class BreakConfig:
    """Configuration for break behaviors."""

    enabled: bool = False
    chance_per_check: float = 0.02
    duration_min: float = 8.0
    duration_max: float = 35.0
    duration_mean: float = 16.0
    duration_std: float = 6.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BreakConfig":
        """Create BreakConfig from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            chance_per_check=data.get("chance_per_check", 0.02),
            duration_min=data.get("duration_min", 8.0),
            duration_max=data.get("duration_max", 35.0),
            duration_mean=data.get("duration_mean", 16.0),
            duration_std=data.get("duration_std", 6.0),
        )


@dataclass
class BehaviorConfig:
    """Complete behavior configuration for a bot."""

    name: str
    description: str
    timing: Dict[str, Any] = field(default_factory=dict)
    mouse: Dict[str, Any] = field(default_factory=dict)
    action: Dict[str, Any] = field(default_factory=dict)
    attention: Dict[str, Any] = field(default_factory=dict)
    breaks: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BehaviorConfig":
        """Create BehaviorConfig from dictionary."""
        return cls(
            name=data.get("name", "Custom"),
            description=data.get("description", "Custom behavior profile"),
            timing=data.get("timing", {}),
            mouse=data.get("mouse", {}),
            action=data.get("action", {}),
            attention=data.get("attention", {}),
            breaks=data.get("breaks", {}),
        )

    def merge_with(self, custom: Dict[str, Any]) -> "BehaviorConfig":
        """
        Merge this config with custom overrides.

        Args:
            custom: Dictionary of custom configuration overrides

        Returns:
            New BehaviorConfig with merged values
        """
        merged = BehaviorConfig(
            name=custom.get("name", self.name),
            description=custom.get("description", self.description),
            timing={**self.timing, **custom.get("timing", {})},
            mouse={**self.mouse, **custom.get("mouse", {})},
            action={**self.action, **custom.get("action", {})},
            attention={**self.attention, **custom.get("attention", {})},
            breaks={**self.breaks, **custom.get("breaks", {})},
        )
        return merged


@dataclass
class BotBehaviorConfig:
    """
    Configuration for bot BehaviorManager initialization.

    Provides a type-safe way to configure bot behavior when creating
    a bot instance. Bots can pass this to OSRSBot.__init__.

    Attributes:
        profile: Behavior profile name ("cautious", "active", "high-active", etc.)
        mouse_profile: Optional mouse activity profile (fidgeting frequency)
        camera_profile: Optional camera movement profile
        custom_config: Optional dict to override specific profile settings

    Example:
        # Bank-standing bot with minimal camera movement
        from utilities.behavior.config import BotBehaviorConfig
        from utilities.behavior.profiles import MouseProfile, CameraProfile

        config = BotBehaviorConfig(
            profile="high-active",
            mouse_profile=MouseProfile.BANK_STANDING,
            camera_profile=CameraProfile.BANK_STANDING,
            custom_config={
                "timing": {"speed_multiplier": 0.9},
                "action": {"misclick_chance": 0.05},
            }
        )

        # Pass to OSRSBot
        super().__init__(
            bot_title="Cooking",
            description="...",
            behavior_config=config,
        )
    """

    profile: str = "active"
    mouse_profile: Optional["MouseProfile"] = None
    camera_profile: Optional["CameraProfile"] = None
    custom_config: Optional[Dict[str, Any]] = None

    def to_kwargs(self) -> Dict[str, Any]:
        """
        Convert to kwargs dict for BehaviorManager.__init__.

        Returns:
            Dictionary with keys matching BehaviorManager.__init__ parameters

        Example:
            config = BotBehaviorConfig(profile="high-active")
            manager = BehaviorManager(bot, **config.to_kwargs())
        """
        kwargs: Dict[str, Any] = {"profile": self.profile}

        if self.mouse_profile is not None:
            kwargs["mouse_profile"] = self.mouse_profile

        if self.camera_profile is not None:
            kwargs["camera_profile"] = self.camera_profile

        if self.custom_config is not None:
            kwargs["custom_config"] = self.custom_config

        return kwargs
