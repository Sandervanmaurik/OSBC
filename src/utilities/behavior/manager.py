"""Behavior manager for orchestrating all behavior modules."""

import time
import random
import threading
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Any, Optional, Union

from utilities.behavior.profiles import BehaviorProfiles
from utilities.behavior.profiles import (
    ActivityProfile,
    ACTIVITY_PROFILE_CONFIGS,
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
        profile: str = "active",  # DEPRECATED: Use activity_profile
        activity_profile: Optional[ActivityProfile] = None,  # RECOMMENDED
        cycle_enabled: bool = True,
        mouse_profile: Optional[MouseProfile] = None,
        camera_profile: Optional[CameraProfile] = None,
        custom_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize behavior manager with profile and custom config.

        Args:
            bot: The bot instance that will use these behaviors
            profile: DEPRECATED - Legacy profile name ("active", "high-active", etc.)
            activity_profile: RECOMMENDED - Activity profile enum (ActivityProfile.SKILLING_ACTIVE, etc.)
            cycle_enabled: Enable automatic profile switching after inventories
            mouse_profile: Optional mouse activity profile
            camera_profile: Optional camera movement profile
            custom_config: Optional dict to override profile settings
                          Format: {"timing": {...}, "mouse": {...}, etc.}

        Example (DEPRECATED - still works):
            manager = BehaviorManager(bot, profile="active")

        Example (RECOMMENDED):
            from utilities.behavior.profiles import ActivityProfile
            manager = BehaviorManager(bot, activity_profile=ActivityProfile.SKILLING_ACTIVE)

        Example (With cycle):
            manager = BehaviorManager(
                bot,
                activity_profile=ActivityProfile.BANK_STANDING_ACTIVE,
                cycle_enabled=True
            )
        """
        self.bot = bot

        # Determine which profile system to use
        if activity_profile is not None:
            # New activity profile system
            self._activity_profile = activity_profile
            self.profile_name = activity_profile.value
            profile_config = ACTIVITY_PROFILE_CONFIGS[activity_profile].copy()

            # Store for later logging (controller not ready during __init__)
            self._pending_init_log = True
        else:
            # Legacy profile system
            self._activity_profile = None
            self.profile_name = profile
            profile_config = BehaviorProfiles.get(profile)
            self._pending_init_log = False

        # Cycle management
        self.cycle_enabled = cycle_enabled
        self._inventory_count = 0

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

    def _log_init_if_pending(self) -> None:
        """
        Log initialization info if it hasn't been logged yet.

        This is called on first inventory complete or can be called manually.
        We defer init logging because controller isn't ready during __init__.
        """
        if not self._pending_init_log or self.bot is None:
            return

        if not hasattr(self.bot, "controller") or self.bot.controller is None:
            return

        self._pending_init_log = False

        if self._activity_profile is not None:
            profile_info = ACTIVITY_PROFILE_CONFIGS[self._activity_profile]
            self.bot.log_msg("=" * 60)
            self.bot.log_msg("[BEHAVIOR] PROFILE INITIALIZED")
            self.bot.log_msg("=" * 60)
            self.bot.log_msg(f"Profile: {profile_info['name']}")
            self.bot.log_msg(f"Description: {profile_info['description']}")
            self.bot.log_msg(f"Speed: {profile_info['timing']['speed_multiplier']}x")
            self.bot.log_msg(
                f"Cycling: {'ENABLED' if self.cycle_enabled else 'DISABLED'}"
            )
            if self.cycle_enabled:
                switch_chance = profile_info.get("cycle_switch_chance", 0.05)
                self.bot.log_msg(
                    f"Switch chance: {switch_chance * 100:.1f}% per inventory"
                )
            self.bot.log_msg(
                f"Tab-out: {'ENABLED' if profile_info['attention']['tab_out_enabled'] else 'DISABLED'}"
            )
            self.bot.log_msg(
                f"Bank check: {'ENABLED' if profile_info['attention']['bank_check_enabled'] else 'DISABLED'}"
            )
            self.bot.log_msg("=" * 60)

    def on_inventory_complete(self) -> None:
        """
        Called by bot when inventory cycle completes.

        This triggers cycle management logic:
        1. Increments inventory counter
        2. Probabilistically decides if profile should switch
        3. If switching, selects next profile using weighted random
        4. Reconfigures all modules with new profile

        Example:
            # In bot's main loop
            if inventory_full and banked:
                self.behavior.on_inventory_complete()  # May switch profile
        """
        # Log initialization on first call (controller is ready now)
        self._log_init_if_pending()

        if not self.cycle_enabled or self._activity_profile is None:
            return

        self._inventory_count += 1

        # Log inventory completion
        if self.bot is not None:
            self.bot.log_msg(f"[Cycle] Inventory #{self._inventory_count} complete")

        # Check if we should switch profiles
        if self._should_switch_profile():
            new_profile = self._select_next_profile()
            if new_profile != self._activity_profile:
                if self.bot is not None:
                    self.bot.log_msg(
                        f"[Cycle] Profile switch triggered (random chance)"
                    )
                self.switch_to_profile(new_profile)
            else:
                if self.bot is not None:
                    self.bot.log_msg(
                        f"[Cycle] Switch rolled but stayed on same profile"
                    )
        else:
            if self.bot is not None:
                profile_info = ACTIVITY_PROFILE_CONFIGS[self._activity_profile]
                switch_chance = profile_info.get("cycle_switch_chance", 0.05)
                self.bot.log_msg(
                    f"[Cycle] No switch this inventory ({switch_chance * 100:.1f}% chance)"
                )

    def _should_switch_profile(self) -> bool:
        """
        Determine if profile should switch based on cycle chance.

        Returns:
            True if profile should switch
        """
        if self._activity_profile is None:
            return False

        # Get switch probability from current profile config
        switch_chance = self.config.get("cycle_switch_chance", 0.05)

        # Probabilistic switch
        import utilities.random_util as rd

        return rd.random_chance(switch_chance)

    def _select_next_profile(self) -> ActivityProfile:
        """
        Select next profile using weighted random selection.

        Uses the cycle_weights from current profile config to determine
        which profile to switch to.

        Returns:
            Next ActivityProfile to switch to
        """
        if self._activity_profile is None:
            return ActivityProfile.SKILLING_ACTIVE

        # Get weights from current profile
        weights_dict = self.config.get("cycle_weights", {})

        if not weights_dict:
            # No weights defined, stay on current profile
            return self._activity_profile

        # Convert to lists for random.choices
        profiles = []
        weights = []

        for profile_name, weight in weights_dict.items():
            try:
                # Convert string name to ActivityProfile enum
                profile = ActivityProfile(profile_name)
                profiles.append(profile)
                weights.append(weight)
            except ValueError:
                # Invalid profile name, skip
                continue

        if not profiles:
            return self._activity_profile

        # Weighted random selection
        selected = random.choices(profiles, weights=weights, k=1)[0]
        return selected

    def switch_to_profile(self, new_profile: ActivityProfile) -> None:
        """
        Switch to a new activity profile.

        Reconfigures all behavior modules with the new profile settings.

        Args:
            new_profile: ActivityProfile to switch to

        Example:
            from utilities.behavior.profiles import ActivityProfile
            self.behavior.switch_to_profile(ActivityProfile.BANK_STANDING_AFK)
        """
        if new_profile == self._activity_profile:
            return  # Already on this profile

        old_profile_name = (
            self._activity_profile.value if self._activity_profile else "unknown"
        )
        self._activity_profile = new_profile
        self.profile_name = new_profile.value

        # Load new profile config
        profile_config = ACTIVITY_PROFILE_CONFIGS[new_profile].copy()
        self.config = profile_config

        # Reconfigure all modules
        self.timing.config = profile_config.get("timing", {})
        self.mouse.config = profile_config.get("mouse", {})
        self.action.config = profile_config.get("action", {})
        self.attention.config = profile_config.get("attention", {})

        # Reset attention intervals for new profile
        self.attention._tab_out_interval = self.attention._random_interval("tab_out")
        self.attention._bank_check_interval = self.attention._random_interval(
            "bank_check"
        )
        self.attention._skill_interval = self.attention._random_interval("skill_check")
        self.attention._mouse_interval = self.attention._random_interval(
            "mouse_movement"
        )
        self.attention._inventory_interval = self.attention._random_interval(
            "inventory_check"
        )

        self.breaks.config = profile_config.get("breaks", {})

        # Log the switch with detailed info
        if self.bot is not None:
            new_profile_info = ACTIVITY_PROFILE_CONFIGS[new_profile]
            self.bot.log_msg("=" * 60)
            self.bot.log_msg(f"[BEHAVIOR] PROFILE SWITCHED")
            self.bot.log_msg("=" * 60)
            self.bot.log_msg(f"Old: {old_profile_name}")
            self.bot.log_msg(f"New: {new_profile.value} - {new_profile_info['name']}")
            self.bot.log_msg(
                f"Speed: {new_profile_info['timing']['speed_multiplier']}x"
            )
            self.bot.log_msg(
                f"Tab-out: {'ENABLED' if new_profile_info['attention']['tab_out_enabled'] else 'DISABLED'}"
            )
            self.bot.log_msg(
                f"Bank check: {'ENABLED' if new_profile_info['attention']['bank_check_enabled'] else 'DISABLED'}"
            )
            self.bot.log_msg(f"Total switches: {self.stats['profile_switches'] + 1}")
            self.bot.log_msg("=" * 60)
        self.increment_stat("profile_switches")

    def get_current_profile(self) -> Optional[ActivityProfile]:
        """
        Get the current activity profile.

        Returns:
            Current ActivityProfile or None if using legacy profile
        """
        return self._activity_profile

    def log_profile_status(self) -> None:
        """
        Log detailed information about the current profile and stats.

        Useful for debugging or showing the user what profile is active.
        """
        # Log initialization if it hasn't been logged yet
        self._log_init_if_pending()

        if self.bot is None:
            return

        if self._activity_profile is None:
            self.bot.log_msg("Using legacy profile system")
            return

        profile_info = ACTIVITY_PROFILE_CONFIGS[self._activity_profile]

        self.bot.log_msg("=" * 60)
        self.bot.log_msg("[BEHAVIOR] PROFILE STATUS")
        self.bot.log_msg("=" * 60)
        self.bot.log_msg(f"Current Profile: {profile_info['name']}")
        self.bot.log_msg(f"Description: {profile_info['description']}")
        self.bot.log_msg(
            f"Speed Multiplier: {profile_info['timing']['speed_multiplier']}x"
        )
        self.bot.log_msg(f"Cycling: {'ENABLED' if self.cycle_enabled else 'DISABLED'}")
        if self.cycle_enabled:
            self.bot.log_msg(f"Inventories Completed: {self._inventory_count}")
            self.bot.log_msg(
                f"Profile Switches: {self.stats.get('profile_switches', 0)}"
            )
        self.bot.log_msg(
            f"Tab-out: {'ENABLED' if profile_info['attention']['tab_out_enabled'] else 'DISABLED'}"
        )
        if self.stats.get("tab_out", 0) > 0:
            self.bot.log_msg(f"  Tab-outs: {self.stats['tab_out']}")
        self.bot.log_msg(
            f"Bank Check: {'ENABLED' if profile_info['attention']['bank_check_enabled'] else 'DISABLED'}"
        )
        if self.stats.get("bank_check", 0) > 0:
            self.bot.log_msg(f"  Bank checks: {self.stats['bank_check']}")
        self.bot.log_msg("=" * 60)

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

        # Random startup delay (1-5s) to feel more natural - moved to background thread
        startup_delay = random.uniform(1.0, 5.0)

        self._fidget_stop_event = threading.Event()
        self._fidget_thread = threading.Thread(
            target=self._fidget_loop,
            args=(bot, startup_delay),
            daemon=True,
            name="MouseFidget",
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

    def _fidget_loop(self, bot, startup_delay: float = 0.0) -> None:
        """
        Background loop for continuous mouse fidgeting.
        Runs until stop_fidgeting() is called.
        Pauses when _fidget_paused is True.

        Args:
            bot: Bot instance for mouse control
            startup_delay: Delay before first fidget (non-blocking in background)
        """
        import utilities.random_util as rd

        # Sleep for startup delay in background (non-blocking)
        if startup_delay > 0:
            slept = 0.0
            while slept < startup_delay and not self._fidget_stop_event.is_set():
                time.sleep(0.5)
                slept += 0.5
            if self._fidget_stop_event.is_set():
                return

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
