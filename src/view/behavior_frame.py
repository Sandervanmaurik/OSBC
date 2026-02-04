from typing import Dict, Any
import tkinter

import customtkinter

from view.fonts.fonts import *


class BehaviorFrame(customtkinter.CTkFrame):
    def __init__(self, parent):
        """
        Creates a frame displaying behavior configuration and stats.
        Shows profile name and key settings (read-only display).
        """
        super().__init__(parent)

        # Configure grid layout (8 rows: title + 7 settings)
        self.rowconfigure(0, weight=0)  # Title row
        for r in range(1, 8):  # 7 setting rows
            self.rowconfigure(r, weight=0)
        self.columnconfigure(0, weight=1)

        # Frame title
        self.lbl_title = customtkinter.CTkLabel(
            master=self,
            text="Behavior",
            font=subheading_font(),
            justify=tkinter.LEFT,
        )
        self.lbl_title.grid(row=0, column=0, sticky="wns", padx=10, pady=(10, 5))

        # Setting labels (7 key settings)
        self.setting_labels = []
        setting_names = [
            "Profile:",
            "Speed:",
            "Misclick:",
            "Camera:",
            "Breaks:",
            "Bank-Standing:",
            "Stats:",
        ]

        for i, name in enumerate(setting_names, start=1):
            row_frame = customtkinter.CTkFrame(master=self, fg_color=self._fg_color)
            row_frame.grid(row=i, column=0, padx=10, pady=2, sticky="ew")
            row_frame.columnconfigure(0, weight=0)
            row_frame.columnconfigure(1, weight=1)

            # Setting name label
            name_label = customtkinter.CTkLabel(
                master=row_frame,
                text=name,
                font=log_font(12),
                justify=tkinter.LEFT,
                anchor="w",
                width=100,
            )
            name_label.grid(row=0, column=0, padx=(0, 10), pady=1, sticky="w")

            # Setting value label
            value_label = customtkinter.CTkLabel(
                master=row_frame,
                text="--",
                font=log_font(12),
                justify=tkinter.LEFT,
                anchor="w",
            )
            value_label.grid(row=0, column=1, padx=(0, 0), pady=1, sticky="w")
            self.setting_labels.append(value_label)

    def update_behavior_display(
        self, behavior_config: Dict[str, Any], stats: Dict[str, Any] = None
    ):
        """
        Updates the behavior settings display.

        Args:
            behavior_config: Dictionary from BehaviorManager.config
            stats: Optional statistics dictionary from BehaviorManager.get_stats_summary()
        """
        if not isinstance(behavior_config, dict):
            return

        # Extract key settings
        profile_name = behavior_config.get("name", "Unknown")
        timing_config = behavior_config.get("timing", {})
        mouse_config = behavior_config.get("mouse", {})
        action_config = behavior_config.get("action", {})
        attention_config = behavior_config.get("attention", {})
        breaks_config = behavior_config.get("breaks", {})

        # Calculate derived values
        speed_mult = timing_config.get("speed_multiplier", 1.0)
        speed_text = f"{speed_mult:.2f}x"
        if speed_mult < 1.0:
            speed_text += " (faster)"
        elif speed_mult > 1.0:
            speed_text += " (slower)"

        misclick_chance = action_config.get("misclick_chance", 0.0)
        misclick_text = f"{misclick_chance:.1%}"

        camera_enabled = attention_config.get("camera_enabled", True)
        camera_interval = attention_config.get("camera_interval", (30, 90))
        if camera_enabled:
            # Check if bank-standing mode (very rare camera: 60-1200s)
            if isinstance(camera_interval, tuple) and camera_interval[0] >= 60:
                camera_text = (
                    f"Enabled ({camera_interval[0]:.0f}-{camera_interval[1]:.0f}s)"
                )
            else:
                camera_text = "Enabled"
        else:
            camera_text = "Disabled"

        breaks_enabled = breaks_config.get("enabled", False)
        breaks_text = "Enabled" if breaks_enabled else "Disabled"

        # Bank-standing detection (very rare camera = 60-1200s)
        is_bank_standing = False
        if camera_enabled and isinstance(camera_interval, tuple):
            if camera_interval[0] >= 60 and camera_interval[1] >= 600:
                is_bank_standing = True
        bank_standing_text = "Yes" if is_bank_standing else "No"

        # Stats summary
        stats_text = "--"
        if stats and isinstance(stats, dict):
            duration_min = stats.get("duration_minutes", 0)
            camera_count = stats.get("camera", 0)
            mouse_count = stats.get("mouse_movement", 0)
            skill_count = stats.get("skill_check", 0)
            inventory_count = stats.get("inventory_check", 0)

            total_behaviors = camera_count + mouse_count + skill_count + inventory_count
            if duration_min > 0:
                stats_text = f"{total_behaviors} in {duration_min:.1f}min"
            else:
                stats_text = f"{total_behaviors} total"

        # Update labels
        values = [
            profile_name,
            speed_text,
            misclick_text,
            camera_text,
            breaks_text,
            bank_standing_text,
            stats_text,
        ]

        for idx, value in enumerate(values):
            if idx < len(self.setting_labels):
                self.setting_labels[idx].configure(text=value)

    def reset_display(self):
        """
        Resets all setting values to '--'.
        """
        for lbl in self.setting_labels:
            lbl.configure(text="--")
