"""
ChainBuilderPanel - UI for creating and managing script chains.
Allows users to build sequences of bot scripts with custom durations and options.
"""

import customtkinter
from typing import Dict, Callable, Optional
from model.chain import ScriptChain, ChainEntry, save_chains, load_chains
from view.components.chain_entry_card import ChainEntryCard


class ChainBuilderPanel(customtkinter.CTkFrame):
    """
    Panel for building and editing script chains.

    Features:
        - Chain name input
        - Add Mode toggle for adding scripts from sidebar
        - Scrollable list of chain entries (ChainEntryCard widgets)
        - Save/Load/Clear chain functionality
        - Run Chain button to start execution
        - Total duration display
    """

    def __init__(
        self,
        parent,
        models: Dict[str, any],  # Map of bot_name -> Bot instance
        on_run_chain: Callable[
            [ScriptChain], None
        ],  # Callback when Run Chain is clicked
    ):
        """
        Args:
            parent: Parent widget
            models: Dictionary of all bot instances {bot_name: Bot}
            on_run_chain: Callback function when chain execution is requested
        """
        super().__init__(parent, fg_color="#1A1A1A", corner_radius=0)

        self.models = models
        self.on_run_chain = on_run_chain

        # Current state
        self.current_chain: Optional[ScriptChain] = None
        self.add_mode_active = False
        self.entry_cards: list[ChainEntryCard] = []  # Currently displayed cards

        # Configure layout
        self.rowconfigure(0, weight=0)  # Header
        self.rowconfigure(1, weight=0)  # Add mode toggle
        self.rowconfigure(2, weight=1)  # Scrollable entries list
        self.rowconfigure(3, weight=0)  # Footer buttons
        self.columnconfigure(0, weight=1)

        # ============ Header: Chain Name ============
        header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        header_frame.columnconfigure(1, weight=1)

        self.lbl_chain_name = customtkinter.CTkLabel(
            header_frame,
            text="Chain Name:",
            font=("Roboto Medium", 14),
            text_color="#DCE4EE",
            anchor="w",
        )
        self.lbl_chain_name.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.entry_chain_name = customtkinter.CTkEntry(
            header_frame,
            placeholder_text="Enter chain name...",
            font=("Roboto", 13),
            height=32,
        )
        self.entry_chain_name.grid(row=0, column=1, sticky="ew")

        # ============ Add Mode Toggle ============
        add_mode_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        add_mode_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 10))

        self.btn_add_mode = customtkinter.CTkButton(
            add_mode_frame,
            text="🔗 Add Mode: OFF",
            font=("Roboto Medium", 13),
            fg_color="#2E2E2E",
            hover_color="#3E3E3E",
            command=self._toggle_add_mode,
            height=36,
        )
        self.btn_add_mode.grid(row=0, column=0, sticky="w")

        self.lbl_add_mode_hint = customtkinter.CTkLabel(
            add_mode_frame,
            text="Click a script in the sidebar to add it to the chain",
            font=("Roboto", 11),
            text_color="#707070",
            anchor="w",
        )
        self.lbl_add_mode_hint.grid(row=0, column=1, sticky="w", padx=(15, 0))

        # ============ Scrollable Entries List ============
        self.scrollable_frame = customtkinter.CTkScrollableFrame(
            self,
            fg_color="#0F0F0F",
            corner_radius=8,
        )
        self.scrollable_frame.grid(
            row=2, column=0, sticky="nsew", padx=20, pady=(0, 10)
        )
        self.scrollable_frame.columnconfigure(0, weight=1)

        # Empty state label
        self.lbl_empty = customtkinter.CTkLabel(
            self.scrollable_frame,
            text="No scripts added yet.\nEnable Add Mode and click scripts from the sidebar.",
            font=("Roboto", 13),
            text_color="#606060",
            justify="center",
        )
        self.lbl_empty.grid(row=0, column=0, pady=50)

        # ============ Footer: Buttons & Total Time ============
        footer_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))
        footer_frame.columnconfigure(4, weight=1)  # Push buttons left, total time right

        # Save button
        self.btn_save = customtkinter.CTkButton(
            footer_frame,
            text="💾 Save",
            font=("Roboto Medium", 13),
            fg_color="#2E7D32",
            hover_color="#388E3C",
            command=self._save_chain,
            width=100,
            height=36,
        )
        self.btn_save.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # Load button (with dropdown)
        self.btn_load = customtkinter.CTkButton(
            footer_frame,
            text="📂 Load",
            font=("Roboto Medium", 13),
            fg_color="#1976D2",
            hover_color="#2196F3",
            command=self._show_load_menu,
            width=100,
            height=36,
        )
        self.btn_load.grid(row=0, column=1, sticky="w", padx=(0, 10))

        # Clear button
        self.btn_clear = customtkinter.CTkButton(
            footer_frame,
            text="🗑️ Clear",
            font=("Roboto Medium", 13),
            fg_color="#C62828",
            hover_color="#D32F2F",
            command=self._clear_chain,
            width=100,
            height=36,
        )
        self.btn_clear.grid(row=0, column=2, sticky="w", padx=(0, 10))

        # Run Chain button
        self.btn_run = customtkinter.CTkButton(
            footer_frame,
            text="▶️ Run Chain",
            font=("Roboto Medium", 14),
            fg_color="#4A90E2",
            hover_color="#5BA3F5",
            command=self._run_chain,
            width=140,
            height=36,
        )
        self.btn_run.grid(row=0, column=3, sticky="w", padx=(0, 20))

        # Total time display
        self.lbl_total_time = customtkinter.CTkLabel(
            footer_frame,
            text="Total: 0 min",
            font=("Roboto Medium", 13),
            text_color="#DCE4EE",
            anchor="e",
        )
        self.lbl_total_time.grid(row=0, column=4, sticky="e")

        # Initialize with empty chain
        self._create_empty_chain()

    # ============ Public API ============

    def set_add_mode(self, active: bool):
        """
        Toggle Add Mode on/off.

        Args:
            active: True to enable add mode, False to disable
        """
        self.add_mode_active = active
        if active:
            self.btn_add_mode.configure(
                text="🔗 Add Mode: ON",
                fg_color="#2E7D32",
                hover_color="#388E3C",
            )
        else:
            self.btn_add_mode.configure(
                text="🔗 Add Mode: OFF",
                fg_color="#2E2E2E",
                hover_color="#3E3E3E",
            )

    def add_script(self, bot_name: str):
        """
        Add a script to the current chain.
        Called from OSBC when sidebar script is clicked in Add Mode.

        Args:
            bot_name: Name of the bot class (e.g., "OSRSFishing")
        """
        if not self.add_mode_active:
            return

        bot = self.models.get(bot_name)
        if not bot:
            return

        # Create new entry with default values
        entry = ChainEntry(
            script_name=bot_name,
            running_time=10,  # Default 10 minutes
            options={},  # Empty options (user must configure)
        )

        # Add to chain
        self.current_chain.add_entry(entry)

        # Refresh display
        self._refresh_entries()
        self._update_total_time()

    # ============ Private Methods ============

    def _create_empty_chain(self):
        """Create a new empty chain."""
        self.current_chain = ScriptChain(name="")
        self._refresh_entries()
        self._update_total_time()

    def _toggle_add_mode(self):
        """Toggle Add Mode on/off."""
        self.set_add_mode(not self.add_mode_active)

    def _refresh_entries(self):
        """Rebuild the list of entry cards."""
        # Clear existing cards
        for card in self.entry_cards:
            card.destroy()
        self.entry_cards.clear()

        # Show/hide empty state
        if not self.current_chain.entries:
            self.lbl_empty.grid(row=0, column=0, pady=50)
            return
        else:
            self.lbl_empty.grid_forget()

        # Create card for each entry
        for idx, entry in enumerate(self.current_chain.entries):
            card = ChainEntryCard(
                parent=self.scrollable_frame,
                entry=entry,
                on_configure=lambda e=entry: self._configure_entry(e),
                on_delete=lambda e=entry: self._remove_entry(e),
                on_move_up=lambda e=entry: self._move_entry_up(e),
                on_move_down=lambda e=entry: self._move_entry_down(e),
            )
            card.grid(row=idx, column=0, sticky="ew", padx=10, pady=5)
            self.entry_cards.append(card)

            # Update up/down button states
            is_first = idx == 0
            is_last = idx == len(self.current_chain.entries) - 1
            card.update_move_buttons(is_first, is_last)

    def _configure_entry(self, entry: ChainEntry):
        """
        Open options dialog for a chain entry.

        Args:
            entry: ChainEntry to configure
        """
        bot = self.models.get(entry.script_name)
        if not bot:
            return

        # Create options window
        options_window = customtkinter.CTkToplevel(self)
        options_window.title(f"Configure {bot.bot_title}")
        options_window.geometry("600x500")
        options_window.transient(self)
        options_window.grab_set()

        # Build options UI using bot's create_options method
        options_builder = bot.create_options()
        if options_builder:
            # Temporarily override controller to capture options
            temp_controller = _OptionsCapture(entry)
            options_ui = options_builder.build_ui(options_window, temp_controller)
            options_ui.pack(fill="both", expand=True, padx=10, pady=10)

            # Pre-fill existing options if any
            if entry.options:
                _prefill_options(options_ui, entry.options)

    def _remove_entry(self, entry: ChainEntry):
        """Remove an entry from the chain."""
        # Find index
        idx = next(
            (i for i, e in enumerate(self.current_chain.entries) if e is entry),
            None,
        )
        if idx is not None:
            self.current_chain.remove_entry(idx)
            self._refresh_entries()
            self._update_total_time()

    def _move_entry_up(self, entry: ChainEntry):
        """Move an entry up in the chain."""
        idx = next(
            (i for i, e in enumerate(self.current_chain.entries) if e is entry),
            None,
        )
        if idx is not None and idx > 0:
            self.current_chain.reorder(idx, idx - 1)
            self._refresh_entries()

    def _move_entry_down(self, entry: ChainEntry):
        """Move an entry down in the chain."""
        idx = next(
            (i for i, e in enumerate(self.current_chain.entries) if e is entry),
            None,
        )
        if idx is not None and idx < len(self.current_chain.entries) - 1:
            self.current_chain.reorder(idx, idx + 1)
            self._refresh_entries()

    def _update_total_time(self):
        """Update the total time display."""
        total_min = self.current_chain.total_time_minutes()
        hours = total_min // 60
        minutes = total_min % 60
        if hours > 0:
            time_str = f"{hours}h {minutes}m"
        else:
            time_str = f"{minutes}m"
        self.lbl_total_time.configure(text=f"Total: {time_str}")

    def _save_chain(self):
        """Save the current chain to disk."""
        # Validate chain name
        chain_name = self.entry_chain_name.get().strip()
        if not chain_name:
            # Show error dialog
            self._show_error("Chain name cannot be empty")
            return

        if not self.current_chain.entries:
            self._show_error("Chain must have at least one script")
            return

        # Update chain name
        self.current_chain.name = chain_name

        # Load existing chains
        chains = load_chains()

        # Add/update this chain
        chains[chain_name] = self.current_chain

        # Save to disk
        save_chains(chains)

        # Show success
        self._show_success(f"Chain '{chain_name}' saved successfully!")

    def _show_load_menu(self):
        """Show a menu to select and load a saved chain."""
        chains = load_chains()

        if not chains:
            self._show_error("No saved chains found")
            return

        # Create dropdown menu window
        load_window = customtkinter.CTkToplevel(self)
        load_window.title("Load Chain")
        load_window.geometry("400x300")
        load_window.transient(self)
        load_window.grab_set()

        # Title
        lbl_title = customtkinter.CTkLabel(
            load_window,
            text="Select a chain to load:",
            font=("Roboto Medium", 14),
        )
        lbl_title.pack(pady=(20, 10))

        # Scrollable list of chains
        scroll_frame = customtkinter.CTkScrollableFrame(load_window)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        for chain_name, chain in chains.items():
            btn = customtkinter.CTkButton(
                scroll_frame,
                text=f"{chain_name} ({len(chain.entries)} scripts, {chain.total_time_minutes()} min)",
                font=("Roboto", 12),
                command=lambda c=chain: self._load_chain(c, load_window),
            )
            btn.pack(fill="x", pady=5)

    def _load_chain(self, chain: ScriptChain, window):
        """Load a chain into the builder."""
        self.current_chain = chain
        self.entry_chain_name.delete(0, "end")
        self.entry_chain_name.insert(0, chain.name)
        self._refresh_entries()
        self._update_total_time()
        window.destroy()

    def _clear_chain(self):
        """Clear all entries and reset chain."""
        self.entry_chain_name.delete(0, "end")
        self._create_empty_chain()

    def _run_chain(self):
        """Validate and execute the chain."""
        # Validate
        if not self.current_chain.entries:
            self._show_error("Chain is empty. Add at least one script.")
            return

        # Check if all entries are configured
        for entry in self.current_chain.entries:
            if not entry.options:
                bot = self.models.get(entry.script_name)
                bot_title = bot.bot_title if bot else entry.script_name
                self._show_error(
                    f"Script '{bot_title}' is not configured.\nClick the ⚙️ button to configure it."
                )
                return

        # Reset statuses
        self.current_chain.reset_status()

        # Call callback
        self.on_run_chain(self.current_chain)

    def _show_error(self, message: str):
        """Show error dialog."""
        dialog = customtkinter.CTkToplevel(self)
        dialog.title("Error")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()

        lbl = customtkinter.CTkLabel(
            dialog,
            text=message,
            font=("Roboto", 13),
            wraplength=350,
        )
        lbl.pack(pady=20)

        btn = customtkinter.CTkButton(
            dialog,
            text="OK",
            command=dialog.destroy,
            width=100,
        )
        btn.pack(pady=10)

    def _show_success(self, message: str):
        """Show success dialog."""
        dialog = customtkinter.CTkToplevel(self)
        dialog.title("Success")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()

        lbl = customtkinter.CTkLabel(
            dialog,
            text=message,
            font=("Roboto", 13),
            text_color="#4CAF50",
        )
        lbl.pack(pady=20)

        btn = customtkinter.CTkButton(
            dialog,
            text="OK",
            command=dialog.destroy,
            fg_color="#2E7D32",
            width=100,
        )
        btn.pack(pady=10)


# ============ Helper Classes ============


class _OptionsCapture:
    """
    Temporary controller that captures options when Save is clicked.
    Used to extract options from the OptionsUI without full controller.
    """

    def __init__(self, entry: ChainEntry):
        self.entry = entry

    def save_options(self, options: dict):
        """Capture options into the chain entry."""
        self.entry.options = options


def _prefill_options(options_ui, options: dict):
    """
    Pre-fill an OptionsUI with existing values.

    Args:
        options_ui: OptionsUI instance
        options: Dictionary of option values
    """
    for key, value in options.items():
        widget = options_ui.widgets.get(key)
        if widget is None:
            continue

        if isinstance(widget, customtkinter.CTkSlider):
            widget.set(value / 100)
            options_ui.change_slider_val(key, value / 100)
        elif isinstance(widget, list):  # Checkboxes
            for checkbox in widget:
                if checkbox.cget("text") in value:
                    checkbox.select()
        elif isinstance(widget, customtkinter.CTkOptionMenu):
            widget.set(value)
        elif isinstance(widget, customtkinter.CTkEntry):
            widget.delete(0, "end")
            widget.insert(0, value)
