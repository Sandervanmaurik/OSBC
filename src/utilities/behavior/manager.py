"""Behavior manager for orchestrating all behavior modules."""

import time
import random
import threading
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Any, Optional

from utilities.behavior.profiles import BehaviorProfiles
from utilities.behavior.profiles import (
    MouseProfile,
    CameraProfile,
    MOUSE_PROFILES,
    CAMERA_PROFILES,
    MouseProfileConfig,
    CameraProfileConfig,
)
from utilities.behavior.modules import (
    TimingBehavior,
    MouseBehavior,
    ActionBehavior,
    AttentionBehavior,
    BreakBehavior,
)

if TYPE_CHECKING:
    from model.bot import Bot


class BehaviorManager:
    """
    Orchestrates all behavior modules for a bot.

    The BehaviorManager is the main interface for adding human-like behaviors
    to your bot. It initializes and manages all behavior modules based on a
    selected profile and optional custom configuration.

    Attributes:
        timing: TimingBehavior module for sleep patterns and delays
        mouse: MouseBehavior module for mouse movements
        action: ActionBehavior module for action execution patterns
        attention: AttentionBehavior module for random attention behaviors
        breaks: BreakBehavior module for break timing

    Example:
        # In your bot's __init__:
        self.behavior = BehaviorManager(
            bot=self,
            profile="experienced"
        )

        # Customize for specific bot needs
        self.behavior = BehaviorManager(
            bot=self,
            profile="experienced",
            custom_config={
                "attention": {
                    "camera_enabled": False  # Disable camera for banking bot
                }
            }
        )

        # In your bot code:
        self.behavior.timing.sleep("short")
        self.behavior.mouse.move_to(target)
        self.behavior.attention.perform_random_behaviors()
    """

    def __init__(
        self,
        bot: "Bot",
        profile: str = "experienced",
        mouse_profile: Optional[MouseProfile] = None,
        camera_profile: Optional[CameraProfile] = None,
        custom_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize behavior manager with profile and custom config.

        Args:
            bot: The bot instance that will use these behaviors
            profile: Profile name ("cautious", "experienced", "focused")
            mouse_profile: Optional mouse activity profile
            camera_profile: Optional camera movement profile
            custom_config: Optional dict to override profile settings
                          Format: {"timing": {...}, "mouse": {...}, etc.}

        Example:
            # Use default profile
            manager = BehaviorManager(bot, profile="experienced")

            # Customize specific settings
            manager = BehaviorManager(
                bot,
                profile="cautious",
                custom_config={
                    "timing": {"speed_multiplier": 1.5},
                    "attention": {"camera_enabled": False}
                }
            )

            # Use activity profiles
            manager = BehaviorManager(
                bot,
                profile="high-active",
                mouse_profile=MouseProfile.BANK_STANDING,
                camera_profile=CameraProfile.BANK_STANDING,
            )
        """
        self.bot = bot
        self.profile_name = profile

        # Store mouse and camera profiles
        self.mouse_profile = mouse_profile or MouseProfile.ACTIVE
        self.camera_profile = camera_profile or CameraProfile.ACTIVE
        self.mouse_config = MOUSE_PROFILES[self.mouse_profile]
        self.camera_config = CAMERA_PROFILES[self.camera_profile]

        # Fidget thread state
        self._fidget_thread = None
        self._fidget_stop_event = None
        self._fidget_paused = False  # Pause during actions
        self._fidget_started = False

        # Load profile configuration
        profile_config = BehaviorProfiles.get(profile)

        # Merge with custom config if provided
        if custom_config:
            profile_config = self._merge_configs(profile_config, custom_config)

        # Store final config
        self.config = profile_config

        # Initialize stats tracking
        self.stats = defaultdict(int)
        self.stats_start_time = time.time()

        # Initialize all behavior modules
        self.timing = TimingBehavior(config=profile_config.get("timing", {}), bot=bot)

        self.mouse = MouseBehavior(config=profile_config.get("mouse", {}), bot=bot)

        self.action = ActionBehavior(config=profile_config.get("action", {}), bot=bot)

        self.attention = AttentionBehavior(
            config=profile_config.get("attention", {}), bot=bot
        )

        self.breaks = BreakBehavior(config=profile_config.get("breaks", {}), bot=bot)

    def _merge_configs(
        self, base: Dict[str, Any], custom: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deep merge custom config into base config.

        Args:
            base: Base configuration dictionary
            custom: Custom overrides

        Returns:
            Merged configuration
        """
        import copy

        result = copy.deepcopy(base)

        for key, value in custom.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursively merge nested dicts
                result[key] = {**result[key], **value}
            else:
                # Override value
                result[key] = value

        return result

    def configure(self, **module_toggles) -> None:
        """
        Enable/disable specific behavior modules or features.

        This is a convenience method for quickly toggling behaviors without
        modifying the full configuration.

        Args:
            **module_toggles: Keyword arguments for module configuration
                Supported: timing_enabled, mouse_enabled, action_enabled,
                          attention_enabled, breaks_enabled,
                          camera_enabled, skill_check_enabled, etc.

        Example:
            # Disable camera for fletching bot
            self.behavior.configure(camera_enabled=False)

            # Disable all attention behaviors
            self.behavior.configure(attention_enabled=False)

            # Enable breaks
            self.behavior.configure(breaks_enabled=True)
        """
        # Module-level toggles
        if "timing_enabled" in module_toggles:
            self.timing.enabled = module_toggles["timing_enabled"]

        if "mouse_enabled" in module_toggles:
            self.mouse.enabled = module_toggles["mouse_enabled"]

        if "action_enabled" in module_toggles:
            self.action.enabled = module_toggles["action_enabled"]

        if "attention_enabled" in module_toggles:
            self.attention.enabled = module_toggles["attention_enabled"]

        if "breaks_enabled" in module_toggles:
            self.breaks.enabled = module_toggles["breaks_enabled"]

        # Feature-specific toggles for attention module
        attention_features = [
            "camera_enabled",
            "skill_check_enabled",
            "mouse_movement_enabled",
            "inventory_check_enabled",
        ]
        for feature in attention_features:
            if feature in module_toggles:
                self.attention.update_config(**{feature: module_toggles[feature]})

    def disable_all(self) -> None:
        """
        Disable all behavior modules.

        Useful for testing or emergency situations.

        Example:
            self.behavior.disable_all()
        """
        self.timing.disable()
        self.mouse.disable()
        self.action.disable()
        self.attention.disable()
        self.breaks.disable()

    def enable_all(self) -> None:
        """
        Enable all behavior modules.

        Re-enables modules after disable_all() call.

        Example:
            self.behavior.enable_all()
        """
        self.timing.enable()
        self.mouse.enable()
        self.action.enable()
        self.attention.enable()
        self.breaks.enable()

    def get_profile_info(self) -> Dict[str, str]:
        """
        Get information about the current profile.

        Returns:
            Dictionary with profile name and description

        Example:
            info = self.behavior.get_profile_info()
            print(f"Using profile: {info['name']} - {info['description']}")
        """
        return {
            "name": self.config.get("name", self.profile_name),
            "description": self.config.get("description", ""),
        }

    def update_speed_multiplier(self, multiplier: float) -> None:
        """
        Update the timing speed multiplier.

        This affects all timing-based behaviors. Useful for dynamically
        adjusting bot speed.

        Args:
            multiplier: Speed multiplier (1.0 = normal, >1.0 = slower, <1.0 = faster)

        Example:
            # Make bot 20% slower
            self.behavior.update_speed_multiplier(1.2)

            # Make bot 10% faster
            self.behavior.update_speed_multiplier(0.9)
        """
        self.timing.update_config(speed_multiplier=multiplier)

    def summary(self) -> str:
        """
        Get a summary of current behavior configuration.

        Returns:
            Human-readable configuration summary

        Example:
            print(self.behavior.summary())
        """
        info = self.get_profile_info()
        lines = [
            f"Behavior Profile: {info['name']}",
            f"Description: {info['description']}",
            "",
            "Module Status:",
            f"  Timing: {'Enabled' if self.timing.enabled else 'Disabled'}",
            f"  Mouse: {'Enabled' if self.mouse.enabled else 'Disabled'}",
            f"  Action: {'Enabled' if self.action.enabled else 'Disabled'}",
            f"  Attention: {'Enabled' if self.attention.enabled else 'Disabled'}",
            f"  Breaks: {'Enabled' if self.breaks.enabled else 'Disabled'}",
            "",
            "Key Settings:",
            f"  Speed Multiplier: {self.timing.config.get('speed_multiplier', 1.0)}x",
            f"  Mouse Speed: {self.mouse.config.get('default_speed', 'fast')}",
            f"  Misclick Chance: {self.action.config.get('misclick_chance', 0.08):.1%}",
            f"  Camera Enabled: {self.attention.config.get('camera_enabled', True)}",
        ]
        return "\n".join(lines)

    def increment_stat(self, category: str) -> None:
        """
        Increment a behavior stat counter.

        Args:
            category: Stat category (e.g., "camera", "mouse_movement", "skill_check")

        Example:
            self.behavior.increment_stat("camera")
        """
        self.stats[category] += 1

    def get_stats_summary(self, since_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Get summary of behavior statistics.

        Args:
            since_time: Optional timestamp to calculate duration from (defaults to stats_start_time)

        Returns:
            Dictionary with stat counts and duration

        Example:
            summary = self.behavior.get_stats_summary()
            # {"camera": 5, "mouse_movement": 12, "duration_seconds": 300}
        """
        start = since_time if since_time is not None else self.stats_start_time
        duration = time.time() - start

        summary = dict(self.stats)
        summary["duration_seconds"] = duration
        summary["duration_minutes"] = duration / 60.0
        return summary

    def reset_stats(self) -> None:
        """
        Reset all behavior statistics and start time.

        Example:
            self.behavior.reset_stats()
        """
        self.stats.clear()
        self.stats_start_time = time.time()

    def log_stats_summary(self, bot_logger=None) -> None:
        """
        Log a summary of behavior statistics.

        Args:
            bot_logger: Optional logger function (defaults to self.bot.log_msg)

        Example:
            self.behavior.log_stats_summary()
        """
        logger = bot_logger or (
            self.bot.log_msg if hasattr(self.bot, "log_msg") else print
        )
        summary = self.get_stats_summary()

        duration_min = summary.get("duration_minutes", 0)
        camera = summary.get("camera", 0)
        mouse = summary.get("mouse_movement", 0)
        skill = summary.get("skill_check", 0)
        inventory = summary.get("inventory_check", 0)

        logger(
            f"Behavior stats ({duration_min:.1f}min): "
            f"Camera={camera}, Mouse={mouse}, Skills={skill}, Inventory={inventory}"
        )

    def get_camera_config(self) -> CameraProfileConfig:
        """
        Get camera configuration from profile.

        Returns:
            CameraProfileConfig instance
        """
        return self.camera_config

    def start_fidgeting(self, bot) -> None:
        """
        Start continuous mouse fidgeting in background thread.

        Args:
            bot: Bot instance for mouse control and game window access
        """
        if not self.mouse_config.fidget_enabled:
            self.bot.log_msg("Mouse fidgeting disabled for this profile")
            return

        if self._fidget_started:
            return  # Already running

        # Random startup delay (1-5s) to feel more natural
        startup_delay = random.uniform(1.0, 5.0)
        time.sleep(startup_delay)

        self._fidget_stop_event = threading.Event()
        self._fidget_thread = threading.Thread(
            target=self._fidget_loop, args=(bot,), daemon=True, name="MouseFidget"
        )
        self._fidget_thread.start()
        self._fidget_started = True
        self.bot.log_msg(
            f"Mouse fidgeting started (profile: {self.mouse_profile.value})"
        )

    def stop_fidgeting(self) -> None:
        """Stop the fidgeting background thread cleanly."""
        if not self._fidget_started:
            return

        if self._fidget_stop_event:
            self._fidget_stop_event.set()

        if self._fidget_thread and self._fidget_thread.is_alive():
            self._fidget_thread.join(timeout=2.0)

        self._fidget_started = False
        self.bot.log_msg("Mouse fidgeting stopped")

    def pause_fidgeting(self) -> None:
        """
        Temporarily pause fidgeting during critical actions.
        Call this before clicking, moving, or performing actions.
        """
        self._fidget_paused = True

    def resume_fidgeting(self) -> None:
        """Resume fidgeting after critical actions are complete."""
        self._fidget_paused = False

    def _fidget_loop(self, bot) -> None:
        """
        Background loop for continuous mouse fidgeting.
        Runs until stop_fidgeting() is called.
        Pauses when _fidget_paused is True.
        """
        import utilities.random_util as rd

        while not self._fidget_stop_event.is_set():
            # Generate random interval from profile range
            min_interval, max_interval = self.mouse_config.fidget_interval_range
            interval = rd.truncated_normal_sample(
                min_interval,
                max_interval,
                mean=(min_interval + max_interval) / 2,
                std=(max_interval - min_interval) / 6,
            )

            # Sleep in 0.5s chunks to be responsive to stop event
            slept = 0.0
            while slept < interval and not self._fidget_stop_event.is_set():
                time.sleep(0.5)
                slept += 0.5

            if self._fidget_stop_event.is_set():
                break

            # Only perform fidget if not paused
            if not self._fidget_paused:
                self._perform_fidget(bot)

    def _perform_fidget(self, bot) -> None:
        """
        Perform a single smooth mouse movement to a random point.
        Movement stays within game window bounds and uses varying speeds.
        """
        try:
            # Get game window bounds
            if not bot.win or not bot.win.game_view:
                return

            game_view = bot.win.game_view

            # Pick a random point within the game view
            target_point = game_view.random_point()

            # Vary the speed based on profile
            # Bank-standing: slower, more deliberate
            # Active/High-Active: faster movements
            speed_options = ["medium", "fast", "fastest"]

            # Weight speeds based on profile
            if self.mouse_profile.value == "bank_standing":
                # Prefer slower speeds for bank-standing
                speed = random.choices(
                    speed_options,
                    weights=[0.5, 0.35, 0.15],  # 50% medium, 35% fast, 15% fastest
                    k=1,
                )[0]
            elif self.mouse_profile.value in ["active", "low_active"]:
                # Balanced speeds
                speed = random.choices(
                    speed_options,
                    weights=[0.3, 0.4, 0.3],  # 30% medium, 40% fast, 30% fastest
                    k=1,
                )[0]
            else:  # high_active, afk
                # Prefer faster speeds
                speed = random.choices(
                    speed_options,
                    weights=[0.15, 0.35, 0.5],  # 15% medium, 35% fast, 50% fastest
                    k=1,
                )[0]

            # Move mouse smoothly (no click)
            bot.mouse.move_to(
                target_point,
                mouseSpeed=speed,
                knotsCount=random.choice([1, 2]),  # Vary path complexity
            )

        except Exception as exc:
            # Don't crash the fidget thread - silently continue
            pass
