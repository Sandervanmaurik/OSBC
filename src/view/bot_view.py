import customtkinter

from view.info_frame import InfoFrame
from view.output_log_frame import OutputLogFrame
from view.skills_frame import SkillsFrame
from view.behavior_frame import BehaviorFrame


class BotView(customtkinter.CTkFrame):
    def __init__(self, parent):
        """
        A base frame for all bot views. This frame contains the following:
            - Info frame (controls, title, description, progress) - spans full width at top
            - Tabbed view (left column, 30% width):
                - Skills tab (skill levels display)
                - Behavior tab (behavior settings display)
            - Output log frame (log messages) - right column (70% width)
        This view needs to be configured using setup() to populate fields based
        on the bot's title and description, as well as setting controllers for the child views.
        """
        super().__init__(parent)

        # Configure grid layout
        # Row 0: Info (full width)
        # Row 1: Tabview (30%) | Logs (70%)
        self.rowconfigure(0, weight=0)  # controls row - fixed height
        self.rowconfigure(1, weight=1)  # tabview/logs row - expandable
        self.columnconfigure(0, weight=0, minsize=280)  # left column - fixed width ~30%
        self.columnconfigure(1, weight=1)  # right column - expandable ~70%

        # ---------- TOP (script info and control buttons) ----------
        self.frame_info = InfoFrame(parent=self, title="Title", info="Description")
        self.frame_info.grid(
            row=0, column=0, columnspan=2, pady=15, padx=15, sticky="nsew"
        )

        # ---------- BOTTOM LEFT (tabbed view for skills and behavior) ----------
        self.tabview = customtkinter.CTkTabview(master=self)
        self.tabview.grid(row=1, column=0, pady=(0, 15), padx=(15, 7), sticky="nsew")

        # Add tabs
        self.tabview.add("Skills")
        self.tabview.add("Behavior")

        # Set Skills as default tab
        self.tabview.set("Skills")

        # ---------- SKILLS TAB ----------
        self.frame_skills = SkillsFrame(parent=self.tabview.tab("Skills"))
        self.frame_skills.pack(fill="both", expand=True, padx=0, pady=0)

        # ---------- BEHAVIOR TAB ----------
        self.frame_behavior = BehaviorFrame(parent=self.tabview.tab("Behavior"))
        self.frame_behavior.pack(fill="both", expand=True, padx=0, pady=0)

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
        # Note: skills and behavior frames don't need direct controller access

    def update_behavior_display(self, behavior_config, stats=None):
        """
        Updates the behavior settings display.
        Args:
            behavior_config: Dictionary from BehaviorManager.config
            stats: Optional stats dictionary from BehaviorManager.get_stats_summary()
        """
        self.frame_behavior.update_behavior_display(behavior_config, stats)
