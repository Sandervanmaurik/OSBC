import importlib
import pathlib
import tkinter
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
from model import Bot, RuneLiteBot
from utilities.game_launcher import Launchable
from view import *
from view.fonts.fonts import *
from view.components import CollapsibleSidebar, ScriptMenuButton
from view.panels import StatsPanel, ScriptPanel, WelcomePanel
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

        # Create controller (using legacy BotView for compatibility)
        # We'll wire the new panels to the controller below
        self.legacy_bot_view = BotView(parent=self.middle_container)
        self.controller = BotController(model=None, view=self.legacy_bot_view)
        self.legacy_bot_view.set_controller(self.controller)

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

        # Hide welcome panel, show script panel
        self.welcome_panel.grid_forget()
        self.script_panel.grid(row=0, column=0, sticky="nswe")

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

        # Hide script panel, show welcome panel
        self.script_panel.grid_forget()
        self.welcome_panel.grid(row=0, column=0, sticky="nswe")

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
