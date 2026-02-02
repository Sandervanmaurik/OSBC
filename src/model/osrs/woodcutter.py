import random
import time
from typing import Dict, List, Optional

import utilities.color as clr
import utilities.game_launcher as launcher
import utilities.ocr as ocr
import utilities.random_util as rd
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
from utilities.geometry import Point, RuneLiteObject
from utilities.osrs_bot_utils import OSRSBotBehaviorMixin


class OSRSWoodcutter(OSRSBotBehaviorMixin, OSRSBot, launcher.Launchable):
    """
    Human-like woodcutting bot with recovery logic.

    How to use:
    - Stand near trees and tag them with the chosen tree tag color.
    - If using bank mode, tag a bank with the chosen bank tag color.
    - Keep the inventory tab available (default layout).
    """

    COLOR_OPTIONS: Dict[str, clr.Color] = {
        "Pink": clr.PINK,
        "Green": clr.GREEN,
        "Cyan": clr.CYAN,
        "Yellow": clr.YELLOW,
        "Red": clr.RED,
        "White": clr.WHITE,
    }

    INVENTORY_MODES = [
        "Bank (tagged)",
        "Drop",
    ]

    TREE_TYPES = [
        "Any",
        "Normal",
        "Oak",
        "Willow",
        "Maple",
        "Yew",
        "Magic",
        "Mahogany",
    ]

    def __init__(self) -> None:
        bot_title = "Woodcutter"
        description = (
            "Human-like woodcutting with recovery logic. Tag trees (and bank if needed). "
            "Prioritizes natural behavior and avoids getting stuck."
        )
        super().__init__(bot_title=bot_title, description=description)

        self.running_time = 60  # minutes
        self.take_breaks = False
        self.tree_type = "Any"
        self.tree_tag_color_name = self.COLOR_OPTIONS["Pink"]
        self.bank_tag_color_name = self.COLOR_OPTIONS["Green"]
        self.inventory_mode = "Bank (tagged)"

        # Enable default options - can be customized via Options button
        self.options_set = True

        self._last_camera_move = 0.0
        self._last_random_action = 0.0
        self._camera_interval = 0.0
        self._action_interval = 0.0
        self._recovery_stage = 0
        self._idle_timeout = 25.0
        self._progress_timeout = 90.0

    def create_options(self) -> None:
        self.options_builder.add_slider_option(
            "running_time", "How long to run (minutes)?", 1, 500
        )
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])
        self.options_builder.add_dropdown_option(
            "tree_type", "Tree type", self.TREE_TYPES
        )
        self.options_builder.add_dropdown_option(
            "tree_tag_color_name", "Tree tag color", list(self.COLOR_OPTIONS.keys())
        )
        self.options_builder.add_dropdown_option(
            "inventory_mode", "Inventory handling", self.INVENTORY_MODES
        )
        self.options_builder.add_dropdown_option(
            "bank_tag_color_name", "Bank tag color", list(self.COLOR_OPTIONS.keys())
        )

    def save_options(self, options: dict) -> None:
        for option in options:
            if option == "running_time":
                self.running_time = int(options[option])
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            elif option == "tree_type":
                self.tree_type = options[option]
            elif option == "tree_tag_color_name":
                self.tree_tag_color_name = options[option]
            elif option == "inventory_mode":
                self.inventory_mode = options[option]
            elif option == "bank_tag_color_name":
                self.bank_tag_color_name = options[option]
            else:
                self.log_msg(f"Unknown option: {option}")
                self.options_set = False
                return

        self.log_msg(f"Running time: {self.running_time} minutes")
        self.log_msg(f"Take breaks: {self.take_breaks}")
        self.log_msg(f"Tree type: {self.tree_type}")
        self.log_msg(f"Tree tag color: {self.tree_tag_color_name}")
        self.log_msg(f"Inventory mode: {self.inventory_mode}")
        self.log_msg(f"Bank tag color: {self.bank_tag_color_name}")
        self.options_set = True

    def main_loop(self) -> None:
        self.log_msg("Starting human-like woodcutting bot...")
        self._open_inventory_tab()
        self._reset_random_intervals()
        self._reset_timeouts()

        last_action_time = time.time()
        last_progress_time = time.time()
        last_inventory_count = self.count_inventory_items_visual()
        search_failures = 0
        bank_failures = 0

        with self.timed_session(self.running_time) as session:
            while session.running:
                if self._should_stop():
                    break

                self._perform_random_behaviors()
                self._maybe_take_break()

                if self._inventory_is_full():
                    self.log_msg("Inventory full, handling...")
                    handled = self._handle_inventory_full()
                    if handled:
                        bank_failures = 0
                        last_progress_time = time.time()
                        last_inventory_count = self.count_inventory_items_visual()
                        search_failures = 0
                        self._reset_timeouts()
                        self._recovery_stage = 0
                    else:
                        bank_failures += 1
                        self.log_msg(f"Inventory handling failed (#{bank_failures})")
                        self._run_recovery("inventory handling failed")
                        if (
                            bank_failures >= 3
                            and self.inventory_mode == "Bank (tagged)"
                        ):
                            self.log_msg(
                                "Too many bank failures, falling back to drop this cycle."
                            )
                            if not self._drop_inventory():
                                self.log_msg("Drop fallback failed.")
                            bank_failures = 0
                    self._sleep(0.4, 1.2)
                    continue

                if self._is_chopping():
                    last_action_time = time.time()
                    if not self._wait_while_chopping():
                        self._run_recovery("chopping timeout")
                    else:
                        new_count = self.count_inventory_items_visual()
                        if new_count > last_inventory_count:
                            last_inventory_count = new_count
                            last_progress_time = time.time()
                        self._reset_timeouts()
                        self._recovery_stage = 0
                    continue

                target = self._select_tree_target()
                if target is None:
                    search_failures += 1
                    self.log_msg(f"No tagged trees found (#{search_failures})")
                    if search_failures >= 3:
                        self._run_recovery("no trees found")
                        search_failures = 0
                    self._sleep(0.5, 1.4)
                    if self._check_stuck(last_action_time, last_progress_time):
                        last_action_time = time.time()
                        last_progress_time = time.time()
                    continue

                search_failures = 0
                if self._attempt_chop(target):
                    if self._wait_for_chop_start():
                        last_action_time = time.time()
                        session.increment("trees_clicked")
                        if not self._wait_while_chopping():
                            self._run_recovery("chopping timeout")
                        else:
                            new_count = self.count_inventory_items_visual()
                            if new_count > last_inventory_count:
                                last_inventory_count = new_count
                                last_progress_time = time.time()
                            self._reset_timeouts()
                            self._recovery_stage = 0
                    else:
                        self._run_recovery("chop did not start")
                else:
                    self._sleep(0.2, 0.9)

                if self._check_stuck(last_action_time, last_progress_time):
                    last_action_time = time.time()
                    last_progress_time = time.time()

        self.log_msg("Woodcutting session complete.")

    def _handle_inventory_full(self) -> bool:
        self.log_msg(f"Handling full inventory with mode: {self.inventory_mode}")
        if self.inventory_mode == "Drop":
            return self._drop_inventory()
        if self.inventory_mode == "Bank (tagged)":
            return self._bank_items()
        self.log_msg(f"Unknown inventory mode: {self.inventory_mode}")
        return False

    def _drop_inventory(self) -> bool:
        self.log_msg("Dropping inventory...")
        self.drop_all()
        self._sleep(0.6, 1.4)
        if self.is_inventory_full_visual():
            self.log_msg("Inventory still full after drop.")
            return False
        return True

    def _bank_items(self) -> bool:
        bankOpen = self._bank_interface_visible()
        self.log_msg(f"Bank interface open: {bankOpen}")
        if bankOpen:
            self.log_msg("Bank interface is open, proceeding to deposit.")
            return self._deposit_all_shift_click()

        bank = self._find_bank_with_rotation()
        if bank is None:
            self.log_msg("Tagged bank not found.")
            return False

        self.mouse.move_to(bank.random_point(), mouseSpeed="medium")
        self._sleep(0.2, 0.6)

        if not self.mouseover_text(contains=["Bank", "Deposit"]):
            self.mouse.click()
            self._sleep(1.0, 1.8)
            bank = self._find_bank_with_rotation(attempts=2)
            if bank is None:
                return False
            self.mouse.move_to(bank.random_point(), mouseSpeed="medium")
            self._sleep(0.2, 0.5)
            if not self.mouseover_text(contains=["Bank", "Deposit"]):
                return False

        self.mouse.click()
        if not self._wait_for_bank_open():
            self.log_msg("Bank did not open, retrying...")
            self._sleep(0.5, 1.0)
            bank = self._find_bank_with_rotation(attempts=2)
            if bank is None:
                return False
            self.mouse.move_to(bank.random_point(), mouseSpeed="medium")
            self._sleep(0.2, 0.5)
            if not self.mouseover_text(contains=["Bank", "Deposit"]):
                return False
            self.mouse.click()
            if not self._wait_for_bank_open():
                return False

        return self._deposit_all_shift_click()

    def _deposit_all_shift_click(self) -> bool:
        if not self._safe_key_down("shift"):
            return False
        try:
            if not self.win.inventory_slots:
                return False
            slot = random.choice(self.win.inventory_slots)
            self.mouse.move_to(slot.random_point(), mouseSpeed="fast")
            self._sleep(0.1, 0.3)
            self.mouse.click()
        finally:
            self._safe_key_up("shift")
        self._sleep(0.3, 0.7)
        self._safe_key_press("escape")
        self._sleep(0.4, 0.9)
        return True

    def _find_tagged_bank(self) -> Optional[RuneLiteObject]:
        color = self.COLOR_OPTIONS.get(self.bank_tag_color_name, clr.GREEN)
        bank = self.get_nearest_tag(color)
        return bank

    def _find_bank_with_rotation(self, attempts: int = 3) -> Optional[RuneLiteObject]:
        for attempt in range(attempts):
            bank = self._find_tagged_bank()
            if bank is not None:
                return bank
            if attempt < attempts - 1:
                self.log_msg(
                    f"Bank not found, rotating camera (attempt {attempt + 1}/{attempts})"
                )
                self._rotate_camera_search()
                self._sleep(0.5, 1.2)
        return None

    def _wait_for_bank_open(self, timeout_seconds: float = 8.0) -> bool:
        start = time.time()
        while time.time() - start < timeout_seconds:
            if self.status != BotStatus.RUNNING:
                return False
            if self._bank_interface_visible():
                return True
            self._sleep(0.12, 0.25)
        return False

    def _bank_is_open(self) -> bool:
        return self._bank_interface_visible()

    def _bank_interface_visible(self) -> bool:
        try:
            words = ["The Bank of Gielinor", "Deposit", "Withdraw"]
            if ocr.find_text(words, self.win.game_view, ocr.PLAIN_12, [clr.OFF_ORANGE]):
                return True
            if ocr.find_text(words, self.win.game_view, ocr.BOLD_12, [clr.OFF_ORANGE]):
                return True
        except Exception as exc:
            self.log_msg(f"Bank UI check error: {exc}")
        return False

    def _select_tree_target(self) -> Optional[RuneLiteObject]:
        color = self.COLOR_OPTIONS.get(self.tree_tag_color_name, clr.PINK)
        trees = self.get_all_tagged_in_rect(self.win.game_view, color)
        return self._select_tagged_target(trees)

    def _attempt_chop(self, target: RuneLiteObject) -> bool:
        try:
            click_point = target.random_point()
            if random.random() < 0.08:
                miss = Point(
                    click_point.x + random.randint(-12, 12),
                    click_point.y + random.randint(-12, 12),
                )
                self.mouse.move_to(miss, mouseSpeed="fast")
                self.mouse.click()
                self._sleep(0.2, 0.6)

            self.mouse.move_to(
                click_point, mouseSpeed=random.choice(["slow", "medium", "fast"])
            )
            self._sleep(0.1, 0.4)

            if not self._is_chop_hover():
                return False

            self.mouse.click()
            self._sleep(0.2, 0.6)
            return True
        except Exception as exc:
            self.log_msg(f"Chop attempt error: {exc}")
            return False

    def _is_chop_hover(self) -> bool:
        if not self.mouseover_text(contains="Chop"):
            return False
        if self.tree_type == "Any":
            return True
        if random.random() < 0.6:
            return self.mouseover_text(contains=self.tree_type)
        return True

    def _wait_for_chop_start(self) -> bool:
        timeout = rd.truncated_normal_sample(1.5, 4.0, mean=2.5, std=0.6)
        start = time.time()
        while time.time() - start < timeout:
            if self.status != BotStatus.RUNNING:
                return False
            if self._is_chopping():
                return True
            self._sleep(0.08, 0.25)
        self._log_action_text_debug("chop_start_timeout")
        return False

    def _wait_while_chopping(self) -> bool:
        timeout = rd.truncated_normal_sample(12, 45, mean=26, std=7)
        start = time.time()
        while self._is_chopping():
            if self.status != BotStatus.RUNNING:
                return False
            if time.time() - start > timeout:
                self._log_action_text_debug("chop_timeout")
                return False
            if random.random() < 0.12:
                self._micro_behavior_during_action()
            self._sleep(0.2, 0.6)
        return True

    def _is_chopping(self) -> bool:
        if self.is_player_doing_action("Woodcutting"):
            return True
        return self._action_text_contains(["Woodcutting", "Chopping"])
