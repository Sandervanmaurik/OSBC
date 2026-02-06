"""
WelcomePanel - Initial panel shown when no script is selected.
Displays logo and welcome message.
"""

import pathlib
import customtkinter
from PIL import Image


class WelcomePanel(customtkinter.CTkFrame):
    """
    Welcome panel shown before a script is selected.
    Contains centered logo and welcome message.
    """

    def __init__(self, parent):
        """
        Args:
            parent: Parent widget
        """
        super().__init__(parent, fg_color="#1A1A1A", corner_radius=0)

        # Configure layout
        self.rowconfigure(0, weight=1)  # Top spacer
        self.rowconfigure(1, weight=0)  # Logo
        self.rowconfigure(2, weight=0)  # Message
        self.rowconfigure(3, weight=1)  # Bottom spacer
        self.columnconfigure(0, weight=1)

        # Load logo
        PATH = pathlib.Path(__file__).parent.parent.parent.resolve()
        logo_path = PATH / "images" / "ui" / "logo.png"

        logo_image = None
        if logo_path.exists():
            logo_image = customtkinter.CTkImage(
                light_image=Image.open(logo_path),
                dark_image=Image.open(logo_path),
                size=(120, 120),
            )

        # Logo
        self.lbl_logo = customtkinter.CTkLabel(
            self,
            text="",
            image=logo_image,
        )
        self.lbl_logo.grid(row=1, column=0, pady=(0, 20))

        # Welcome message
        self.lbl_message = customtkinter.CTkLabel(
            self,
            text="Select a script from the menu to get started",
            font=("Roboto", 16),
            text_color="#A0A0A0",
        )
        self.lbl_message.grid(row=2, column=0, pady=(0, 0))
