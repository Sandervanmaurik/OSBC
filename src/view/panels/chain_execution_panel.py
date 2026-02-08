"""
ChainExecutionPanel - Displays progress during script chain execution.

Shows:
    - Current script name and progress
    - Current script countdown timer
    - Overall chain progress
    - List of all scripts with status indicators
    - Stop button
"""

import customtkinter
from typing import Optional
from model.chain import ScriptChain, ChainEntry, ChainEntryStatus


class ChainExecutionPanel(customtkinter.CTkFrame):
    """
    Panel shown during chain execution.

    Displays:
        - Chain name and overall progress
        - Current script progress with countdown
        - List of all scripts with status icons
        - Stop button
    """

    def __init__(self, parent, on_stop_command):
        """
        Args:
            parent: Parent widget
            on_stop_command: Callback when Stop button is clicked
        """
        super().__init__(parent, fg_color="#1A1A1A", corner_radius=0)

        self.on_stop_command = on_stop_command
        self.current_chain: Optional[ScriptChain] = None
        self.script_labels = []  # List of labels for each script

        # Configure layout
        self.rowconfigure(0, weight=0)  # Chain name
        self.rowconfigure(1, weight=0)  # Overall progress bar
        self.rowconfigure(2, weight=0)  # Overall progress label
        self.rowconfigure(3, weight=0)  # Separator
        self.rowconfigure(4, weight=0)  # Current script title
        self.rowconfigure(5, weight=0)  # Current script progress
        self.rowconfigure(6, weight=0)  # Current script countdown
        self.rowconfigure(7, weight=0)  # Separator
        self.rowconfigure(8, weight=1)  # Script list (scrollable)
        self.rowconfigure(9, weight=0)  # Stop button
        self.columnconfigure(0, weight=1)

        # ============ Chain Name ============
        self.lbl_chain_name = customtkinter.CTkLabel(
            self,
            text="Chain: ---",
            font=("Roboto Medium", 18),
            text_color="#DCE4EE",
            anchor="w",
        )
        self.lbl_chain_name.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        # ============ Overall Progress Bar ============
        self.lbl_overall = customtkinter.CTkLabel(
            self,
            text="Overall Progress: 0%",
            font=("Roboto", 12),
            text_color="#A0A0A0",
            anchor="w",
        )
        self.lbl_overall.grid(row=1, column=0, sticky="ew", padx=20, pady=(5, 2))

        self.progress_overall = customtkinter.CTkProgressBar(
            self,
            progress_color="#4A90E2",
            fg_color="#2E2E2E",
        )
        self.progress_overall.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.progress_overall.set(0)

        # ============ Separator ============
        separator1 = customtkinter.CTkFrame(self, height=2, fg_color="#2E2E2E")
        separator1.grid(row=3, column=0, sticky="ew", padx=20, pady=10)

        # ============ Current Script ============
        self.lbl_current_title = customtkinter.CTkLabel(
            self,
            text="Current Script: ---",
            font=("Roboto Medium", 16),
            text_color="#DCE4EE",
            anchor="w",
        )
        self.lbl_current_title.grid(row=4, column=0, sticky="ew", padx=20, pady=(10, 5))

        self.lbl_current_progress = customtkinter.CTkLabel(
            self,
            text="Progress: 0%",
            font=("Roboto", 12),
            text_color="#A0A0A0",
            anchor="w",
        )
        self.lbl_current_progress.grid(
            row=5, column=0, sticky="ew", padx=20, pady=(5, 2)
        )

        self.progress_current = customtkinter.CTkProgressBar(
            self,
            progress_color="#66BB6A",
            fg_color="#2E2E2E",
        )
        self.progress_current.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 5))
        self.progress_current.set(0)

        self.lbl_countdown = customtkinter.CTkLabel(
            self,
            text="Time remaining: --:--",
            font=("Roboto Medium", 13),
            text_color="#FFA726",
            anchor="w",
        )
        self.lbl_countdown.grid(row=7, column=0, sticky="ew", padx=20, pady=(5, 10))

        # ============ Separator ============
        separator2 = customtkinter.CTkFrame(self, height=2, fg_color="#2E2E2E")
        separator2.grid(row=8, column=0, sticky="ew", padx=20, pady=10)

        # ============ Scripts List ============
        list_label = customtkinter.CTkLabel(
            self,
            text="Scripts in Chain:",
            font=("Roboto Medium", 14),
            text_color="#DCE4EE",
            anchor="w",
        )
        list_label.grid(row=9, column=0, sticky="ew", padx=20, pady=(10, 5))

        self.scrollable_scripts = customtkinter.CTkScrollableFrame(
            self,
            fg_color="#0F0F0F",
            corner_radius=8,
        )
        self.scrollable_scripts.grid(
            row=10, column=0, sticky="nsew", padx=20, pady=(0, 10)
        )
        self.scrollable_scripts.columnconfigure(0, weight=1)

        # ============ Stop Button ============
        self.btn_stop = customtkinter.CTkButton(
            self,
            text="⏹ Stop Chain",
            font=("Roboto Medium", 14),
            fg_color="#C62828",
            hover_color="#D32F2F",
            command=self._on_stop_clicked,
            height=40,
        )
        self.btn_stop.grid(row=11, column=0, sticky="ew", padx=20, pady=(0, 15))

    # ============ Public API ============

    def set_chain(self, chain: ScriptChain):
        """
        Set the chain to display.

        Args:
            chain: ScriptChain being executed
        """
        self.current_chain = chain
        self.lbl_chain_name.configure(text=f"Chain: {chain.name}")
        self._build_script_list()

    def update_overall_progress(self, progress: float):
        """
        Update overall chain progress.

        Args:
            progress: Progress value between 0.0 and 1.0
        """
        self.progress_overall.set(progress)
        self.lbl_overall.configure(text=f"Overall Progress: {progress * 100:.0f}%")

    def update_current_script(self, entry: ChainEntry, script_index: int):
        """
        Update the current script display.

        Args:
            entry: Currently executing ChainEntry
            script_index: Index of script in chain (0-based)
        """
        self.lbl_current_title.configure(
            text=f"Current Script: {entry.script_name} ({script_index + 1}/{len(self.current_chain.entries)})"
        )

    def update_current_progress(self, progress: float, remaining_seconds: int):
        """
        Update current script progress and countdown.

        Args:
            progress: Progress value between 0.0 and 1.0
            remaining_seconds: Seconds remaining for current script
        """
        self.progress_current.set(progress)
        self.lbl_current_progress.configure(text=f"Progress: {progress * 100:.0f}%")

        # Format countdown as MM:SS
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        self.lbl_countdown.configure(
            text=f"Time remaining: {minutes:02d}:{seconds:02d}"
        )

    def update_script_status(self, script_index: int, status: ChainEntryStatus):
        """
        Update status icon for a specific script in the list.

        Args:
            script_index: Index of script in chain
            status: New status
        """
        if script_index < len(self.script_labels):
            label = self.script_labels[script_index]
            icon = self._get_status_icon(status)

            # Update just the icon part (first character)
            current_text = label.cget("text")
            # Text format: "icon ScriptName (duration)"
            parts = current_text.split(" ", 1)
            if len(parts) == 2:
                label.configure(text=f"{icon} {parts[1]}")

    def reset(self):
        """Reset panel to initial state."""
        self.lbl_chain_name.configure(text="Chain: ---")
        self.lbl_current_title.configure(text="Current Script: ---")
        self.lbl_current_progress.configure(text="Progress: 0%")
        self.lbl_countdown.configure(text="Time remaining: --:--")
        self.progress_overall.set(0)
        self.progress_current.set(0)
        self.lbl_overall.configure(text="Overall Progress: 0%")

        # Clear script list
        for label in self.script_labels:
            label.destroy()
        self.script_labels.clear()

    # ============ Private Methods ============

    def _build_script_list(self):
        """Build the list of scripts with status icons."""
        # Clear existing
        for label in self.script_labels:
            label.destroy()
        self.script_labels.clear()

        # Create label for each script
        for idx, entry in enumerate(self.current_chain.entries):
            icon = self._get_status_icon(entry.status)
            text = f"{icon} {entry.script_name} ({entry.running_time} min)"

            label = customtkinter.CTkLabel(
                self.scrollable_scripts,
                text=text,
                font=("Roboto", 13),
                text_color="#DCE4EE",
                anchor="w",
            )
            label.grid(row=idx, column=0, sticky="ew", padx=10, pady=3)
            self.script_labels.append(label)

    def _get_status_icon(self, status: ChainEntryStatus) -> str:
        """
        Get emoji icon for a status.

        Args:
            status: ChainEntryStatus

        Returns:
            Emoji string
        """
        status_icons = {
            ChainEntryStatus.PENDING: "⏸️",  # Paused (waiting)
            ChainEntryStatus.RUNNING: "▶️",  # Playing (running)
            ChainEntryStatus.COMPLETED: "✅",  # Checkmark (done)
            ChainEntryStatus.SKIPPED: "⏭️",  # Skip (skipped)
            ChainEntryStatus.FAILED: "❌",  # X (failed)
        }
        return status_icons.get(status, "⏸️")

    def _on_stop_clicked(self):
        """Handle Stop button click."""
        if self.on_stop_command:
            self.on_stop_command()
