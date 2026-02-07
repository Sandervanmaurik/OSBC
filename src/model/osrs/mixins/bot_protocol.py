"""
Protocol definitions for OSRS bot mixins.

This file defines the interface that bots must implement for mixins to work.
Using Protocol allows type checkers (mypy) to verify that mixins have access
to required methods without creating circular dependencies.
"""

from typing import Protocol, Optional, List, runtime_checkable, TYPE_CHECKING
from utilities.geometry import Rectangle
import utilities.color as clr
from model.bot import BotStatus
from model.runelite_bot import RuneLiteObject

if TYPE_CHECKING:
    from utilities.behavior.manager import BehaviorManager
    from model.runelite_bot import RuneLiteWindow


@runtime_checkable
class BotProtocol(Protocol):
    """
    Protocol defining the interface that bot classes must provide for mixins.

    This allows type checkers to verify that mixins can safely call methods
    on self, even though the mixin doesn't directly inherit from the bot class.

    Required Dependencies for Mixins:
    - BehaviorManager: Provides timing, randomization, fidgeting control
    - RuneLiteWindow: Provides game window geometry and UI element access
    - BotStatus: Current bot state (RUNNING, STOPPED, etc.)
    - log_msg: Logging capability
    - Safe key operations: For keyboard input
    - RuneLite object detection: For game object interaction
    - Visual detection: For inventory/bank item finding
    """

    # Required attributes
    behavior: "BehaviorManager"
    win: "RuneLiteWindow"
    status: BotStatus

    # Logging
    def log_msg(self, msg: str, overwrite: bool = False) -> None:
        """Log a message to the bot's log."""
        ...

    # Safe key operations
    def _safe_key_press(self, key: str) -> bool:
        """Press a key safely (checks window focus)."""
        ...

    def _safe_key_down(self, key: str) -> bool:
        """Hold a key down safely."""
        ...

    def _safe_key_up(self, key: str) -> bool:
        """Release a key safely."""
        ...

    # RuneLite-specific methods
    def get_nearest_tag(self, color: clr.Color) -> Optional[RuneLiteObject]:
        """Get nearest tagged object by color."""
        ...

    def mouseover_text(
        self, contains: Optional[List[str]] = None, exact: Optional[List[str]] = None
    ) -> bool:
        """Check mouseover text."""
        ...

    # Inventory methods
    def find_item_in_inventory_visual(
        self,
        item_template_path: str,
        confidence: float = 0.8,
        crop_bottom_portion: float = 0.7,
    ) -> List[int]:
        """Find item slots in inventory using template matching."""
        ...

    def find_item_in_bank_visual(
        self,
        item_template_path: str,
        confidence: float = 0.3,
        crop_bottom_portion: float = 0.7,
    ) -> Optional[tuple[Rectangle, int]]:
        """Find item in bank using template matching."""
        ...
