"""
Mixins for OSRS bots - shared functionality across multiple bot types.

These mixins provide common operations for:
- Template management (static and dynamic)
- Banking operations
- Item interactions
- Action state detection

All mixins are designed to be inherited by OSRSBot, making them available
to all OSRS bots automatically.
"""

from .template_mixin import TemplateMixin
from .banking_mixin import BankingMixin
from .item_interaction_mixin import ItemInteractionMixin
from .action_waiting_mixin import ActionWaitingMixin

__all__ = [
    "TemplateMixin",
    "BankingMixin",
    "ItemInteractionMixin",
    "ActionWaitingMixin",
]
