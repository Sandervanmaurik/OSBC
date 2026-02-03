"""Base classes for behavior modules."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from model.bot import Bot


class BaseBehaviorModule(ABC):
    """
    Base class for all behavior modules.

    Each behavior module handles a specific aspect of human-like behavior
    (timing, mouse movement, attention patterns, etc.) and can be configured
    independently.

    Attributes:
        config: Configuration dictionary for this module
        bot: Reference to the bot using this module
        enabled: Whether this module is currently active
    """

    def __init__(self, config: Dict[str, Any], bot: "Bot"):
        """
        Initialize the behavior module.

        Args:
            config: Configuration dictionary specific to this module
            bot: The bot instance that will use this module
        """
        self.config = self._merge_with_defaults(config)
        self.bot = bot
        self.enabled = True

    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """
        Return default configuration for this module.

        Returns:
            Dictionary of default configuration values
        """
        pass

    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge provided config with defaults.

        Args:
            config: User-provided configuration

        Returns:
            Merged configuration with defaults filled in
        """
        defaults = self.get_default_config()
        merged = defaults.copy()
        merged.update(config)
        return merged

    def enable(self) -> None:
        """Enable this behavior module."""
        self.enabled = True

    def disable(self) -> None:
        """Disable this behavior module."""
        self.enabled = False

    def is_enabled(self) -> bool:
        """Check if this module is enabled."""
        return self.enabled

    def update_config(self, **kwargs) -> None:
        """
        Update configuration values.

        Args:
            **kwargs: Configuration key-value pairs to update
        """
        self.config.update(kwargs)
