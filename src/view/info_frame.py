import pathlib
import tkinter

import customtkinter
from PIL import Image, ImageTk
from pynput import keyboard

import utilities.settings as settings
from utilities.game_launcher import Launchable
from view.fonts.fonts import *
from model.bot_session_state import BotSessionState


class InfoFrame(customtkinter.CTkFrame):
    listener = None
    pressed = False
    current_keys = set()
    combination_keys = settings.get("keybind") or settings.default_keybind
    status = "stopped"

    def __init__(self, parent, title, info):
        """
        Creates a frame with the following widgets:
            - script title (label)
            - script description (label)
            - script progress bar (progressbar)
            - right-side controls title (label)
            - right-side control buttons (buttons)
        Note: Skills display has been moved to SkillsFrame in bot_view.py
        """
        super().__init__(parent)

        PATH = pathlib.Path(__file__).parent.parent.resolve()

        # Configure grid - removed skills row
        self.rowconfigure((0, 2, 3, 4, 5, 6, 7), weight=0)  # rows will not resize
        self.rowconfigure(1, weight=1)  # description row will resize
        self.columnconfigure(0, weight=1, minsize=200)
        self.columnconfigure(1, weight=0)

        # -- script title
        self.lbl_script_title = customtkinter.CTkLabel(
            master=self,
            text=title,
            font=subheading_font(),
            justify=tkinter.LEFT,
        )
        self.lbl_script_title.grid(column=0, row=0, sticky="wns", padx=20, pady=15)

        # -- script description
        self.lbl_script_desc = customtkinter.CTkLabel(
            master=self, text=info, font=body_med_font(), justify=tkinter.CENTER
        )
        self.lbl_script_desc.grid(column=0, row=1, sticky="nwes", padx=15)
        self.lbl_script_desc.bind(
            "<Configure>",
            lambda e: self.lbl_script_desc.configure(
                wraplength=self.lbl_script_desc.winfo_width() - 10
            ),
        )

        # -- session stats (row 2-3)
        self.stats_frame = customtkinter.CTkFrame(master=self, fg_color=self._fg_color)
        self.stats_frame.grid(
            row=2, column=0, rowspan=2, sticky="ew", padx=15, pady=(10, 5)
        )
        self.stats_frame.columnconfigure(0, weight=0)
        self.stats_frame.columnconfigure(1, weight=1)

        # Action row
        self.lbl_action_name = customtkinter.CTkLabel(
            master=self.stats_frame,
            text="Action:",
            font=small_font(),
            width=80,
            anchor="w",
        )
        self.lbl_action_name.grid(row=0, column=0, padx=(0, 10), pady=2, sticky="w")

        self.lbl_action_value = customtkinter.CTkLabel(
            master=self.stats_frame, text="Idle", font=small_font(), anchor="w"
        )
        self.lbl_action_value.grid(row=0, column=1, pady=2, sticky="w")

        # XP Gained row
        self.lbl_xp_name = customtkinter.CTkLabel(
            master=self.stats_frame,
            text="XP Gained:",
            font=small_font(),
            width=80,
            anchor="w",
        )
        self.lbl_xp_name.grid(row=1, column=0, padx=(0, 10), pady=2, sticky="w")

        self.lbl_xp_value = customtkinter.CTkLabel(
            master=self.stats_frame, text="0", font=small_font(), anchor="w"
        )
        self.lbl_xp_value.grid(row=1, column=1, pady=2, sticky="w")

        # Subscribe to state changes
        BotSessionState().add_observer(self._on_session_state_changed)

        # -- script progress bar
        self.lbl_progress = customtkinter.CTkLabel(
            master=self, text="Progress: 0%", font=small_font(), justify=tkinter.CENTER
        )
        self.lbl_progress.grid(row=4, column=0, pady=(15, 0), sticky="ew")

        self.progressbar = customtkinter.CTkProgressBar(master=self)
        self.progressbar.grid(row=5, column=0, sticky="ew", padx=15, pady=(0, 15))
        self.progressbar.set(0)

        # -- right-side control buttons
        # -- images
        img_size = 18
        self.img_play = ImageTk.PhotoImage(
            Image.open(f"{PATH}/images/ui/play.png").resize(
                (img_size, img_size), Image.Resampling.LANCZOS
            ),
        )
        self.img_stop = ImageTk.PhotoImage(
            Image.open(f"{PATH}/images/ui/stop2.png").resize(
                (img_size, img_size), Image.Resampling.LANCZOS
            ),
        )
        self.img_options = ImageTk.PhotoImage(
            Image.open(f"{PATH}/images/ui/options2.png").resize(
                (img_size, img_size), Image.Resampling.LANCZOS
            ),
        )
        self.img_start = ImageTk.PhotoImage(
            Image.open(f"{PATH}/images/ui/rocket.png").resize(
                (img_size, img_size), Image.Resampling.LANCZOS
            ),
        )

        self.lbl_controls_title = customtkinter.CTkLabel(
            master=self,
            text="Controls",
            font=subheading_font(),
            justify=tkinter.LEFT,
        )
        self.lbl_controls_title.grid(row=0, column=1, sticky="wns", padx=20)

        # Button frame
        self.btn_frame = customtkinter.CTkFrame(master=self, fg_color=self._fg_color)
        self.btn_frame.rowconfigure((1, 2, 3), weight=0)
        self.btn_frame.rowconfigure((0, 4), weight=1)
        self.btn_frame.grid(row=1, rowspan=4, column=1, padx=15, sticky="wns")

        self.btn_play = customtkinter.CTkButton(
            master=self.btn_frame,
            text="Play",
            font=button_med_font(),
            text_color="white",
            image=self.img_play,
            command=self.play_btn_clicked,
        )
        self.btn_play.bind(
            "<Enter>",
            lambda event: self.btn_play.configure(
                text=f"{settings.keybind_to_text(self.combination_keys)}"
            ),
        )
        self.btn_play.bind(
            "<Leave>", lambda event: self.btn_play.configure(text="Play")
        )
        self.btn_play.grid(row=1, column=0, pady=(0, 20), sticky="nsew")

        self.btn_stop = customtkinter.CTkButton(
            master=self.btn_frame,
            text="Stop",
            font=button_med_font(),
            text_color="white",
            fg_color="#910101",
            hover_color="#690101",
            image=self.img_stop,
            command=self.stop_btn_clicked,
        )
        self.btn_stop.bind(
            "<Enter>",
            lambda event: self.btn_stop.configure(
                text=f"{settings.keybind_to_text(self.combination_keys)}"
            ),
        )
        self.btn_stop.bind(
            "<Leave>", lambda event: self.btn_stop.configure(text="Stop")
        )

        self.btn_options = customtkinter.CTkButton(
            master=self.btn_frame,
            text="Options",
            font=button_med_font(),
            text_color="white",
            fg_color="#d97b00",
            hover_color="#b36602",
            image=self.img_options,
            command=self.options_btn_clicked,
        )
        self.btn_options.grid(row=2, column=0, pady=0, sticky="nsew")

        self.btn_launch = customtkinter.CTkButton(
            master=self.btn_frame,
            text="Launch Game",
            font=button_med_font(),
            text_color="white",
            fg_color="#616161",
            image=self.img_start,
            command=self.launch_btn_clicked,
        )
        self.btn_launch.configure(state=tkinter.DISABLED)

        self.lbl_status = customtkinter.CTkLabel(
            master=self, text="Status: Idle", font=small_font(), justify=tkinter.CENTER
        )
        self.lbl_status.grid(row=5, column=1, pady=(0, 5), sticky="we")

        self.lbl_state = customtkinter.CTkLabel(
            master=self, text="State: Idle", font=small_font(), justify=tkinter.CENTER
        )
        self.lbl_state.grid(row=6, column=1, pady=(0, 15), sticky="we")

        self.controller = None
        self.options_class = None

        # Add reload button
        self.btn_reload = customtkinter.CTkButton(
            master=self.btn_frame,
            text="Reload Script",
            font=button_small_font(),
            text_color="white",
            fg_color="#616161",
            hover_color="#4f4f4f",
            command=self.reload_btn_clicked,
        )
        self.btn_reload.grid(row=4, column=0, pady=(5, 10), sticky="nsew")

    def destroy(self) -> None:
        """Cleanup observers before destroying frame."""
        BotSessionState().remove_observer(self._on_session_state_changed)
        super().destroy()

    # ---- Setup ----
    def set_controller(self, controller):
        self.controller = controller

    def setup(self, title, description):
        self.lbl_script_title.configure(text=title)
        self.lbl_script_desc.configure(text=description)
        self.lbl_status.configure(text="Status: Idle")
        self.lbl_state.configure(text="State: Idle")
        if self.controller.model:
            if isinstance(self.controller.model, Launchable):
                self.btn_launch.grid(row=3, column=0, pady=15, sticky="nsew")
                self.btn_launch.configure(state=tkinter.DISABLED)
            else:
                self.btn_launch.grid_forget()

    # ---- Button Listeners ----
    def play_btn_clicked(self):
        self.controller.play()

    def stop_btn_clicked(self):
        self.controller.stop()

    def options_btn_clicked(self):
        """
        Creates a new TopLevel view to display bot options.
        """
        self.btn_launch.configure(state=tkinter.DISABLED)
        window = customtkinter.CTkToplevel(master=self)
        window.title("Options")
        window.protocol(
            "WM_DELETE_WINDOW", lambda arg=window: self.on_options_closing(arg)
        )

        view = self.controller.get_options_view(parent=window)
        view.pack(side="top", fill="both", expand=True, padx=20, pady=20)
        window.after(
            100, window.lift
        )  # Workaround for bug where main window takes focus

    def on_options_closing(self, window):
        self.controller.abort_options()
        window.destroy()

    def launch_btn_clicked(self):
        self.controller.launch_game()

    def reload_btn_clicked(self):
        """
        Reloads the current bot script.
        """
        if self.controller and self.controller.model:
            self.controller.reload_model()

    # ---- Keyboard Interrupt Handlers ----
    def start_keyboard_listener(self):
        self.listener = keyboard.Listener(
            on_press=self.__on_press,
            on_release=self.__on_release,
        )
        self.listener.start()

    def stop_keyboard_listener(self):
        self.listener.stop()

    def __on_press(self, key):
        self.current_keys.add(key)
        if (
            all(k in self.current_keys for k in self.combination_keys)
            and not self.pressed
        ):
            self.pressed = True
            if self.status == "running":
                self.controller.stop()
            elif self.status == "stopped":
                self.controller.play()
                self.pressed = False
                self.current_keys.clear()

    def __on_release(self, key):
        self.current_keys.discard(key)
        if all(k not in self.current_keys for k in self.combination_keys):
            self.pressed = False

    # ---- Status Handlers ----
    def update_status_running(self):
        self.__toggle_buttons(True)
        self.btn_options.configure(state=tkinter.DISABLED)
        self.btn_play.grid_forget()
        self.btn_stop.grid(row=1, column=0, pady=(0, 15), sticky="nsew")
        self.lbl_status.configure(text="Status: Running")
        self.status = "running"

    def update_status_stopped(self):
        self.__toggle_buttons(True)
        self.btn_stop.grid_forget()
        self.btn_play.grid(row=1, column=0, pady=(0, 15), sticky="nsew")
        self.lbl_status.configure(text="Status: Stopped")
        self.status = "stopped"

    def update_status_configuring(self):
        self.__toggle_buttons(False)
        self.btn_launch.configure(state=tkinter.DISABLED)
        self.lbl_status.configure(text="Status: Configuring")

    def update_status_configured(self):
        self.__toggle_buttons(True)
        if isinstance(self.controller.model, Launchable):
            self.btn_launch.configure(state=tkinter.NORMAL)
        self.lbl_status.configure(text="Status: Configured")

    def __toggle_buttons(self, enabled: bool) -> None:
        if enabled:
            self.btn_play.configure(state=tkinter.NORMAL)
            self.btn_stop.configure(state=tkinter.NORMAL)
            self.btn_options.configure(state=tkinter.NORMAL)
        else:
            self.btn_play.configure(state=tkinter.DISABLED)
            self.btn_stop.configure(state=tkinter.DISABLED)
            self.btn_options.configure(state=tkinter.DISABLED)

    # ---- Progress Bar Handlers ----
    def update_progress(self, progress: float) -> None:
        """
        Called from controller. Updates the progress bar and percentage.
        Args:
            progress: The progress of the script, a float between 0 and 1.
        """
        self.progressbar.set(progress)
        self.lbl_progress.configure(text=f"Progress: {progress * 100:.0f}%")

    def update_state(self, state: str) -> None:
        """
        Called from controller. Updates the current bot state label.
        """
        self.lbl_state.configure(text=f"State: {state}")

    def _on_session_state_changed(self) -> None:
        """
        Observer callback - called when BotSessionState changes.
        Schedules UI update on main thread (thread-safe for Tkinter).
        """
        # Schedule update on main Tkinter thread to avoid threading issues
        self.after_idle(self._update_session_stats_ui)

    def _update_session_stats_ui(self) -> None:
        """
        Update session stats display (must be called from main thread).
        """
        state = BotSessionState()

        # Update action text
        action_text = state.current_action if state.current_action else "Idle"
        self.lbl_action_value.configure(text=action_text)

        # Update XP gained
        xp_gained = state.get_total_xp_gained()
        self.lbl_xp_value.configure(text=f"{xp_gained:,}")
