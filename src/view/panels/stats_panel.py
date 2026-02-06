"""
StatsPanel - Right panel containing Skills, Current Action, and XP Gained.
Composes existing SkillsFrame with new CurrentActionCard and XPGainedList.
"""

import customtkinter
from view.skills_frame import SkillsFrame
from view.components.current_action_card import CurrentActionCard
from view.components.xp_gained_list import XPGainedList


class StatsPanel(customtkinter.CTkFrame):
    """
    Right panel containing:
        - Skills grid (top, reused from SkillsFrame)
        - Current Action card (middle)
        - XP Gained list (bottom, expandable)
    """

    def __init__(self, parent):
        """
        Args:
            parent: Parent widget
        """
        super().__init__(parent, fg_color="#1A1A1A", corner_radius=0)

        # Configure layout
        self.rowconfigure(0, weight=0)  # Section header
        self.rowconfigure(1, weight=0)  # Skills frame (fixed height)
        self.rowconfigure(2, weight=0)  # Section header
        self.rowconfigure(3, weight=0)  # Current Action card (small)
        self.rowconfigure(4, weight=0)  # Section header
        self.rowconfigure(5, weight=1)  # XP Gained list (expandable)
        self.columnconfigure(0, weight=1)

        # --- Skills Section ---
        self.lbl_skills_header = customtkinter.CTkLabel(
            self,
            text="SKILLS",
            font=("Roboto Medium", 11),
            text_color="#A0A0A0",
            anchor="w",
        )
        self.lbl_skills_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))

        self.skills_frame = SkillsFrame(parent=self)
        self.skills_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        # --- Current Action Section ---
        self.lbl_action_header = customtkinter.CTkLabel(
            self,
            text="CURRENT ACTION",
            font=("Roboto Medium", 11),
            text_color="#A0A0A0",
            anchor="w",
        )
        self.lbl_action_header.grid(row=2, column=0, sticky="ew", padx=15, pady=(10, 5))

        self.action_card = CurrentActionCard(parent=self)
        self.action_card.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

        # --- XP Gained Section ---
        self.lbl_xp_header = customtkinter.CTkLabel(
            self,
            text="XP GAINED",
            font=("Roboto Medium", 11),
            text_color="#A0A0A0",
            anchor="w",
        )
        self.lbl_xp_header.grid(row=4, column=0, sticky="ew", padx=15, pady=(10, 5))

        self.xp_gained_list = XPGainedList(parent=self)
        self.xp_gained_list.grid(row=5, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def get_skills_frame(self):
        """
        Get the SkillsFrame for controller binding.

        Returns:
            SkillsFrame instance
        """
        return self.skills_frame

    def clear_xp_gained(self):
        """Clear the XP Gained list (useful for session reset)."""
        self.xp_gained_list.clear()
