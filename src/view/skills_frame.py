import pathlib
from typing import Dict
import tkinter

import customtkinter
from PIL import Image, ImageTk

from utilities.osrs_skills import skill_names
from view.fonts.fonts import *


class SkillsFrame(customtkinter.CTkFrame):
    def __init__(self, parent):
        """
        Creates a frame displaying OSRS skill levels in a 3x8 grid.
        Skills data persists across bot switches.
        """
        super().__init__(parent)

        # Store current skills data for persistence
        self.current_skills_data: Dict[str, int] = {}

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
            row=0, column=0, columnspan=3, sticky="wns", padx=15, pady=(15, 5)
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
            icon.thumbnail((icon_size, icon_size), Image.LANCZOS)
            canvas = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
            offset = ((icon_size - icon.width) // 2, (icon_size - icon.height) // 2)
            canvas.paste(icon, offset, icon)
            self.skill_images[name] = ImageTk.PhotoImage(canvas)

        # Create skill labels in 3x8 grid
        self.skill_value_labels = []
        for i, name in enumerate(skill_names()):
            row = (i // 3) + 1  # Start from row 1 (row 0 is title)
            col = i % 3

            cell = customtkinter.CTkFrame(master=self, fg_color=self._fg_color)
            cell.grid(row=row, column=col, padx=4, pady=2, sticky="nsew")
            cell.rowconfigure(0, weight=1)
            cell.columnconfigure(0, weight=0)
            cell.columnconfigure(1, weight=1)

            icon = self.skill_images.get(name)
            icon_label = customtkinter.CTkLabel(master=cell, image=icon, text="")
            icon_label.grid(row=0, column=0, padx=(2, 4), pady=1, sticky="w")

            value_label = customtkinter.CTkLabel(
                master=cell,
                text="--",
                font=log_font(12),
                justify=tkinter.LEFT,
            )
            value_label.grid(row=0, column=1, padx=(0, 2), pady=1, sticky="w")
            self.skill_value_labels.append(value_label)

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

        # Update display
        for idx, name in enumerate(skill_names()):
            if idx >= len(self.skill_value_labels):
                break
            level = self.current_skills_data.get(name, -1)
            text = "?" if level < 0 else str(level)
            self.skill_value_labels[idx].configure(text=text)

    def reset_skills(self):
        """
        Resets all skill levels to '--' and clears stored data.
        Only call this when explicitly needed (e.g., closing all bots).
        """
        self.current_skills_data.clear()
        for lbl in self.skill_value_labels:
            lbl.configure(text="--")
