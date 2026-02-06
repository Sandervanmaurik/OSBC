"""
ScriptControlBar - Icon-only control buttons (Play/Stop/Options) for the script panel.
Buttons swap between Play and Stop based on bot status.
"""

import pathlib
import customtkinter
from PIL import Image
from model.bot_session_state import BotSessionState


class ScriptControlBar(customtkinter.CTkFrame):
    """
    A horizontal bar with icon-only control buttons.
    Contains Play/Stop (swappable) and Options buttons.
    Subscribes to BotSessionState to update button visibility.
    """

    def __init__(self, parent, play_command, stop_command, options_command):
        """
        Args:
            parent: Parent widget
            play_command: Callback when Play button is clicked
            stop_command: Callback when Stop button is clicked
            options_command: Callback when Options button is clicked
        """
        super().__init__(parent, fg_color="transparent")

        self.play_command = play_command
        self.stop_command = stop_command
        self.options_command = options_command

        # Load icons
        PATH = pathlib.Path(__file__).parent.parent.parent.resolve()
        icon_size = (24, 24)

        self.play_icon = customtkinter.CTkImage(
            light_image=Image.open(PATH / "images" / "ui" / "play.png"),
            dark_image=Image.open(PATH / "images" / "ui" / "play.png"),
            size=icon_size,
        )

        self.stop_icon = customtkinter.CTkImage(
            light_image=Image.open(PATH / "images" / "ui" / "stop2.png"),
            dark_image=Image.open(PATH / "images" / "ui" / "stop2.png"),
            size=icon_size,
        )

        self.options_icon = customtkinter.CTkImage(
            light_image=Image.open(PATH / "images" / "ui" / "options2.png"),
            dark_image=Image.open(PATH / "images" / "ui" / "options2.png"),
            size=icon_size,
        )

        # Create button frame (left-aligned)
        self.button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(side="left", padx=0, pady=5)

        # Play button (initially visible)
        self.btn_play = customtkinter.CTkButton(
            self.button_frame,
            text="",
            image=self.play_icon,
            command=self._on_play,
            width=40,
            height=40,
            fg_color="#2E2E2E",
            hover_color="#4A90E2",
            corner_radius=6,
        )
        self.btn_play.pack(side="left", padx=2)

        # Stop button (initially hidden)
        self.btn_stop = customtkinter.CTkButton(
            self.button_frame,
            text="",
            image=self.stop_icon,
            command=self._on_stop,
            width=40,
            height=40,
            fg_color="#2E2E2E",
            hover_color="#E24A4A",
            corner_radius=6,
        )
        # Don't pack yet - will be shown when bot starts

        # Options button
        self.btn_options = customtkinter.CTkButton(
            self.button_frame,
            text="",
            image=self.options_icon,
            command=options_command,
            width=40,
            height=40,
            fg_color="#2E2E2E",
            hover_color="#3A3A3A",
            corner_radius=6,
        )
        self.btn_options.pack(side="left", padx=2)

        # Note: Button visibility (Play/Stop swap) is controlled by the Bot model
        # calling controller.update_status(), which updates InfoFrame.
        # We don't need to subscribe to BotSessionState here.

        # Set initial state
        self._update_buttons("stopped")

    def _on_play(self):
        """Handle Play button click."""
        if self.play_command:
            self.play_command()

    def _on_stop(self):
        """Handle Stop button click."""
        if self.stop_command:
            self.stop_command()

    def _update_buttons(self, status: str):
        """
        Show/hide Play/Stop buttons based on bot status.

        Args:
            status: "stopped", "running", "paused", "configuring"
        """
        if status == "running":
            # Hide Play, show Stop
            self.btn_play.pack_forget()
            self.btn_stop.pack(side="left", padx=2, before=self.btn_options)
        else:
            # Show Play, hide Stop
            self.btn_stop.pack_forget()
            self.btn_play.pack(side="left", padx=2, before=self.btn_options)

    def set_buttons_enabled(self, enabled: bool):
        """
        Enable or disable all buttons.

        Args:
            enabled: True to enable, False to disable
        """
        state = "normal" if enabled else "disabled"
        self.btn_play.configure(state=state)
        self.btn_stop.configure(state=state)
        self.btn_options.configure(state=state)
