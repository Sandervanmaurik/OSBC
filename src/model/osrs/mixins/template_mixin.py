"""
TemplateMixin - Unified template management for all OSRS bots.

Supports both static and dynamic template patterns:
- Static: Dict[str, Tuple[str, ...]] - e.g., cooking/fletching
- Dynamic: Dict[str, Callable[..., Tuple[str, ...]]] - e.g., crafting with lambdas

Provides path resolution with caching and validation.
"""

import os
from typing import Dict, Tuple, Callable, Union, Optional, TYPE_CHECKING
from functools import lru_cache

import utilities.imagesearch as imsearch


# Type alias for template specifications
TemplateSpec = Union[
    Tuple[str, ...],  # Static tuple: ("raw_shrimp.png", "cooked_shrimp.png")
    Callable[..., Tuple[str, ...]],  # Dynamic: lambda gem: (f"uncut_{gem}.png", ...)
]


class TemplateMixin:
    """
    Mixin providing unified template management for static and dynamic templates.

    Subclasses should override _define_item_templates() to provide their template mappings.

    This mixin can optionally use self.log_msg() for error logging if available.
    """

    # Type hint for optional log_msg method (provided by bot class)
    if TYPE_CHECKING:

        def log_msg(self, msg: str, overwrite: bool = False) -> None: ...


import os
from typing import Dict, Tuple, Callable, Union, Optional
from functools import lru_cache

import utilities.imagesearch as imsearch


# Type alias for template specifications
TemplateSpec = Union[
    Tuple[str, ...],  # Static tuple: ("raw_shrimp.png", "cooked_shrimp.png")
    Callable[..., Tuple[str, ...]],  # Dynamic: lambda gem: (f"uncut_{gem}.png", ...)
]


class TemplateMixin:
    """
    Mixin providing unified template management for static and dynamic templates.

    Subclasses should override _define_item_templates() to provide their template mappings.

    Example usage (static templates):
        def _define_item_templates(self) -> Dict[str, TemplateSpec]:
            return {
                "Raw shrimp": ("raw_shrimp.png", "cooked_shrimp.png"),
                "Raw salmon": ("raw_salmon.png", "cooked_salmon.png"),
            }

    Example usage (dynamic templates):
        def _define_item_templates(self) -> Dict[str, TemplateSpec]:
            return {
                "Cutting gems": lambda gem_type: (
                    "chisel.png",
                    f"uncut_{gem_type.lower()}.png",
                    f"{gem_type.lower()}.png",
                ),
            }
    """

    def _define_item_templates(self) -> Dict[str, TemplateSpec]:
        """
        Override this method to define bot-specific templates.

        Returns:
            Dictionary mapping method/item names to template specifications.
            Specifications can be static tuples or dynamic callables.
        """
        return {}

    def get_templates(self, method_key: str, **kwargs) -> Tuple[str, ...]:
        """
        Resolve templates for a given method, supporting both static and dynamic specs.

        Args:
            method_key: Key in the template dictionary (e.g., "Raw shrimp", "Cutting gems")
            **kwargs: Parameters for dynamic template functions (e.g., gem_type="Opal")

        Returns:
            Tuple of template filenames

        Raises:
            KeyError: If method_key not found in templates
            TypeError: If dynamic template called without required parameters

        Example:
            # Static
            templates = self.get_templates("Raw shrimp")  # ("raw_shrimp.png", "cooked_shrimp.png")

            # Dynamic
            templates = self.get_templates("Cutting gems", gem_type="Opal")
            # ("chisel.png", "uncut_opal.png", "opal.png")
        """
        template_defs = self._define_item_templates()

        if method_key not in template_defs:
            raise KeyError(f"No templates defined for method: {method_key}")

        spec = template_defs[method_key]

        # Check if it's a callable (dynamic template)
        if callable(spec):
            return spec(**kwargs)
        else:
            # Static tuple
            return spec

    @lru_cache(maxsize=128)
    def get_template_path(self, filename: str, category: str = "items") -> str:
        """
        Get full path to a template image with intelligent category routing.

        Args:
            filename: Template filename (e.g., "chisel.png")
            category: Default category if not auto-detected (default: "items")

        Returns:
            Full path to template file

        Note:
            Automatically routes certain filenames to appropriate categories:
            - "chisel.png" -> "tools"
            - Other tool-like names -> "tools"
            - Default -> "items"
        """
        # Auto-detect category based on filename
        detected_category = self._get_template_category(filename)
        if detected_category:
            category = detected_category

        return str(imsearch.get_template_path(category, filename))

    def _get_template_category(self, filename: str) -> Optional[str]:
        """
        Auto-detect template category based on filename.

        Args:
            filename: Template filename

        Returns:
            Category name if detected, None otherwise
        """
        # Tool detection heuristics
        tool_keywords = ["chisel", "knife", "needle", "hammer"]
        filename_lower = filename.lower()

        for keyword in tool_keywords:
            if keyword in filename_lower:
                return "tools"

        return None

    def validate_templates(self, method_key: str, **kwargs) -> bool:
        """
        Validate that all templates for a method exist on disk.

        Args:
            method_key: Key in the template dictionary
            **kwargs: Parameters for dynamic templates

        Returns:
            True if all templates exist, False otherwise

        Side effects:
            Logs missing template paths using self.log_msg if available
        """
        try:
            templates = self.get_templates(method_key, **kwargs)
        except (KeyError, TypeError) as e:
            if hasattr(self, "log_msg"):
                self.log_msg(f"Template validation error: {e}")
            return False

        missing = []
        for template_file in templates:
            path = self.get_template_path(template_file)
            if not os.path.exists(path):
                missing.append(path)

        if missing:
            if hasattr(self, "log_msg"):
                self.log_msg("=" * 60)
                self.log_msg("MISSING TEMPLATES - Cannot start bot")
                self.log_msg("=" * 60)
                self.log_msg(f"Method: {method_key}")
                if kwargs:
                    self.log_msg(f"Parameters: {kwargs}")
                self.log_msg("")
                self.log_msg("Missing template files:")
                for path in missing:
                    self.log_msg(f"  - {path}")
                self.log_msg("")
                self.log_msg("How to create templates:")
                self.log_msg("  1. Run manual_capture.py or recorder.py")
                self.log_msg("  2. Capture screenshots of the items in your inventory")
                self.log_msg(
                    "  3. Save them to the appropriate folder (items/, tools/, etc.)"
                )
                self.log_msg("=" * 60)
            return False

        return True
