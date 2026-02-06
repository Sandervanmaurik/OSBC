"""
CollapsibleSidebar - Collapsible menu with script buttons.
Contains toggle button, scrollable script list, and settings button.
"""

import pathlib
import customtkinter
from PIL import Image
from typing import Dict, Callable, Optional, Any


class CollapsibleSidebar(customtkinter.CTkFrame):
    """
    A collapsible sidebar menu for script selection.

    Layout:
        - Top: Toggle button (expand/collapse)
        - Middle: Scrollable frame with ScriptMenuButton widgets
        - Bottom: Settings button

    States:
        - Expanded: 180px width, shows icon + text
        - Collapsed: 50px width, shows icon only
    """

    def __init__(
        self,
        parent,
        on_toggle: Optional[Callable[[bool], None]] = None,
        on_settings: Optional[Callable[[], None]] = None,
    ):
        """
        Args:
            parent: Parent widget
            on_toggle: Callback when sidebar is toggled (receives is_collapsed bool)
            on_settings: Callback when settings button is clicked
        """
        super().__init__(parent, fg_color="#242424", corner_radius=0)

        self.on_toggle_callback = on_toggle
        self.on_settings_callback = on_settings
        self.is_collapsed = False

        # Store script buttons for toggle updates
        self.script_buttons: Dict[str, Any] = {}  # {script_id: ScriptMenuButton}

        # Configure layout
        self.rowconfigure(0, weight=0)  # Toggle button
        self.rowconfigure(1, weight=1)  # Script list (expandable)
        self.rowconfigure(2, weight=0)  # Settings button
        self.columnconfigure(0, weight=1)

        # Load icons
        PATH = pathlib.Path(__file__).parent.parent.parent.resolve()

        # Toggle icon (we'll use a simple arrow text for now, or could load an icon)
        # Using text arrows: "◀" (collapsed), "▶" (expanded)

        self.collapse_icon = customtkinter.CTkImage(
            light_image=Image.open(PATH / "images" / "ui" / "options2.png"),
            dark_image=Image.open(PATH / "images" / "ui" / "options2.png"),
            size=(20, 20),
        )

        self.settings_icon = customtkinter.CTkImage(
            light_image=Image.open(PATH / "images" / "ui" / "options2.png"),
            dark_image=Image.open(PATH / "images" / "ui" / "options2.png"),
            size=(20, 20),
        )

        # Top: Toggle button
        self.btn_toggle = customtkinter.CTkButton(
            self,
            text="☰",  # Menu icon
            command=self._toggle_sidebar,
            width=160,
            height=40,
            fg_color="#2E2E2E",
            hover_color="#3A3A3A",
            font=("Roboto", 18),
            corner_radius=6,
        )
        self.btn_toggle.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Middle: Scrollable frame for script buttons
        self.scripts_frame = customtkinter.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color="#2E2E2E",
            scrollbar_button_hover_color="#3A3A3A",
        )
        self.scripts_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.scripts_frame.columnconfigure(0, weight=1)

        # Bottom: Settings button
        self.btn_settings = customtkinter.CTkButton(
            self,
            text="⚙",  # Settings icon
            image=None,  # Could use settings_icon if available
            command=self._on_settings_clicked,
            width=160,
            height=40,
            fg_color="#2E2E2E",
            hover_color="#3A3A3A",
            font=("Roboto", 18),
            corner_radius=6,
        )
        self.btn_settings.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")

    def add_script_button(self, script_id: str, button_widget):
        """
        Add a ScriptMenuButton to the sidebar.

        Args:
            script_id: Unique identifier for the script
            button_widget: ScriptMenuButton instance
        """
        button_widget.pack(fill="x", pady=3)
        self.script_buttons[script_id] = button_widget

    def remove_script_button(self, script_id: str):
        """
        Remove a script button from the sidebar.

        Args:
            script_id: Unique identifier for the script
        """
        if script_id in self.script_buttons:
            self.script_buttons[script_id].destroy()
            del self.script_buttons[script_id]

    def clear_script_buttons(self):
        """Remove all script buttons."""
        for button in self.script_buttons.values():
            button.destroy()
        self.script_buttons.clear()

    def _toggle_sidebar(self):
        """Toggle between expanded and collapsed states."""
        self.is_collapsed = not self.is_collapsed
        self._update_sidebar_width()

        # Update all script buttons
        for button in self.script_buttons.values():
            button.set_collapsed(self.is_collapsed)

        # Update toggle and settings buttons
        if self.is_collapsed:
            self.btn_toggle.configure(text="☰", width=40)
            self.btn_settings.configure(text="⚙", width=40)
        else:
            self.btn_toggle.configure(text="☰", width=160)
            self.btn_settings.configure(text="⚙", width=160)

        # Notify parent
        if self.on_toggle_callback:
            self.on_toggle_callback(self.is_collapsed)

    def _update_sidebar_width(self):
        """Update the sidebar's min/max width based on collapsed state."""
        if self.is_collapsed:
            self.configure(width=50)
        else:
            self.configure(width=180)

    def _on_settings_clicked(self):
        """Handle settings button click."""
        if self.on_settings_callback:
            self.on_settings_callback()

    def set_script_selected(self, script_id: str, selected: bool = True):
        """
        Highlight a script button as selected.

        Args:
            script_id: Unique identifier for the script
            selected: True to highlight, False to reset
        """
        # Reset all buttons first
        for sid, button in self.script_buttons.items():
            is_selected = sid == script_id and selected
            button.set_selected(is_selected)

    def get_scripts_frame(self):
        """
        Get the scrollable frame for adding script buttons.

        Returns:
            The scripts_frame widget
        """
        return self.scripts_frame
