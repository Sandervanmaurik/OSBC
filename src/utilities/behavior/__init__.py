"""
Modular human-like behavior system for bots.

This package provides a flexible, configurable system for adding realistic
human-like behaviors to bots. Behaviors are organized into modules that can
be independently configured and enabled/disabled per bot.

Quick Start:
    from utilities.behavior import BehaviorManager, BehaviorProfiles

    # In your bot's __init__:
    self.behavior = BehaviorManager(
        bot=self,
        profile="experienced"  # or "cautious", "focused"
    )

    # In your bot code:
    self.behavior.timing.sleep("short")
    self.behavior.mouse.move_to(target)
    if self.behavior.action.should_misclick():
        self.behavior.action.execute_misclick(target)

Modules:
    - timing: Sleep patterns, delays, reaction times
    - mouse: Mouse movement behaviors
    - action: Action execution patterns (misclicks, hesitation)
    - attention: Random attention behaviors (camera, skill checks)
    - breaks: Break timing and patterns

Profiles:
    - cautious: Slower, more deliberate. Maximum human-like behavior.
    - experienced: Balanced, efficient gameplay. (Recommended)
    - focused: Fast, minimal distractions. Good for short sessions.
"""

from utilities.behavior.manager import BehaviorManager
from utilities.behavior.profiles import BehaviorProfiles
from utilities.behavior.config import BehaviorConfig

__all__ = [
    "BehaviorManager",
    "BehaviorProfiles",
    "BehaviorConfig",
]
