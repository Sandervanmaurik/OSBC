import pathlib
from datetime import datetime
from typing import Dict, Optional
import tkinter

import customtkinter
from PIL import Image, ImageTk

from model.skills import SkillsManager, ExperienceTable
from utilities.osrs_skills import skill_names
from view.fonts.fonts import *


class SkillsFrame(customtkinter.CTkFrame):
    def __init__(self, parent):
        """
        Creates a frame displaying OSRS skill levels in a 3x8 grid.
        Skills data persists across bot switches.

        Features:
        - Progress bars showing XP progress to next level
        - Colored dots indicating data freshness (green/yellow/gray)
        - Hover tooltips with detailed XP information
        """
        super().__init__(parent)

        # Store current skills data for persistence
        self.current_skills_data: Dict[str, int] = {}

        # Store UI elements for each skill
        self.skill_cells: Dict[str, tkinter.Canvas] = {}
        self.skill_value_labels = []
        self.skill_freshness_dots = {}  # skill_name -> canvas item ID
        self.skill_progress_bars = {}  # skill_name -> canvas item ID
        self.skill_remaining_xp_labels = {}  # skill_name -> canvas item ID
        self.skill_tooltips = {}  # skill_name -> tooltip text

        # Configure grid layout (8 rows, 3 columns for skills, plus title row)
        # All rows should have weight=0 to prevent expansion and show all content
        self.rowconfigure(0, weight=0)  # Title row - fixed size
        for r in range(1, 9):  # 8 rows of skills - fixed size to show all
            self.rowconfigure(r, weight=0)
        for c in range(3):
            self.columnconfigure(c, weight=1)

        # Frame title
        self.lbl_title = customtkinter.CTkLabel(
            master=self,
            text="Skills",
            font=subheading_font(),
            justify=tkinter.LEFT,
        )
        self.lbl_title.grid(
            row=0, column=0, columnspan=3, sticky="wns", padx=10, pady=(10, 5)
        )

        # Load skill icons
        skills_path = pathlib.Path(__file__).parent.parent.joinpath(
            "images", "bot", "skills"
        )
        self.skill_images: Dict[str, ImageTk.PhotoImage] = {}
        icon_size = 22
        for name in skill_names():
            icon_file = skills_path / f"{name}.png"
            if not icon_file.exists():
                continue
            icon = Image.open(icon_file).convert("RGBA")
            icon.thumbnail((icon_size, icon_size), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
            offset = ((icon_size - icon.width) // 2, (icon_size - icon.height) // 2)
            canvas.paste(icon, offset, icon)
            self.skill_images[name] = ImageTk.PhotoImage(canvas)

        # Create skill cells in 3x8 grid
        self._create_skill_cells()

        # Subscribe to SkillsManager for automatic updates
        SkillsManager().add_observer(self._on_skills_updated)

        # Start periodic UI refresh for freshness indicators
        self._refresh_timer_id = None
        self._schedule_refresh()

        # Initial UI update to show current skill states
        self.update_skills_from_manager()

    def _create_skill_cells(self):
        """Create the skill display cells with progress bars and indicators."""
        for i, name in enumerate(skill_names()):
            row = (i // 3) + 1  # Start from row 1 (row 0 is title)
            col = i % 3

            # Create container frame with rounded corners
            container = customtkinter.CTkFrame(
                master=self,
                fg_color="#1E1E1E",  # Match canvas background
                corner_radius=6,  # Rounded corners
            )
            container.grid(row=row, column=col, padx=5, pady=3, sticky="nsew")

            # Create canvas for custom drawing (progress bar, freshness dot)
            cell_canvas = tkinter.Canvas(
                container,
                width=70,
                height=36,
                bg="#1E1E1E",  # Very dark gray background
                highlightthickness=0,
            )
            cell_canvas.pack(fill="both", expand=True, padx=1, pady=1)
            self.skill_cells[name] = cell_canvas

            # Draw skill icon on the left (centered vertically between level and remaining XP)
            icon = self.skill_images.get(name)
            if icon:
                cell_canvas.create_image(6, 18, image=icon, anchor="w")

            # Draw skill value text to the right of the icon (upper area)
            value_text_id = cell_canvas.create_text(
                32,
                12,
                text="--",
                font=("Consolas", 10, "bold"),
                anchor="w",
                fill="#DCE4EE",  # Light gray/white text
            )
            self.skill_value_labels.append((name, cell_canvas, value_text_id))

            # Create freshness indicator (hidden by default)
            dot_id = cell_canvas.create_oval(0, 0, 0, 0, fill="", outline="")
            self.skill_freshness_dots[name] = dot_id

            # Create progress bar (hidden by default)
            bar_id = cell_canvas.create_rectangle(0, 0, 0, 0, fill="", outline="")
            self.skill_progress_bars[name] = bar_id

            # Create remaining XP label (hidden by default, smaller text below the level)
            remaining_xp_id = cell_canvas.create_text(
                32,
                24,
                text="",
                font=("Consolas", 7),
                anchor="w",
                fill="#888888",  # Dimmed gray text
            )
            self.skill_remaining_xp_labels[name] = remaining_xp_id

            # Bind hover events for tooltip
            cell_canvas.bind("<Enter>", lambda e, s=name: self._show_tooltip(e, s))
            cell_canvas.bind("<Leave>", lambda e: self._hide_tooltip())

    def _on_skills_updated(self):
        """Callback when SkillsManager notifies of skill changes."""
        self.update_skills_from_manager()

    def _schedule_refresh(self):
        """Schedule periodic UI refresh for freshness indicators."""
        self.update_freshness_indicators()
        # Refresh every 5 seconds to update dot colors
        self._refresh_timer_id = self.after(5000, self._schedule_refresh)

    def destroy(self):
        """Clean up when frame is destroyed."""
        if self._refresh_timer_id:
            self.after_cancel(self._refresh_timer_id)
        SkillsManager().remove_observer(self._on_skills_updated)
        super().destroy()

    def update_skills(self, skill_data):
        """
        Updates the skill levels display and stores the data for persistence.
        Args:
            skill_data: Dict mapping skill names to level values
        """
        if not isinstance(skill_data, dict):
            return

        # Update stored data
        self.current_skills_data.update(skill_data)

        # Update SkillsManager with level data (this will trigger observers)
        for skill_name, level in skill_data.items():
            try:
                SkillsManager().update_skill_level(skill_name, level)
            except (ValueError, KeyError) as e:
                # Skip invalid skill names or levels
                continue

        # Force immediate UI update (observer may be delayed)
        self.update_skills_from_manager()

    def update_skills_from_manager(self):
        """Update the UI from SkillsManager data (called by observer)."""
        manager = SkillsManager()

        for skill_name, canvas, text_id in self.skill_value_labels:
            try:
                skill_state = manager.get_skill(skill_name)

                # Update level text (show -- for -1, ? for 0, or the actual level)
                if skill_state.level < 0:
                    level_text = "--"
                elif skill_state.level == 0:
                    level_text = "?"
                else:
                    level_text = str(skill_state.level)

                canvas.itemconfig(text_id, text=level_text)

                # Update progress bar (only if we have XP data)
                self._update_progress_bar(skill_name, skill_state)

                # Update remaining XP label (only if we have XP data)
                self._update_remaining_xp_label(skill_name, skill_state)

                # Update freshness dot
                self._update_freshness_dot(skill_name, skill_state)

                # Update tooltip data
                self._update_tooltip(skill_name, skill_state)

            except (ValueError, KeyError) as e:
                # Skill not found, skip
                continue
            except Exception as e:
                # Unexpected error, skip
                continue

    def _update_progress_bar(self, skill_name: str, skill_state):
        """Draw or hide the progress bar based on XP data."""
        canvas = self.skill_cells.get(skill_name)
        bar_id = self.skill_progress_bars.get(skill_name)

        if not canvas or bar_id is None:
            return

        if (
            skill_state.has_xp_data()
            and skill_state.level < 99
            and skill_state.level > 0
        ):
            # Calculate progress
            progress = ExperienceTable().progress_to_next_level(skill_state.xp)

            # Get canvas dimensions (use fixed width since we set it)
            canvas_width = 70  # Fixed width we set in _create_skill_cells
            canvas_height = 36  # Fixed height we set (increased from 28 to 36)

            # Draw progress bar at bottom (3px tall, blue)
            bar_width = int(canvas_width * progress)
            canvas.coords(bar_id, 0, canvas_height - 3, bar_width, canvas_height)
            canvas.itemconfig(bar_id, fill="#4A90E2", outline="")
        else:
            # Hide progress bar (no XP data, level 99, or unread)
            canvas.coords(bar_id, 0, 0, 0, 0)
            canvas.itemconfig(bar_id, fill="", outline="")

    def _update_remaining_xp_label(self, skill_name: str, skill_state):
        """Show or hide the remaining XP label based on XP data."""
        canvas = self.skill_cells.get(skill_name)
        label_id = self.skill_remaining_xp_labels.get(skill_name)

        if not canvas or label_id is None:
            return

        if (
            skill_state.has_xp_data()
            and skill_state.level < 99
            and skill_state.level > 0
        ):
            # Calculate remaining XP to next level
            current_level = skill_state.level
            next_level_xp = ExperienceTable().level_to_xp(current_level + 1)
            remaining_xp = next_level_xp - skill_state.xp

            # Format remaining XP (use k/m suffix for large numbers)
            if remaining_xp >= 1_000_000:
                xp_text = f"{remaining_xp / 1_000_000:.1f}m"
            elif remaining_xp >= 10_000:
                xp_text = f"{remaining_xp / 1_000:.0f}k"
            elif remaining_xp >= 1_000:
                xp_text = f"{remaining_xp / 1_000:.1f}k"
            else:
                xp_text = str(remaining_xp)

            # Update label text
            canvas.itemconfig(label_id, text=xp_text)
        else:
            # Hide label (no XP data, level 99, or unread)
            canvas.itemconfig(label_id, text="")

    def _update_freshness_dot(self, skill_name: str, skill_state):
        """Draw the freshness indicator dot in the top-right corner."""
        canvas = self.skill_cells.get(skill_name)
        dot_id = self.skill_freshness_dots.get(skill_name)

        if not canvas or dot_id is None:
            return

        # Don't show dot if skill hasn't been read yet
        if skill_state.level < 0:
            canvas.coords(dot_id, 0, 0, 0, 0)
            canvas.itemconfig(dot_id, fill="", outline="")
            return

        # Calculate age of data
        age_seconds = (datetime.now() - skill_state.timestamp).total_seconds()

        # Determine color based on freshness
        if age_seconds < 10:
            color = "#4CAF50"  # Green
        elif age_seconds < 60:
            color = "#FFC107"  # Yellow
        else:
            color = "#9E9E9E"  # Gray

        # Get canvas dimensions (use fixed width)
        canvas_width = 70  # Fixed width we set

        # Draw dot in top-right corner (5px diameter)
        dot_size = 5
        x = canvas_width - dot_size - 4
        y = 4
        canvas.coords(dot_id, x, y, x + dot_size, y + dot_size)
        canvas.itemconfig(dot_id, fill=color, outline="")

    def update_freshness_indicators(self):
        """Update all freshness dots (called periodically)."""
        manager = SkillsManager()
        for skill_name in skill_names():
            try:
                skill_state = manager.get_skill(skill_name)
                self._update_freshness_dot(skill_name, skill_state)
            except (ValueError, KeyError):
                continue

    def _update_tooltip(self, skill_name: str, skill_state):
        """Update the tooltip text for a skill."""
        if skill_state.has_xp_data():
            next_level_xp = ExperienceTable().xp_to_next_level(skill_state.xp)
            tooltip = f"{skill_state.xp:,} / {next_level_xp:,} XP (XP gained: {skill_state.xp_gained:,})"
            self.skill_tooltips[skill_name] = tooltip
        else:
            self.skill_tooltips[skill_name] = None

    def _show_tooltip(self, event, skill_name: str):
        """Show tooltip on hover."""
        tooltip_text = self.skill_tooltips.get(skill_name)
        if not tooltip_text:
            return

        # Create tooltip window
        if hasattr(self, "_tooltip_window") and self._tooltip_window:
            self._tooltip_window.destroy()

        self._tooltip_window = tkinter.Toplevel(self)
        self._tooltip_window.wm_overrideredirect(True)
        self._tooltip_window.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

        label = tkinter.Label(
            self._tooltip_window,
            text=tooltip_text,
            background="#FFFFE0",
            relief="solid",
            borderwidth=1,
            font=("Arial", 9),
        )
        label.pack()

    def _hide_tooltip(self):
        """Hide tooltip."""
        if hasattr(self, "_tooltip_window") and self._tooltip_window:
            self._tooltip_window.destroy()
            self._tooltip_window = None

    def reset_skills(self):
        """
        Resets all skill levels to '--' and clears stored data.
        Only call this when explicitly needed (e.g., closing all bots).
        """
        self.current_skills_data.clear()

        # Reset UI display
        for skill_name, canvas, text_id in self.skill_value_labels:
            canvas.itemconfig(text_id, text="--")

            # Hide progress bars and dots
            bar_id = self.skill_progress_bars.get(skill_name)
            if bar_id:
                canvas.coords(bar_id, 0, 0, 0, 0)
                canvas.itemconfig(bar_id, fill="", outline="")

            dot_id = self.skill_freshness_dots.get(skill_name)
            if dot_id:
                canvas.coords(dot_id, 0, 0, 0, 0)
                canvas.itemconfig(dot_id, fill="", outline="")

            # Hide remaining XP label
            remaining_xp_id = self.skill_remaining_xp_labels.get(skill_name)
            if remaining_xp_id:
                canvas.itemconfig(remaining_xp_id, text="")
