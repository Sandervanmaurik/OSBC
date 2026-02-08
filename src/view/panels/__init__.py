"""
Panel containers for the Auto-OSBC application.
"""

from .stats_panel import StatsPanel
from .script_panel import ScriptPanel
from .welcome_panel import WelcomePanel
from .chain_builder_panel import ChainBuilderPanel
from .chain_execution_panel import ChainExecutionPanel

__all__ = [
    "StatsPanel",
    "ScriptPanel",
    "WelcomePanel",
    "ChainBuilderPanel",
    "ChainExecutionPanel",
]
