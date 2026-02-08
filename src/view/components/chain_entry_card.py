"""
ChainEntryCard - A card representing a single script in the chain builder.

Displays script icon, name, duration, and controls (configure, delete, reorder).
"""

import customtkinter
from typing import Callable, Optional
from model.chain import ChainEntry


class ChainEntryCard(customtkinter.CTkFrame):
    """
    A card widget for displaying and managing a chain entry.

    Layout: [Icon] Script Name | Duration | [Configure] [Delete] [↑] [↓]
    """

    def __init__(
        self,
        parent,
        entry: ChainEntry,
        on_configure: Optional[Callable[[ChainEntry], None]] = None,
        on_delete: Optional[Callable[[ChainEntry], None]] = None,
        on_move_up: Optional[Callable[[ChainEntry], None]] = None,
        on_move_down: Optional[Callable[[ChainEntry], None]] = None,
    ):
        """
        Args:
            parent: Parent widget
            entry: The ChainEntry this card represents
            on_configure: Callback when Configure button clicked
            on_delete: Callback when Delete button clicked
            on_move_up: Callback when Up button clicked
            on_move_down: Callback when Down button clicked
        """
        super().__init__(
            parent,
            fg_color=("#E0E0E0", "#2E2E2E"),
            corner_radius=6,
            border_width=1,
            border_color=("#CCCCCC", "#3A3A3A"),
        )

        self.entry = entry
        self.on_configure = on_configure
        self.on_delete = on_delete
        self.on_move_up = on_move_up
        self.on_move_down = on_move_down

        # Configure grid
        self.grid_columnconfigure(0, weight=0)  # Icon/Name
        self.grid_columnconfigure(1, weight=0)  # Duration
        self.grid_columnconfigure(2, weight=1)  # Spacer
        self.grid_columnconfigure(3, weight=0)  # Configure button
        self.grid_columnconfigure(4, weight=0)  # Delete button
        self.grid_columnconfigure(5, weight=0)  # Up button
        self.grid_columnconfigure(6, weight=0)  # Down button

        # Script name label
        self.lbl_script = customtkinter.CTkLabel(
            self,
            text=self._format_script_name(entry.script_name),
            font=("Roboto Medium", 13),
            text_color=("#2C2C2C", "#DCE4EE"),
            anchor="w",
        )
        self.lbl_script.grid(row=0, column=0, sticky="w", padx=(10, 15), pady=8)

        # Duration label
        self.lbl_duration = customtkinter.CTkLabel(
            self,
            text=f"{entry.running_time} min",
            font=("Roboto", 12),
            text_color=("#555555", "#A0A0A0"),
            width=60,
        )
        self.lbl_duration.grid(row=0, column=1, sticky="w", padx=5, pady=8)

        # Configure button
        self.btn_configure = customtkinter.CTkButton(
            self,
            text="⚙",
            command=self._on_configure_clicked,
            width=30,
            height=28,
            fg_color=("#4A90E2", "#3A7BC8"),
            hover_color=("#5AA0F2", "#4A8BD8"),
            font=("Roboto", 14),
        )
        self.btn_configure.grid(row=0, column=3, padx=3, pady=4)

        # Delete button
        self.btn_delete = customtkinter.CTkButton(
            self,
            text="🗑",
            command=self._on_delete_clicked,
            width=30,
            height=28,
            fg_color=("#E74C3C", "#C0392B"),
            hover_color=("#F55C4C", "#D0493B"),
            font=("Roboto", 14),
        )
        self.btn_delete.grid(row=0, column=4, padx=3, pady=4)

        # Up button
        self.btn_up = customtkinter.CTkButton(
            self,
            text="↑",
            command=self._on_move_up_clicked,
            width=30,
            height=28,
            fg_color=("#95A5A6", "#7F8C8D"),
            hover_color=("#A5B5B6", "#8F9C9D"),
            font=("Roboto", 14),
        )
        self.btn_up.grid(row=0, column=5, padx=3, pady=4)

        # Down button
        self.btn_down = customtkinter.CTkButton(
            self,
            text="↓",
            command=self._on_move_down_clicked,
            width=30,
            height=28,
            fg_color=("#95A5A6", "#7F8C8D"),
            hover_color=("#A5B5B6", "#8F9C9D"),
            font=("Roboto", 14),
        )
        self.btn_down.grid(row=0, column=6, padx=(3, 10), pady=4)

    def _format_script_name(self, script_name: str) -> str:
        """Format script name for display (remove OSRS prefix, add icon)."""
        # Remove "OSRS" prefix if present
        display_name = script_name.replace("OSRS", "").strip()

        # Map to icons based on common bot names
        icon_map = {
            "Fishing": "🎣",
            "Mining": "⛏️",
            "Woodcutting": "🪓",
            "Cooking": "🍳",
            "Crafting": "🔨",
            "Fletching": "🏹",
            "Smithing": "⚒️",
            "Firemaking": "🔥",
        }

        icon = icon_map.get(display_name, "📜")
        return f"{icon} {display_name}"

    def _on_configure_clicked(self):
        """Handle Configure button click."""
        if self.on_configure:
            self.on_configure(self.entry)

    def _on_delete_clicked(self):
        """Handle Delete button click."""
        if self.on_delete:
            self.on_delete(self.entry)

    def _on_move_up_clicked(self):
        """Handle Up button click."""
        if self.on_move_up:
            self.on_move_up(self.entry)

    def _on_move_down_clicked(self):
        """Handle Down button click."""
        if self.on_move_down:
            self.on_move_down(self.entry)

    def update_entry(self, entry: ChainEntry):
        """Update the displayed entry."""
        self.entry = entry
        self.lbl_script.configure(text=self._format_script_name(entry.script_name))
        self.lbl_duration.configure(text=f"{entry.running_time} min")

    def set_button_states(self, can_move_up: bool, can_move_down: bool):
        """Enable/disable up/down buttons based on position."""
        self.btn_up.configure(state="normal" if can_move_up else "disabled")
        self.btn_down.configure(state="normal" if can_move_down else "disabled")
