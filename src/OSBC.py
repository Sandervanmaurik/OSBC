import importlib
import pathlib
import tkinter
import time
import sys
from typing import List

# Add the project root to the Python path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.absolute()))

import customtkinter
from PIL import Image, ImageTk
from pynput import keyboard
from tktooltip import ToolTip

from utilities import settings
from controller.bot_controller import BotController, MockBotController
from controller.chain_controller import ChainController
from model import Bot, RuneLiteBot
from utilities.game_launcher import Launchable
from utilities.random_util import truncated_normal_sample
from view import *
from view.fonts.fonts import *
from view.components import CollapsibleSidebar, ScriptMenuButton
from view.panels import (
    StatsPanel,
    ScriptPanel,
    WelcomePanel,
    ChainBuilderPanel,
    ChainExecutionPanel,
)
from utilities.machine_config import get_machine_config

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme(
    "blue"
)  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    DEFAULT_GRAY = ("gray50", "gray30")

    def __init_dimensions(self):
        """Initialize window dimensions from machine config."""
        config = get_machine_config()
        self.WIDTH, self.HEIGHT = config.get_app_dimensions()

    def __init__(self, test: bool = False):
        super().__init__()
        self.__init_dimensions()
        self.__init_settings()
        if not test:
            ui_images_path = (
                pathlib.Path(__file__).parent.resolve().joinpath("images", "ui")
            )
            self.img_rocket = ImageTk.PhotoImage(
                Image.open(ui_images_path.joinpath("rocket.png")).resize(
                    (12, 12), Image.Resampling.LANCZOS
                )
            )
            self.img_settings = ImageTk.PhotoImage(
                Image.open(ui_images_path.joinpath("options.png")).resize(
                    (12, 12), Image.Resampling.LANCZOS
                )
            )
            self.build_ui()

    def build_ui(self):  # sourcery skip: merge-list-append, move-assign-in-block
        self.title("OS Bot COLOR")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.update()
        self.minsize(self.winfo_width(), self.winfo_height())

        self.protocol(
            "WM_DELETE_WINDOW", self.on_closing
        )  # call .on_closing() when app gets closed

        # ============ Create 3-Panel Layout ============
        # Column 0: Sidebar (collapsible, 50-180px)
        # Column 1: Middle panel (expandable, script view or welcome)
        # Column 2: Stats panel (fixed width ~280px)

        self.grid_columnconfigure(0, weight=0, minsize=50)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Middle panel (expandable)
        self.grid_columnconfigure(2, weight=0, minsize=280)  # Stats panel
        self.grid_rowconfigure(0, weight=1)

        # ============ Initialize Panels ============
        # Create collapsible sidebar (left panel)
        from view.components.collapsible_sidebar import CollapsibleSidebar

        self.sidebar = CollapsibleSidebar(
            parent=self,
            on_toggle=self._on_sidebar_toggle,
            on_settings=self._on_settings_clicked,
            on_chain_builder=self._on_chain_builder_clicked,
        )
        self.sidebar.grid(row=0, column=0, sticky="nswe")

        # Create middle panel container
        self.middle_container = customtkinter.CTkFrame(
            master=self, fg_color="transparent"
        )
        self.middle_container.grid(row=0, column=1, sticky="nswe")
        self.middle_container.grid_columnconfigure(0, weight=1)
        self.middle_container.grid_rowconfigure(0, weight=1)

        # Create stats panel (right panel)
        from view.panels.stats_panel import StatsPanel

        self.stats_panel = StatsPanel(parent=self)
        self.stats_panel.grid(row=0, column=2, sticky="nswe")

        # ============ View/Controller Configuration ============
        self.models: dict[str, Bot] = {}  # Map of all bots, keyed by bot name

        # Create welcome panel (shown when no script selected)
        from view.panels.welcome_panel import WelcomePanel

        self.welcome_panel = WelcomePanel(parent=self.middle_container)
        self.welcome_panel.grid(row=0, column=0, sticky="nswe")

        # Create script panel (shown when script is selected)
        from view.panels.script_panel import ScriptPanel

        self.script_panel = ScriptPanel(
            parent=self.middle_container,
            play_command=self._on_play_clicked,
            stop_command=self._on_stop_clicked,
            options_command=self._on_options_clicked,
        )
        # Don't grid yet - will show when script selected

        # Create chain builder panel (shown when chain builder clicked)
        from view.panels.chain_builder_panel import ChainBuilderPanel

        self.chain_builder_panel = ChainBuilderPanel(
            parent=self.middle_container,
            models=self.models,
            on_run_chain=self._on_run_chain,
        )
        # Don't grid yet - will show when chain builder clicked

        # Create chain execution panel (shown during chain execution)
        from view.panels.chain_execution_panel import ChainExecutionPanel

        self.chain_execution_panel = ChainExecutionPanel(
            parent=self.middle_container,
            on_stop_command=self._on_stop_chain,
        )
        # Don't grid yet - will show when chain is running

        # Create controller (using legacy BotView for compatibility)
        # We'll wire the new panels to the controller below
        self.legacy_bot_view = BotView(parent=self.middle_container)
        self.controller = BotController(model=None, view=self.legacy_bot_view)
        self.legacy_bot_view.set_controller(self.controller)

        # Create chain controller
        self.chain_controller = ChainController(
            models=self.models,
            bot_controller=self.controller,
        )

        # Initialize chain callback flags
        self._chain_callbacks_active = False
        self._pending_script_progress_update = False
        self._pending_chain_progress_update = False

        self._wire_chain_callbacks()

        # Track application state
        self.current_view = (
            "welcome"  # "welcome", "script", "chain_builder", "chain_execution"
        )
        self.chain_running = False

        # ============ Bot Discovery and Sidebar Population ============
        # Dynamically import all OSRS bots and add them to the sidebar
        # Only OSRS bots are supported (no game selector dropdown)

        module = importlib.import_module("model")
        names = dir(module)

        # Track script buttons for selection management
        self.script_buttons: dict[str, any] = {}  # {bot_name: ScriptMenuButton}
        self.current_selected_bot: str = None  # Currently selected bot name

        for name in names:
            obj = getattr(module, name)
            if (
                obj is not Bot
                and obj is not RuneLiteBot
                and isinstance(obj, type)
                and issubclass(obj, Bot)
            ):
                instance = obj()

                # Only add OSRS bots (game_title == "OSRS")
                if instance.game_title != "OSRS":
                    continue

                # Set controller
                instance.set_controller(self.controller)
                self.models[name] = instance

                # Create script menu button with primary skill icon
                from view.components.script_menu_button import ScriptMenuButton

                primary_skill = getattr(
                    instance, "primary_skill", "attack"
                )  # Default to attack if not set

                script_button = ScriptMenuButton(
                    parent=self.sidebar.get_scripts_frame(),
                    script_name=instance.bot_title,
                    primary_skill=primary_skill,
                    command=lambda bot_name=name: self._on_script_selected(bot_name),
                    is_collapsed=False,
                )

                # Add button to sidebar
                self.sidebar.add_script_button(name, script_button)
                self.script_buttons[name] = script_button

    # ============ Event Handlers ============
    def _on_sidebar_toggle(self, is_collapsed: bool):
        """
        Handle sidebar collapse/expand.
        Updates sidebar width constraint.
        """
        if is_collapsed:
            self.grid_columnconfigure(0, minsize=50, weight=0)
        else:
            self.grid_columnconfigure(0, minsize=180, weight=0)

    def _on_script_selected(self, bot_name: str):
        """
        Handle script selection from sidebar.
        Shows script panel and loads bot into controller.
        """
        # Check if chain builder is in Add Mode
        if (
            self.current_view == "chain_builder"
            and self.chain_builder_panel.add_mode_active
        ):
            self.chain_builder_panel.add_script(bot_name)
            return

        # Check if navigation is blocked (chain running)
        if not self._can_navigate():
            return

        bot = self.models.get(bot_name)
        if not bot:
            return

        # If same script is selected, deselect it
        if self.current_selected_bot == bot_name:
            self._deselect_script()
            return

        # Update selection state
        self.current_selected_bot = bot_name
        self.sidebar.set_script_selected(bot_name, selected=True)

        # Hide other panels, show script panel
        self.welcome_panel.grid_forget()
        self.chain_builder_panel.grid_forget()
        self.chain_execution_panel.grid_forget()
        self.script_panel.grid(row=0, column=0, sticky="nswe")
        self.current_view = "script"

        # Update script panel info
        self.script_panel.set_script_info(
            title=bot.bot_title,
            description=bot.description,
        )

        # IMPORTANT: Wire the script_panel's frames to match what BotController expects
        # Create a view adapter that exposes the interface BotController needs
        self._create_view_adapter()

        # Change model in controller
        self.controller.change_model(bot)

    def _create_view_adapter(self):
        """
        Create a simple adapter so BotController can access our new panels.
        The controller expects view.frame_info, view.frame_skills, view.frame_output_log, etc.
        """
        script_panel = self.script_panel
        stats_panel = self.stats_panel
        legacy_view = self.legacy_bot_view

        # Create a simple wrapper object that the controller can use
        class ViewAdapter:
            def __init__(adapter_self):
                # Use script_panel's frames for log and behavior
                adapter_self.frame_output_log = script_panel.get_log_frame()
                adapter_self.frame_behavior = script_panel.get_behavior_frame()

                # Use stats_panel's skills frame
                adapter_self.frame_skills = stats_panel.get_skills_frame()

                # For frame_info, create a wrapper that delegates to both
                # the legacy frame_info and our script_panel
                adapter_self.frame_info = adapter_self._create_info_frame_wrapper(
                    legacy_view.frame_info, script_panel
                )

            def _create_info_frame_wrapper(adapter_self, legacy_info, script_panel):
                """Create a wrapper for InfoFrame that updates both legacy and new UI."""

                class InfoFrameWrapper:
                    def __init__(self):
                        self.legacy = legacy_info
                        self.script_panel = script_panel

                    def update_progress(self, progress):
                        # Update both legacy (for keyboard listener, etc) and new panel
                        self.legacy.update_progress(progress)
                        self.script_panel.update_progress(progress)

                    def update_status_running(self):
                        self.legacy.update_status_running()
                        # Update control bar to show Stop button
                        self.script_panel.get_control_bar()._update_buttons("running")

                    def update_status_stopped(self):
                        self.legacy.update_status_stopped()
                        # Update control bar to show Play button
                        self.script_panel.get_control_bar()._update_buttons("stopped")

                    def update_status_configuring(self):
                        self.legacy.update_status_configuring()

                    def update_status_configured(self):
                        self.legacy.update_status_configured()

                    def update_state(self, state):
                        self.legacy.update_state(state)
                        # State is also visible in CurrentActionCard via BotSessionState

                    def setup(self, title, description):
                        self.legacy.setup(title, description)
                        # Script panel already shows title/description

                    def start_keyboard_listener(self):
                        self.legacy.start_keyboard_listener()

                    def stop_keyboard_listener(self):
                        self.legacy.stop_keyboard_listener()

                return InfoFrameWrapper()

            def update_behavior_display(adapter_self, behavior_config, stats):
                """Forward behavior updates to the behavior frame."""
                adapter_self.frame_behavior.update_behavior_display(
                    behavior_config, stats
                )

        # Replace the controller's view with our adapter
        self.controller.view = ViewAdapter()

    def _deselect_script(self):
        """Deselect current script and show welcome panel."""
        if self.current_selected_bot:
            self.sidebar.set_script_selected(self.current_selected_bot, selected=False)
            self.current_selected_bot = None

        # Hide all panels except welcome
        self.script_panel.grid_forget()
        self.chain_builder_panel.grid_forget()
        self.chain_execution_panel.grid_forget()
        self.welcome_panel.grid(row=0, column=0, sticky="nswe")
        self.current_view = "welcome"

        # Unlink model from controller
        if self.controller.model:
            self.controller.model.progress = 0
            self.controller.update_progress()
            self.controller.change_model(None)

    def _on_play_clicked(self):
        """Handle Play button click."""
        if self.controller:
            self.controller.play()

    def _on_stop_clicked(self):
        """Handle Stop button click."""
        if self.controller:
            self.controller.stop()

    def _on_options_clicked(self):
        """Handle Options button click - opens bot options dialog."""
        if not self.controller or not self.controller.model:
            return

        window = customtkinter.CTkToplevel(master=self)
        window.title("Options")
        window.protocol("WM_DELETE_WINDOW", lambda: self._on_options_closing(window))

        view = self.controller.get_options_view(parent=window)
        view.pack(side="top", fill="both", expand=True, padx=20, pady=20)
        window.after(100, window.lift)

    def _on_options_closing(self, window):
        """Handle options window closing."""
        window.destroy()
        # Re-enable controls if needed

    # ============ Chain Integration Methods ============
    def _on_chain_builder_clicked(self):
        """Handle Chain Builder button click from sidebar."""
        # Check if navigation is blocked
        if not self._can_navigate():
            return

        # Deselect any selected script
        if self.current_selected_bot:
            self.sidebar.set_script_selected(self.current_selected_bot, selected=False)
            self.current_selected_bot = None

        # Hide other panels, show chain builder
        self.welcome_panel.grid_forget()
        self.script_panel.grid_forget()
        self.chain_execution_panel.grid_forget()
        self.chain_builder_panel.grid(row=0, column=0, sticky="nswe")
        self.current_view = "chain_builder"

    def _on_run_chain(self, chain):
        """Handle Run Chain button click from ChainBuilderPanel."""
        # Enable callbacks for new chain run
        self._chain_callbacks_active = True
        self._pending_script_progress_update = False
        self._pending_chain_progress_update = False

        # Update state
        self.chain_running = True

        # Switch to chain execution panel
        self.chain_builder_panel.grid_forget()
        self.chain_execution_panel.grid(row=0, column=0, sticky="nswe")
        self.current_view = "chain_execution"

        # Set chain in execution panel
        self.chain_execution_panel.set_chain(chain)

        # Clear the log for new chain run
        self.chain_execution_panel.clear_log()

        # Start chain execution
        self.chain_controller.run_chain(chain)

    def _on_stop_chain(self):
        """Handle Stop Chain button click from ChainExecutionPanel."""
        self.chain_controller.stop_chain()

    def _wire_chain_callbacks(self):
        """Wire ChainController callbacks to UI updates (thread-safe)."""
        # Chain started
        self.chain_controller.on_chain_started = lambda: self.after(
            0, self._on_chain_started_callback
        )

        # Window initialization (must run on main thread)
        def init_window_wrapper(bot):
            self.after(0, lambda: self._on_init_window_callback(bot))

        self.chain_controller.on_init_window = init_window_wrapper

        # Script started - use default args to capture values
        self.chain_controller.on_script_started = lambda entry, index: self.after(
            0, lambda e=entry, i=index: self._on_script_started_callback(e, i)
        )

        # Script progress - use default args and throttle with flag
        def on_progress_wrapper(progress, remaining):
            try:
                if (
                    self._chain_callbacks_active
                    and not self._pending_script_progress_update
                ):
                    self._pending_script_progress_update = True
                    self.after(
                        0,
                        lambda p=progress,
                        r=remaining: self._on_script_progress_callback_throttled(p, r),
                    )
            except Exception as e:
                print(f"[ERROR] Progress wrapper error: {e}")

        self.chain_controller.on_script_progress = on_progress_wrapper

        # Chain progress - use default args and throttle with flag
        def on_chain_progress_wrapper(progress):
            try:
                if (
                    self._chain_callbacks_active
                    and not self._pending_chain_progress_update
                ):
                    self._pending_chain_progress_update = True
                    self.after(
                        0,
                        lambda p=progress: self._on_chain_progress_callback_throttled(
                            p
                        ),
                    )
            except Exception as e:
                print(f"[ERROR] Chain progress wrapper error: {e}")

        self.chain_controller.on_chain_progress = on_chain_progress_wrapper

        # Script completed - use default args to capture values
        self.chain_controller.on_script_completed = lambda entry, xp: self.after(
            0, lambda e=entry, x=xp: self._on_script_completed_callback(e, x)
        )

        # Script skipped - use default args to capture values
        self.chain_controller.on_script_skipped = lambda entry, reason: self.after(
            0, lambda e=entry, r=reason: self._on_script_skipped_callback(e, r)
        )

        # Chain completed - use default args to capture value
        self.chain_controller.on_chain_completed = lambda chain: self.after(
            0, lambda c=chain: self._on_chain_completed_callback(c)
        )

        # Chain stopped
        self.chain_controller.on_chain_stopped = lambda: self.after(
            0, self._on_chain_stopped_callback
        )

        # Log update - use default args to capture values
        self.chain_controller.on_log_update = lambda msg, overwrite: self.after(
            0, lambda m=msg, o=overwrite: self._on_chain_log_update_callback(m, o)
        )

    # ============ Chain Callback Implementations ============

    def _on_script_progress_callback_throttled(self, progress, remaining_seconds):
        """Handle script progress update with throttling (on main thread)."""
        self.chain_execution_panel.update_current_progress(progress, remaining_seconds)
        self._pending_script_progress_update = False  # Allow next update

    def _on_chain_progress_callback_throttled(self, progress):
        """Handle overall chain progress update with throttling (on main thread)."""
        self.chain_execution_panel.update_overall_progress(progress)
        self._pending_chain_progress_update = False  # Allow next update

    def _on_chain_log_update_callback(self, msg, overwrite):
        """Handle script log update (on main thread)."""
        if self._chain_callbacks_active:
            self.chain_execution_panel.update_log(msg, overwrite)

    def _on_init_window_callback(self, bot):
        """Initialize bot window on main thread (thread-safe)."""
        try:
            bot.win.focus()
            bot.win.initialize()
        except Exception as e:
            print(f"[ERROR] Window initialization error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            # Signal that initialization is complete
            self.chain_controller._window_init_event.set()

    def _on_chain_started_callback(self):
        """Handle chain started (on main thread)."""
        pass  # UI already updated in _on_run_chain

    def _on_script_started_callback(self, entry, index):
        """Handle script started (on main thread)."""
        self.chain_execution_panel.update_current_script(entry, index)
        self.chain_execution_panel.update_script_status(index, entry.status)

    def _on_script_completed_callback(self, entry, xp_gained):
        """Handle script completion (on main thread)."""
        # Find index of entry
        if self.chain_controller.current_chain:
            for idx, e in enumerate(self.chain_controller.current_chain.entries):
                if e is entry:
                    self.chain_execution_panel.update_script_status(idx, entry.status)
                    break

    def _on_script_skipped_callback(self, entry, reason):
        """Handle script skipped (on main thread)."""
        # Find index of entry
        if self.chain_controller.current_chain:
            for idx, e in enumerate(self.chain_controller.current_chain.entries):
                if e is entry:
                    self.chain_execution_panel.update_script_status(idx, entry.status)
                    break

    def _on_chain_completed_callback(self, chain):
        """Handle chain completion (on main thread)."""
        from view.components.chain_summary_dialog import ChainSummaryDialog

        # Disable callbacks to stop processing queued events
        self._chain_callbacks_active = False

        # Update state
        self.chain_running = False

        # Get accumulated XP from chain controller
        total_xp = self.chain_controller.chain_xp_gained.copy()

        # Show summary dialog
        dialog = ChainSummaryDialog(
            parent=self,
            chain=chain,
            total_xp=total_xp,
            on_run_again=lambda: self._on_run_chain_again(chain),
        )

        # Return to chain builder
        self.chain_execution_panel.hide()  # Unbind shortcuts before hiding
        self.chain_execution_panel.grid_forget()
        self.chain_builder_panel.grid(row=0, column=0, sticky="nswe")
        self.current_view = "chain_builder"

    def _on_chain_stopped_callback(self):
        """Handle chain stopped (on main thread)."""
        # Disable callbacks to stop processing queued events
        self._chain_callbacks_active = False

        # Update state
        self.chain_running = False

        # Return to chain builder
        self.chain_execution_panel.hide()  # Unbind shortcuts before hiding
        self.chain_execution_panel.grid_forget()
        self.chain_builder_panel.grid(row=0, column=0, sticky="nswe")
        self.current_view = "chain_builder"

    def _on_run_chain_again(self, chain):
        """Handle Run Again from summary dialog."""
        # Reset chain and run again
        chain.reset_status()
        self._on_run_chain(chain)

    def _can_navigate(self) -> bool:
        """Check if navigation is allowed. Shows warning if blocked."""
        if self.chain_running:
            self._show_navigation_warning()
            return False
        return True

    def _show_navigation_warning(self):
        """Show warning dialog when navigation is blocked."""
        dialog = customtkinter.CTkToplevel(self)
        dialog.title("Cannot Navigate")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()

        lbl = customtkinter.CTkLabel(
            dialog,
            text="A chain is currently running.\nPlease stop the chain before navigating.",
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

    # ============ Settings Init ============
    def __init_settings(self):
        """
        Initializes the settings for the application.
        """
        # If "keybind" doesn't exist, add default
        keybind = settings.get("keybind")
        if keybind is None:
            settings.set("keybind", settings.default_keybind)

    def _on_settings_clicked(self):
        """Open settings dialog."""
        window = customtkinter.CTkToplevel(master=self)
        window.geometry("540x287")
        window.title("Settings")
        view = SettingsView(parent=window)
        view.pack(side="top", fill="both", expand=True, padx=20, pady=20)
        window.after(100, window.lift)

    # ============ Misc Handlers ============
    def on_closing(self, event=0):
        self.destroy()

    def start(self):
        self.mainloop()

    # ============ UI-less Test Functions ============
    def test(self, bot: Bot) -> None:
        bot.set_controller(MockBotController(bot))
        bot.options_set = True
        self.listener = keyboard.Listener(
            on_press=lambda event: self.__on_press(event, bot),
            on_release=None,
        )
        self.listener.start()
        bot.play()
        self.listener.join()

    def __on_press(self, key: keyboard.Key, bot: Bot) -> None:
        if key == keyboard.Key.ctrl_l:
            bot.thread.stop()
            self.listener.stop()


if __name__ == "__main__":
    # To test a bot without the GUI, address the comments for each line below.
    # from model.<folder_bot_is_in> import <bot_class_name>  # Uncomment this line and replace <folder_bot_is_in> and <bot_class_name> accordingly to import your bot
    app = App()  # Add the "test=True" argument to the App constructor call.
    app.start()  # Comment out this line.
    # app.test(Bot())  # Uncomment this line and replace argument with your bot's instance.

    # IMPORTANT
    # - Make sure your bot's options are pre-defined in its __init__ method.
    # - You can stop the bot by pressing `Left Ctrl`
