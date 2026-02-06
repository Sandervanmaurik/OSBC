"""
ScriptPanel - Middle panel showing script details, controls, progress, log, and behavior.
Composes ScriptControlBar, OutputLogFrame, and BehaviorFrame.
"""

import customtkinter
from view.components.script_control_bar import ScriptControlBar
from view.output_log_frame import OutputLogFrame
from view.behavior_frame import BehaviorFrame


class ScriptPanel(customtkinter.CTkFrame):
    """
    Middle panel containing:
        - Script title and description (top)
        - Script control bar (Play/Stop/Options)
        - Progress bar
        - Output log (large, reused)
        - Behavior frame (compact, reused)
    """

    def __init__(self, parent, play_command, stop_command, options_command):
        """
        Args:
            parent: Parent widget
            play_command: Callback when Play button is clicked
            stop_command: Callback when Stop button is clicked
            options_command: Callback when Options button is clicked
        """
        super().__init__(parent, fg_color="#1A1A1A", corner_radius=0)

        # Configure layout
        self.rowconfigure(0, weight=0)  # Title
        self.rowconfigure(1, weight=0)  # Description
        self.rowconfigure(2, weight=0)  # Control bar
        self.rowconfigure(3, weight=0)  # Progress label
        self.rowconfigure(4, weight=0)  # Progress bar
        self.rowconfigure(5, weight=1)  # Output log (expandable)
        self.rowconfigure(6, weight=0)  # Behavior frame (compact)
        self.columnconfigure(0, weight=1)

        # --- Script Title ---
        self.lbl_title = customtkinter.CTkLabel(
            self,
            text="Select a Script",
            font=("Roboto Medium", 18),
            text_color="#DCE4EE",
            anchor="w",
        )
        self.lbl_title.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))

        # --- Script Description ---
        self.lbl_description = customtkinter.CTkLabel(
            self,
            text="",
            font=("Roboto", 13),
            text_color="#A0A0A0",
            anchor="w",
            wraplength=500,
        )
        self.lbl_description.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        # --- Control Bar ---
        self.control_bar = ScriptControlBar(
            parent=self,
            play_command=play_command,
            stop_command=stop_command,
            options_command=options_command,
        )
        self.control_bar.grid(row=2, column=0, sticky="w", padx=20, pady=(5, 10))

        # --- Progress Label ---
        self.lbl_progress = customtkinter.CTkLabel(
            self,
            text="Progress: 0%",
            font=("Roboto", 12),
            text_color="#A0A0A0",
            anchor="w",
        )
        self.lbl_progress.grid(row=3, column=0, sticky="ew", padx=20, pady=(5, 2))

        # --- Progress Bar ---
        self.progressbar = customtkinter.CTkProgressBar(
            self,
            progress_color="#4A90E2",
            fg_color="#2E2E2E",
        )
        self.progressbar.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.progressbar.set(0)

        # --- Output Log (large) ---
        self.log_frame = OutputLogFrame(parent=self)
        self.log_frame.grid(row=5, column=0, sticky="nsew", padx=15, pady=(5, 10))

        # --- Behavior Frame (compact) ---
        self.behavior_frame = BehaviorFrame(parent=self)
        self.behavior_frame.grid(row=6, column=0, sticky="ew", padx=15, pady=(0, 15))

    def set_script_info(self, title: str, description: str):
        """
        Update the script title and description.

        Args:
            title: Script title
            description: Script description
        """
        self.lbl_title.configure(text=title)
        self.lbl_description.configure(text=description)

    def update_progress(self, progress: float):
        """
        Update the progress bar.

        Args:
            progress: Progress value between 0.0 and 1.0
        """
        self.progressbar.set(progress)
        self.lbl_progress.configure(text=f"Progress: {progress * 100:.0f}%")

    def get_control_bar(self):
        """
        Get the ScriptControlBar for external control.

        Returns:
            ScriptControlBar instance
        """
        return self.control_bar

    def get_log_frame(self):
        """
        Get the OutputLogFrame for controller binding.

        Returns:
            OutputLogFrame instance
        """
        return self.log_frame

    def get_behavior_frame(self):
        """
        Get the BehaviorFrame for controller binding.

        Returns:
            BehaviorFrame instance
        """
        return self.behavior_frame
