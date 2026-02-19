"""
CurrentActionCard - Compact card displaying the current bot action and XP/hour rate.
Subscribes to BotSessionState for real-time updates.
"""

import customtkinter
from model.bot_session_state import BotSessionState
from view.fonts.fonts import *


class CurrentActionCard(customtkinter.CTkFrame):
    """
    A small card displaying the current bot action and XP/hour rate.
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
        self.rowconfigure(2, weight=0)

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
        self.lbl_action.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 5))

        # XP/Hour label
        self.lbl_xp_hour = customtkinter.CTkLabel(
            self,
            text="XP/Hour: 0",
            font=("Roboto", 12),
            text_color="#90A0B0",
            anchor="w",
        )
        self.lbl_xp_hour.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))

        # Subscribe to bot state changes
        BotSessionState().add_observer(self._on_bot_state_changed)

        # Initialize with current state
        self._update_display()

        # Start periodic updates for XP/hour (updates every 2 seconds)
        self._update_xp_hour_periodically()

    def _on_bot_state_changed(self, property_name=None, value=None):
        """
        Observer callback for BotSessionState changes.
        Updates action and XP/hour display.
        """
        # Schedule UI update on main thread (thread-safe for Tkinter)
        self.after_idle(self._update_display)

    def _update_xp_hour_periodically(self):
        """
        Periodically update XP/hour display (every 2 seconds).
        This ensures XP/hour updates even when no XP events occur.
        """
        # Update XP/hour only (action is updated via observer)
        state = BotSessionState()
        xp_per_hour = state.get_xp_per_hour()
        self.lbl_xp_hour.configure(text=f"XP/Hour: {xp_per_hour:,}")

        # Schedule next update in 2000ms (2 seconds)
        self.after(2000, self._update_xp_hour_periodically)

    def _update_display(self):
        """
        Update the action text and XP/hour from BotSessionState.
        Must be called from main thread.
        """
        state = BotSessionState()

        # Update action text
        action_text = state.current_action if state.current_action else "Idle"
        self.lbl_action.configure(text=action_text)

        # Update XP/hour
        xp_per_hour = state.get_xp_per_hour()
        self.lbl_xp_hour.configure(text=f"XP/Hour: {xp_per_hour:,}")
