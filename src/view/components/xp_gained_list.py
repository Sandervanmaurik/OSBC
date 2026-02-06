"""
XPGainedList - List of skills with XP gained, styled as skill cells.
Subscribes to BotSessionState for real-time XP tracking updates.
"""

import pathlib
import customtkinter
from PIL import Image
from model.bot_session_state import BotSessionState
from model.skills import SkillsManager
from utilities.osrs_skills import SKILL_ORDER


class XPGainedList(customtkinter.CTkScrollableFrame):
    """
    A scrollable list showing skills with XP gained during the session.
    Each entry is styled like a skill cell (icon + name + XP value).
    Dynamically creates/removes rows as XP is gained.
    """

    def __init__(self, parent):
        """
        Args:
            parent: Parent widget
        """
        super().__init__(
            parent,
            fg_color="#1A1A1A",
            corner_radius=0,
            scrollbar_button_color="#2E2E2E",
            scrollbar_button_hover_color="#3A3A3A",
        )

        # Path for skill icons
        self.PATH = pathlib.Path(__file__).parent.parent.parent.resolve()

        # Track created skill rows {skill_name: frame}
        self.skill_rows = {}

        # Subscribe to both BotSessionState (for XP tracking) and SkillsManager (for updates)
        BotSessionState().add_observer(self._on_session_changed)
        SkillsManager().add_observer(self._on_skills_changed)

        # Initial population
        self._update_xp_list()

    def _on_session_changed(self):
        """
        Observer callback for BotSessionState changes.
        Updates XP list when session state changes.
        """
        # Schedule UI update on main thread (thread-safe for Tkinter)
        self.after_idle(self._update_xp_list)

    def _on_skills_changed(self):
        """
        Observer callback for SkillsManager changes.
        Updates XP list when skills are updated.
        """
        # Schedule UI update on main thread (thread-safe for Tkinter)
        self.after_idle(self._update_xp_list)

    def _update_xp_list(self):
        """
        Update the XP gained list.
        Creates/removes skill rows based on xp_gained > 0.
        Must be called from main thread.
        """
        session_state = BotSessionState()

        # Determine which skills have gained XP using BotSessionState
        skills_with_xp = []
        for skill_name in SKILL_ORDER:
            xp_gained = session_state.get_xp_gained(skill_name)
            if xp_gained > 0:
                skills_with_xp.append((skill_name, xp_gained))

        # Remove skills that no longer have XP
        for skill_name in list(self.skill_rows.keys()):
            if skill_name not in [s[0] for s in skills_with_xp]:
                self.skill_rows[skill_name].destroy()
                del self.skill_rows[skill_name]

        # Create or update skills with XP
        for skill_name, xp_gained in skills_with_xp:
            if skill_name not in self.skill_rows:
                # Create new row
                self._create_skill_row(skill_name, xp_gained)
            else:
                # Update existing row
                self._update_skill_row(skill_name, xp_gained)

    def _create_skill_row(self, skill_name: str, xp_gained: int):
        """
        Create a new skill row (icon + name + XP).

        Args:
            skill_name: Name of the skill
            xp_gained: XP gained for this skill
        """
        # Row frame (styled like skill cell)
        row_frame = customtkinter.CTkFrame(
            self,
            fg_color="#2E2E2E",
            corner_radius=6,
            height=40,
        )
        row_frame.pack(fill="x", padx=8, pady=4)
        row_frame.pack_propagate(False)

        # Load skill icon
        icon_path = self.PATH / "images" / "bot" / "skills" / f"{skill_name}.png"
        skill_icon = None
        if icon_path.exists():
            skill_icon = customtkinter.CTkImage(
                light_image=Image.open(icon_path),
                dark_image=Image.open(icon_path),
                size=(20, 20),
            )

        # Icon label
        lbl_icon = customtkinter.CTkLabel(
            row_frame,
            text="",
            image=skill_icon,
            width=24,
        )
        lbl_icon.pack(side="left", padx=(8, 5))

        # Skill name label
        lbl_name = customtkinter.CTkLabel(
            row_frame,
            text=skill_name.capitalize(),
            font=("Roboto", 12),
            text_color="#DCE4EE",
            anchor="w",
        )
        lbl_name.pack(side="left", padx=5, fill="x", expand=True)

        # XP value label
        lbl_xp = customtkinter.CTkLabel(
            row_frame,
            text=f"+{xp_gained:,}",
            font=("Roboto Medium", 12),
            text_color="#4A90E2",
            anchor="e",
        )
        lbl_xp.pack(side="right", padx=8)

        # Store references
        self.skill_rows[skill_name] = row_frame
        row_frame.lbl_xp = lbl_xp  # Store XP label for updates

    def _update_skill_row(self, skill_name: str, xp_gained: int):
        """
        Update an existing skill row's XP value.

        Args:
            skill_name: Name of the skill
            xp_gained: Updated XP gained for this skill
        """
        row_frame = self.skill_rows.get(skill_name)
        if row_frame and hasattr(row_frame, "lbl_xp"):
            row_frame.lbl_xp.configure(text=f"+{xp_gained:,}")

    def clear(self):
        """Clear all skill rows (useful for session reset)."""
        for row_frame in self.skill_rows.values():
            row_frame.destroy()
        self.skill_rows.clear()
