"""
ChainExecutionPanel - Displays progress during script chain execution.

Shows:
    - Compact script items with status and time remaining
    - Script log output
    - Stop button

XP Gained and Current Action are shown in the right column.
"""

import tkinter
import customtkinter
from typing import Optional
from model.chain import ScriptChain, ChainEntry, ChainEntryStatus
from view.fonts.fonts import log_font


class ChainExecutionPanel(customtkinter.CTkFrame):
    """
    Panel shown during chain execution.

    Displays:
        - Compact chain progress with script items
        - Script log
        - Stop button

    Keyboard shortcuts:
        - SHIFT+ENTER: Stop chain
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
        self.script_boxes = []  # List of script box frames
        self._shortcut_bound = False  # Track if keyboard shortcut is bound

        # Configure layout - much more compact
        self.rowconfigure(0, weight=0)  # Chain header
        self.rowconfigure(1, weight=0)  # Scripts container
        self.rowconfigure(2, weight=0)  # Separator
        self.rowconfigure(3, weight=0)  # Log label
        self.rowconfigure(4, weight=1)  # Log (expandable)
        self.rowconfigure(5, weight=0)  # Stop button
        self.columnconfigure(0, weight=1)

        # ============ Chain Header ============
        self.lbl_chain_name = customtkinter.CTkLabel(
            self,
            text="Chain: ---",
            font=("Roboto Medium", 16),
            text_color="#DCE4EE",
            anchor="w",
        )
        self.lbl_chain_name.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        # ============ Scripts Container (Compact Boxes) ============
        self.scripts_container = customtkinter.CTkScrollableFrame(
            self,
            fg_color="#0F0F0F",
            corner_radius=8,
            height=140,  # Fixed compact height
            scrollbar_button_color="#2E2E2E",
            scrollbar_button_hover_color="#3A3A3A",
        )
        self.scripts_container.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.scripts_container.columnconfigure(0, weight=1)

        # ============ Separator ============
        separator = customtkinter.CTkFrame(self, height=2, fg_color="#2E2E2E")
        separator.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

        # ============ Script Log ============
        log_label = customtkinter.CTkLabel(
            self,
            text="Script Log:",
            font=("Roboto Medium", 14),
            text_color="#DCE4EE",
            anchor="w",
        )
        log_label.grid(row=3, column=0, sticky="ew", padx=20, pady=(5, 5))

        # Log frame container
        log_container = customtkinter.CTkFrame(
            self, fg_color="#0F0F0F", corner_radius=8
        )
        log_container.grid(row=4, column=0, sticky="nsew", padx=20, pady=(0, 10))
        log_container.rowconfigure(0, weight=1)
        log_container.columnconfigure(0, weight=1)

        # Text Box for log
        self.txt_log = tkinter.Text(
            master=log_container,
            wrap=tkinter.WORD,
            font=log_font(),
            bg="#343638",
            fg="#ffffff",
            padx=20,
            pady=5,
            spacing1=4,  # spacing before a line
            spacing3=4,  # spacing after a line / wrapped line
            cursor="arrow",
            height=10,  # Initial height in lines
        )
        self.txt_log.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)
        self.txt_log.configure(state=tkinter.DISABLED)

        # Scrollbar for log
        log_scrollbar = customtkinter.CTkScrollbar(
            master=log_container, command=self.txt_log.yview
        )
        log_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 5), pady=5)
        self.txt_log.configure(yscrollcommand=log_scrollbar.set)

        # ============ Stop Button ============
        self.btn_stop = customtkinter.CTkButton(
            self,
            text="⏹ Stop Chain (SHIFT+ENTER)",
            font=("Roboto Medium", 14),
            fg_color="#C62828",
            hover_color="#D32F2F",
            command=self._on_stop_clicked,
            height=40,
        )
        self.btn_stop.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 15))

    # ============ Public API ============

    def show(self):
        """Show the panel and bind keyboard shortcuts."""
        self._bind_shortcuts()
        # Grid is called by parent, this is just for shortcut binding

    def hide(self):
        """Hide the panel and unbind keyboard shortcuts."""
        self._unbind_shortcuts()
        # Ungrid is called by parent, this is just for shortcut unbinding

    def set_chain(self, chain: ScriptChain):
        """
        Set the chain to display.

        Args:
            chain: ScriptChain being executed
        """
        self.current_chain = chain
        self.lbl_chain_name.configure(
            text=f"Chain: {chain.name} ({len(chain.entries)} scripts)"
        )
        self._build_script_boxes()
        self._bind_shortcuts()  # Ensure shortcuts are bound when chain starts

    def update_overall_progress(self, progress: float):
        """
        Update overall chain progress (updates all script boxes).

        Args:
            progress: Progress value between 0.0 and 1.0
        """
        # Overall progress is shown via individual script statuses
        pass

    def update_current_script(self, entry: ChainEntry, script_index: int):
        """
        Update the current script display.

        Args:
            entry: Currently executing ChainEntry
            script_index: Index of script in chain (0-based)
        """
        # Highlight the current script box
        if script_index < len(self.script_boxes):
            self._update_script_box(script_index, entry)

    def update_current_progress(self, progress: float, remaining_seconds: int):
        """
        Update current script progress and countdown.

        Args:
            progress: Progress value between 0.0 and 1.0
            remaining_seconds: Seconds remaining for current script
        """
        # Find the currently running script and update its box
        for idx, entry in enumerate(self.current_chain.entries):
            if entry.status == ChainEntryStatus.RUNNING:
                if idx < len(self.script_boxes):
                    self._update_script_box(idx, entry, progress, remaining_seconds)
                break

    def update_script_status(self, script_index: int, status: ChainEntryStatus):
        """
        Update status icon for a specific script in the list.

        Args:
            script_index: Index of script in chain
            status: New status
        """
        if script_index < len(self.script_boxes):
            entry = self.current_chain.entries[script_index]
            self._update_script_box(script_index, entry)

    def reset(self):
        """Reset panel to initial state."""
        self.lbl_chain_name.configure(text="Chain: ---")

        # Clear script boxes
        for box in self.script_boxes:
            box.destroy()
        self.script_boxes.clear()

        # Clear log
        self.clear_log()

    def update_log(self, msg: str, overwrite: bool = False):
        """
        Update the script log with a message.

        Args:
            msg: Message to log
            overwrite: If True, replace the last line
        """
        self.txt_log.configure(state=tkinter.NORMAL)
        if overwrite:
            self.txt_log.delete("end-1c linestart", "end")
        self.txt_log.insert(tkinter.END, "\n" + msg)
        self.txt_log.configure(state=tkinter.DISABLED)
        self.txt_log.see(tkinter.END)

    def clear_log(self):
        """Clear the script log."""
        self.txt_log.configure(state=tkinter.NORMAL)
        self.txt_log.delete(1.0, tkinter.END)
        self.txt_log.configure(state=tkinter.DISABLED)
        self.txt_log.see(tkinter.END)

    # ============ Private Methods ============

    def _build_script_boxes(self):
        """Build compact script boxes styled like XP gained boxes."""
        # Clear existing
        for box in self.script_boxes:
            box.destroy()
        self.script_boxes.clear()

        # Create box for each script
        for idx, entry in enumerate(self.current_chain.entries):
            box = self._create_script_box(idx, entry)
            self.script_boxes.append(box)

    def _create_script_box(self, idx: int, entry: ChainEntry) -> customtkinter.CTkFrame:
        """
        Create a compact script box with status, name, and time info.

        Args:
            idx: Index of script in chain
            entry: ChainEntry to display

        Returns:
            The created frame widget
        """
        # Box frame (styled like XP gained boxes)
        box = customtkinter.CTkFrame(
            self.scripts_container,
            fg_color="#2E2E2E",
            corner_radius=6,
            height=50,
        )
        box.pack(fill="x", padx=8, pady=4)
        box.pack_propagate(False)
        box.columnconfigure(1, weight=1)

        # Status icon (left side)
        icon = self._get_status_icon(entry.status)
        lbl_icon = customtkinter.CTkLabel(
            box,
            text=icon,
            font=("Roboto", 20),
            width=30,
        )
        lbl_icon.grid(row=0, column=0, rowspan=2, padx=(10, 5), sticky="w")

        # Script name (top right)
        lbl_name = customtkinter.CTkLabel(
            box,
            text=f"{idx + 1}. {entry.script_name}",
            font=("Roboto Medium", 13),
            text_color="#DCE4EE",
            anchor="w",
        )
        lbl_name.grid(row=0, column=1, sticky="ew", padx=5, pady=(8, 0))

        # Time info (bottom right) - will show duration or time remaining
        lbl_time = customtkinter.CTkLabel(
            box,
            text=f"Duration: {entry.running_time} min",
            font=("Roboto", 11),
            text_color="#A0A0A0",
            anchor="w",
        )
        lbl_time.grid(row=1, column=1, sticky="ew", padx=5, pady=(0, 8))

        # Progress indicator (right side) - only shown when running
        lbl_progress = customtkinter.CTkLabel(
            box,
            text="",
            font=("Roboto Medium", 11),
            text_color="#66BB6A",
            width=60,
        )
        lbl_progress.grid(row=0, column=2, rowspan=2, padx=(5, 10))

        # Store references for updates
        box.lbl_icon = lbl_icon
        box.lbl_name = lbl_name
        box.lbl_time = lbl_time
        box.lbl_progress = lbl_progress

        return box

    def _update_script_box(
        self,
        idx: int,
        entry: ChainEntry,
        progress: float = None,
        remaining_seconds: int = None,
    ):
        """
        Update a script box with current status and progress.

        Args:
            idx: Index of script in chain
            entry: ChainEntry with current status
            progress: Optional progress value (0.0 to 1.0)
            remaining_seconds: Optional seconds remaining
        """
        if idx >= len(self.script_boxes):
            return

        box = self.script_boxes[idx]

        # Update status icon
        icon = self._get_status_icon(entry.status)
        box.lbl_icon.configure(text=icon)

        # Update box color based on status
        if entry.status == ChainEntryStatus.RUNNING:
            box.configure(fg_color="#3A4A3A")  # Green tint for running
        elif entry.status == ChainEntryStatus.COMPLETED:
            box.configure(fg_color="#2E3E2E")  # Darker green for completed
        elif entry.status == ChainEntryStatus.FAILED:
            box.configure(fg_color="#4A2E2E")  # Red tint for failed
        else:
            box.configure(fg_color="#2E2E2E")  # Default gray

        # Update time/progress info
        if entry.status == ChainEntryStatus.RUNNING and remaining_seconds is not None:
            # Show time remaining when running
            minutes = int(remaining_seconds // 60)
            seconds = int(remaining_seconds % 60)
            box.lbl_time.configure(text=f"⏱ {minutes:02d}:{seconds:02d} remaining")

            # Show progress percentage
            if progress is not None:
                box.lbl_progress.configure(text=f"{progress * 100:.0f}%")
        elif entry.status == ChainEntryStatus.COMPLETED:
            box.lbl_time.configure(text=f"✓ Completed ({entry.running_time} min)")
            box.lbl_progress.configure(text="100%")
        elif entry.status == ChainEntryStatus.FAILED:
            box.lbl_time.configure(text=f"✗ Failed")
            box.lbl_progress.configure(text="")
        elif entry.status == ChainEntryStatus.SKIPPED:
            box.lbl_time.configure(text=f"⏭ Skipped")
            box.lbl_progress.configure(text="")
        else:
            # Pending - show duration
            box.lbl_time.configure(text=f"Duration: {entry.running_time} min")
            box.lbl_progress.configure(text="")

    def _get_status_icon(self, status: ChainEntryStatus) -> str:
        """
        Get emoji icon for a status.

        Args:
            status: ChainEntryStatus

        Returns:
            Emoji string
        """
        status_icons = {
            ChainEntryStatus.PENDING: "⏸",  # Paused (waiting)
            ChainEntryStatus.RUNNING: "▶",  # Playing (running)
            ChainEntryStatus.COMPLETED: "✅",  # Checkmark (done)
            ChainEntryStatus.SKIPPED: "⏭",  # Skip (skipped)
            ChainEntryStatus.FAILED: "❌",  # X (failed)
        }
        return status_icons.get(status, "⏸")

    def _on_stop_clicked(self):
        """Handle Stop button click."""
        if self.on_stop_command:
            self.on_stop_command()

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts to the root window."""
        if not self._shortcut_bound:
            try:
                # Get the root window (toplevel Tk/CTk window)
                root = self.winfo_toplevel()
                # Bind to the root window using standard tkinter bind
                root.bind("<Shift-Return>", self._on_shortcut_stop, add=True)
                self._shortcut_bound = True
            except Exception as e:
                print(f"[ChainExecutionPanel] Failed to bind shortcut: {e}")

    def _unbind_shortcuts(self):
        """Unbind keyboard shortcuts from the root window."""
        if self._shortcut_bound:
            try:
                root = self.winfo_toplevel()
                root.unbind("<Shift-Return>")
                self._shortcut_bound = False
            except Exception as e:
                print(f"[ChainExecutionPanel] Failed to unbind shortcut: {e}")

    def _on_shortcut_stop(self, event):
        """Handle SHIFT+ENTER keyboard shortcut."""
        self._on_stop_clicked()
        return "break"  # Prevent event propagation

    def destroy(self):
        """Cleanup before destroying panel."""
        # Unbind keyboard shortcuts
        self._unbind_shortcuts()
        super().destroy()
