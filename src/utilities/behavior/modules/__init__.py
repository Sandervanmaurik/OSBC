"""Behavior modules for the human-like behavior system."""

from utilities.behavior.modules.timing import TimingBehavior
from utilities.behavior.modules.mouse import MouseBehavior
from utilities.behavior.modules.action import ActionBehavior
from utilities.behavior.modules.attention import AttentionBehavior
from utilities.behavior.modules.breaks import BreakBehavior

__all__ = [
    "TimingBehavior",
    "MouseBehavior",
    "ActionBehavior",
    "AttentionBehavior",
    "BreakBehavior",
]
