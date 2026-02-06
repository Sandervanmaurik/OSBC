"""
XPGainedList - List of skills with XP gained, styled as skill cells.
Subscribes to BotSessionState for real-time XP tracking updates.
Displays both current (script run) and session (app lifetime) XP gains.
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

    def destroy(self) -> None:
        """Cleanup observers before destroying component."""
        BotSessionState().remove_observer(self._on_session_changed)
        SkillsManager().remove_observer(self._on_skills_changed)
        super().destroy()

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
        Creates/removes skill rows based on current xp_gained > 0.
        Session totals are still visible in the header.
        Must be called from main thread.
        """
        session_state = BotSessionState()

        # Determine which skills have gained XP in the current script run
        # (Session totals are shown in the header, so we only show active skills here)
        skills_with_xp = []
        for skill_name in SKILL_ORDER:
            current_xp = session_state.get_xp_gained(skill_name)
            session_xp = session_state.get_session_xp_gained(skill_name)

            # Only show row if the current script run has gained XP
            if current_xp > 0:
                skills_with_xp.append((skill_name, current_xp, session_xp))

        # Remove skills that no longer have XP
        for skill_name in list(self.skill_rows.keys()):
            if skill_name not in [s[0] for s in skills_with_xp]:
                self.skill_rows[skill_name].destroy()
                del self.skill_rows[skill_name]

        # Create or update skills with XP
        for skill_name, current_xp, session_xp in skills_with_xp:
            if skill_name not in self.skill_rows:
                # Create new row
                self._create_skill_row(skill_name, current_xp, session_xp)
            else:
                # Update existing row
                self._update_skill_row(skill_name, current_xp, session_xp)

    def _create_skill_row(self, skill_name: str, current_xp: int, session_xp: int):
        """
        Create a new skill row (icon + name + Current XP + Session XP).

        Args:
            skill_name: Name of the skill
            current_xp: XP gained in current script run
            session_xp: XP gained since app opened
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

        # Container for XP labels (right side)
        xp_container = customtkinter.CTkFrame(row_frame, fg_color="transparent")
        xp_container.pack(side="right", padx=8)

        # Current XP label (always shown)
        lbl_current_xp = customtkinter.CTkLabel(
            xp_container,
            text=f"+{current_xp:,}",
            font=("Roboto Medium", 11),
            text_color="#4A90E2",
            anchor="e",
        )
        lbl_current_xp.pack(side="left")

        # Session XP (only shown if different from current)
        lbl_divider = None
        lbl_session_xp = None
        if session_xp != current_xp:
            # Gray divider
            lbl_divider = customtkinter.CTkLabel(
                xp_container,
                text="│",
                font=("Roboto", 11),
                text_color="#666666",
                anchor="center",
            )
            lbl_divider.pack(side="left", padx=6)

            # Session XP label
            lbl_session_xp = customtkinter.CTkLabel(
                xp_container,
                text=f"+{session_xp:,}",
                font=("Roboto Medium", 11),
                text_color="#7A7A7A",  # Slightly muted to distinguish from current
                anchor="e",
            )
            lbl_session_xp.pack(side="left")

        # Store references
        self.skill_rows[skill_name] = row_frame
        row_frame.lbl_current_xp = lbl_current_xp
        row_frame.lbl_divider = lbl_divider
        row_frame.lbl_session_xp = lbl_session_xp
        row_frame.xp_container = xp_container

    def _update_skill_row(self, skill_name: str, current_xp: int, session_xp: int):
        """
        Update an existing skill row's XP values.

        Args:
            skill_name: Name of the skill
            current_xp: Updated XP gained in current script run
            session_xp: Updated XP gained since app opened
        """
        row_frame = self.skill_rows.get(skill_name)
        if not row_frame:
            return

        # Update current XP (always shown)
        if hasattr(row_frame, "lbl_current_xp"):
            row_frame.lbl_current_xp.configure(text=f"+{current_xp:,}")

        # Handle session XP display (only when different from current)
        if session_xp != current_xp:
            # Need to show divider and session XP
            if (
                not hasattr(row_frame, "lbl_session_xp")
                or row_frame.lbl_session_xp is None
            ):
                # Create divider and session label if they don't exist
                lbl_divider = customtkinter.CTkLabel(
                    row_frame.xp_container,
                    text="│",
                    font=("Roboto", 11),
                    text_color="#666666",
                    anchor="center",
                )
                lbl_divider.pack(side="left", padx=6)

                lbl_session_xp = customtkinter.CTkLabel(
                    row_frame.xp_container,
                    text=f"+{session_xp:,}",
                    font=("Roboto Medium", 11),
                    text_color="#7A7A7A",
                    anchor="e",
                )
                lbl_session_xp.pack(side="left")

                row_frame.lbl_divider = lbl_divider
                row_frame.lbl_session_xp = lbl_session_xp
            else:
                # Update existing session XP label
                row_frame.lbl_session_xp.configure(text=f"+{session_xp:,}")
        else:
            # Current and session are the same, hide divider and session label
            if hasattr(row_frame, "lbl_divider") and row_frame.lbl_divider:
                row_frame.lbl_divider.pack_forget()
                row_frame.lbl_divider = None
            if hasattr(row_frame, "lbl_session_xp") and row_frame.lbl_session_xp:
                row_frame.lbl_session_xp.pack_forget()
                row_frame.lbl_session_xp = None

    def clear(self):
        """Clear all skill rows (useful for session reset)."""
        for row_frame in self.skill_rows.values():
            row_frame.destroy()
        self.skill_rows.clear()
