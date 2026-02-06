"""
ScriptMenuButton - Individual script button for the collapsible sidebar menu.
Displays skill icon + script name (or icon only when collapsed).
"""

import pathlib
import customtkinter
from PIL import Image


class ScriptMenuButton(customtkinter.CTkButton):
    """
    A button representing a single script in the sidebar menu.
    Shows the script's primary skill icon and name.
    Supports expanded (icon + text) and collapsed (icon only) states.
    """

    def __init__(
        self,
        parent,
        script_name: str,
        primary_skill: str,
        command,
        is_collapsed: bool = False,
    ):
        """
        Args:
            parent: Parent widget
            script_name: Display name of the script (e.g., "Fishing")
            primary_skill: Skill name for icon (e.g., "fishing")
            command: Callback when button is clicked
            is_collapsed: Whether sidebar is in collapsed state
        """
        self.script_name = script_name
        self.primary_skill = primary_skill
        self._is_collapsed = is_collapsed

        # Load skill icon
        self.icon_image = self._load_skill_icon(primary_skill)

        # Initialize button
        super().__init__(
            parent,
            text="" if is_collapsed else script_name,
            image=self.icon_image,
            command=command,
            width=40 if is_collapsed else 160,
            height=40,
            fg_color="#2E2E2E",
            hover_color="#3A3A3A",
            text_color="#DCE4EE",
            anchor="w" if not is_collapsed else "center",
            font=("Roboto", 13),
            compound="left",
            corner_radius=6,
        )

    def _load_skill_icon(self, skill_name: str):
        """Load the skill icon from the images directory."""
        try:
            PATH = pathlib.Path(__file__).parent.parent.parent.resolve()
            icon_path = PATH / "images" / "bot" / "skills" / f"{skill_name}.png"

            if icon_path.exists():
                return customtkinter.CTkImage(
                    light_image=Image.open(icon_path),
                    dark_image=Image.open(icon_path),
                    size=(20, 20),
                )
            else:
                # Fallback to a default icon if skill icon not found
                print(f"Warning: Skill icon not found: {icon_path}")
                return None
        except Exception as e:
            print(f"Error loading skill icon for {skill_name}: {e}")
            return None

    def set_collapsed(self, is_collapsed: bool):
        """
        Update button appearance based on collapsed state.

        Args:
            is_collapsed: True for icon-only, False for icon + text
        """
        self._is_collapsed = is_collapsed

        if is_collapsed:
            self.configure(
                text="",
                width=40,
                anchor="center",
            )
        else:
            self.configure(
                text=self.script_name,
                width=160,
                anchor="w",
            )

    def set_selected(self, is_selected: bool):
        """
        Highlight button when script is selected.

        Args:
            is_selected: True to highlight, False to reset
        """
        if is_selected:
            self.configure(fg_color="#4A90E2", hover_color="#5BA0F2")
        else:
            self.configure(fg_color="#2E2E2E", hover_color="#3A3A3A")
