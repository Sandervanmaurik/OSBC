"""
CurrentActionCard - Compact card displaying the current bot action.
Subscribes to BotSessionState for real-time updates.
"""

import customtkinter
from model.bot_session_state import BotSessionState
from view.fonts.fonts import *


class CurrentActionCard(customtkinter.CTkFrame):
    """
    A small card displaying the current bot action.
    Updates in real-time by subscribing to BotSessionState.
    """

    def __init__(self, parent):
        """
        Args:
            parent: Parent widget
        """
        super().__init__(parent, fg_color="#2E2E2E", corner_radius=8)

        # Configure layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)

        # Title label
        self.lbl_title = customtkinter.CTkLabel(
            self,
            text="Current Action",
            font=("Roboto Medium", 12),
            text_color="#A0A0A0",
            anchor="w",
        )
        self.lbl_title.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 5))

        # Action value label
        self.lbl_action = customtkinter.CTkLabel(
            self,
            text="Idle",
            font=("Roboto", 14),
            text_color="#DCE4EE",
            anchor="w",
        )
        self.lbl_action.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))

        # Subscribe to bot state changes
        BotSessionState().add_observer(self._on_bot_state_changed)

        # Initialize with current state
        self._update_action()

    def _on_bot_state_changed(self, property_name=None, value=None):
        """
        Observer callback for BotSessionState changes.
        Updates action display when current_action changes.
        """
        if property_name is None or property_name == "current_action":
            # Schedule UI update on main thread (thread-safe for Tkinter)
            self.after_idle(self._update_action)

    def _update_action(self):
        """
        Update the action text from BotSessionState.
        Must be called from main thread.
        """
        state = BotSessionState()
        action_text = state.current_action if state.current_action else "Idle"
        self.lbl_action.configure(text=action_text)
