import customtkinter

from view.info_frame import InfoFrame
from view.output_log_frame import OutputLogFrame
from view.skills_frame import SkillsFrame


class BotView(customtkinter.CTkFrame):
    def __init__(self, parent):
        """
        A base frame for all bot views. This frame contains the following:
            - Info frame (controls, title, description, progress) - spans full width at top
            - Skills frame (skill levels display) - bottom left (30% width)
            - Output log frame (log messages) - bottom right (70% width)
        This view needs to be configured using setup() to populate fields based
        on the bot's title and description, as well as setting controllers for the child views.
        """
        super().__init__(parent)

        # Configure grid layout for compact 2-column bottom layout
        # Row 0: Controls (full width)
        # Row 1: Skills (30%) | Logs (70%)
        self.rowconfigure(0, weight=0)  # controls row - fixed height
        self.rowconfigure(1, weight=1)  # skills/logs row - resizable
        self.columnconfigure(
            0, weight=0, minsize=280
        )  # skills column - fixed width ~30%
        self.columnconfigure(1, weight=1)  # logs column - expandable ~70%

        # ---------- TOP (script info and control buttons) ----------
        self.frame_info = InfoFrame(parent=self, title="Title", info="Description")
        self.frame_info.grid(
            row=0, column=0, columnspan=2, pady=15, padx=15, sticky="nsew"
        )

        # ---------- BOTTOM LEFT (skills display) ----------
        self.frame_skills = SkillsFrame(parent=self)
        self.frame_skills.grid(
            row=1, column=0, pady=(0, 15), padx=(15, 7), sticky="new"
        )  # Anchor to top (north), expand horizontally (east-west)

        # ---------- BOTTOM RIGHT (log text box) ----------
        self.frame_output_log = OutputLogFrame(parent=self)
        self.frame_output_log.grid(
            row=1, column=1, pady=(0, 15), padx=(7, 15), sticky="nsew"
        )

        self.controller = None

    def set_controller(self, controller):
        """
        Sets up the view and its child views to use the given controller.
        Args:
            controller: The controller to use.
        """
        self.controller = controller
        self.frame_info.set_controller(controller=controller)
        self.frame_output_log.set_controller(controller=controller)
        # Note: skills frame doesn't need direct controller access
