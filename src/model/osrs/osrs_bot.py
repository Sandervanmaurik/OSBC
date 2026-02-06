from abc import ABCMeta
from functools import wraps
import re
import time
from typing import TypeVar, Callable, Any, Dict, Optional, TYPE_CHECKING

import utilities.color as clr
import utilities.ocr as ocr
import utilities.random_util as rd
from utilities.osrs_skills import skill_index, skill_names

from model.runelite_bot import RuneLiteBot, RuneLiteWindow
from model.skills import SkillsManager

if TYPE_CHECKING:
    from utilities.xp_watcher import XPWatcher

T = TypeVar("T")


def validate_types(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to validate function argument and return types.
    For use with OSRS bot methods.

    Args:
        func (Callable[..., T]): Function to validate

    Returns:
        Callable[..., T]: Wrapped function with type validation
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        result = func(*args, **kwargs)
        return_type = func.__annotations__.get("return")
        if return_type and not isinstance(result, return_type):
            raise TypeError(f"Expected return type {return_type}, got {type(result)}")
        return result

    return wrapper


class OSRSBot(RuneLiteBot, metaclass=ABCMeta):
    win: RuneLiteWindow = None

    def __init__(self, bot_title: str, description: str) -> None:
        window = RuneLiteWindow("RuneLite")
        super().__init__("OSRS", bot_title, description, window)
        # Note: skill_levels is now a property that delegates to SkillsManager
        self._xp_watcher: Optional[XPWatcher] = None
        self._action_watcher = None  # Initialized in on_start()

    @property
    def skill_levels(self) -> Dict[str, int]:
        """
        Backward compatibility property for accessing skill levels.
        Delegates to the global SkillsManager singleton.

        Returns:
            Dict mapping skill names to current levels
        """
        manager = SkillsManager()
        return {skill: manager.get_skill(skill).level for skill in skill_names()}

    def on_start(self) -> None:
        """
        Hook called when the bot starts. Initializes skill tracking and XP watcher.
        """
        # Reset session state for new session
        from model.bot_session_state import BotSessionState

        BotSessionState().reset()

        self.refresh_skill_levels(open_tab=True, return_to_inventory=True)

        # Initialize XP watcher for automatic XP tracking (lazy import to avoid circular dependency)
        if self.win:
            from utilities.xp_watcher import XPWatcher
            from utilities.action_watcher import ActionWatcher

            self._xp_watcher = XPWatcher(self.win)
            self._xp_watcher.load_skill_templates()  # Load templates if available

            self._action_watcher = ActionWatcher(self.win)

            # Start background tracking threads
            self._xp_watcher.start_background(self)
            self._action_watcher.start_background(self)

            self.log_msg(
                "XP Watcher and Action Watcher initialized (background tracking enabled)"
            )

    def on_stop(self) -> None:
        """
        Hook called when the bot stops. Stops background watcher threads.
        """
        if self._xp_watcher:
            self._xp_watcher.stop_background()
        if self._action_watcher:
            self._action_watcher.stop_background()

    def get_skill_level(
        self,
        skill_name: str,
        open_tab: bool = True,
        return_to_inventory: bool = True,
    ) -> int:
        """
        Reads the current level for a given skill from the skills tab.
        Returns -1 if unreadable.
        """
        if not self.win or not self.win.skill_slots:
            return -1

        def _click_tab(index: int) -> None:
            if len(self.win.cp_tabs) <= index:
                return
            if not self._ensure_focus():
                return
            self.mouse.move_to(
                self.win.cp_tabs[index].random_point(), mouseSpeed="fast"
            )
            self.mouse.click()
            time.sleep(rd.truncated_normal_sample(0.2, 0.6, mean=0.35, std=0.1))

        try:
            idx = skill_index(skill_name)
        except ValueError as exc:
            self.log_msg(str(exc))
            if return_to_inventory:
                _click_tab(3)
            return -1

        if idx >= len(self.win.skill_slots):
            if return_to_inventory:
                _click_tab(3)
            return -1

        if open_tab:
            self.refresh_skill_levels(
                open_tab=True, return_to_inventory=return_to_inventory
            )
            return SkillsManager().get_skill(skill_names()[idx]).level

        rect = self.win.skill_slots[idx]
        level = self._read_skill_level_from_rect(rect)
        SkillsManager().update_skill_level(skill_names()[idx], level)
        self._update_skills_ui()

        if return_to_inventory:
            _click_tab(3)

        return level

    def refresh_skill_levels(
        self,
        open_tab: bool = True,
        return_to_inventory: bool = True,
    ) -> Dict[str, int]:
        """
        Refresh all skill levels from the skills tab and update UI memory.
        """
        if not self.win or not self.win.skill_slots:
            return self.skill_levels

        def _click_tab(index: int) -> None:
            if len(self.win.cp_tabs) <= index:
                return
            if not self._ensure_focus():
                return
            self.mouse.move_to(
                self.win.cp_tabs[index].random_point(), mouseSpeed="fast"
            )
            self.mouse.click()
            time.sleep(rd.truncated_normal_sample(0.2, 0.6, mean=0.35, std=0.1))

        if open_tab:
            _click_tab(1)
            time.sleep(rd.truncated_normal_sample(0.3, 0.8, mean=0.5, std=0.15))

        manager = SkillsManager()
        for idx, name in enumerate(skill_names()):
            if idx >= len(self.win.skill_slots):
                break
            level = self._read_skill_level_from_rect(self.win.skill_slots[idx])
            if level >= 0:
                manager.update_skill_level(name, level)

        self._update_skills_ui()

        if return_to_inventory:
            _click_tab(3)

        return self.skill_levels

    def _read_skill_level_from_rect(self, rect) -> int:
        colors = [clr.WHITE, clr.OFF_WHITE, clr.OFF_YELLOW]
        for font in (ocr.PLAIN_11, ocr.PLAIN_12, ocr.BOLD_12):
            if res := ocr.extract_text(rect, font, colors):
                numbers = re.findall(r"\d+", res)
                if not numbers:
                    continue
                if len(numbers) >= 2:
                    return int(numbers[0])
                digits = numbers[0]
                if len(digits) % 2 == 0:
                    half = len(digits) // 2
                    if digits[:half] == digits[half:]:
                        return int(digits[:half])
                return int(digits)
        return -1

    def _update_skills_ui(self) -> None:
        if hasattr(self, "controller") and self.controller:
            self.controller.update_skills(self.skill_levels)

    def _format_skill_levels(self) -> str:
        entries = []
        for name in skill_names():
            level = self.skill_levels.get(name, -1)
            level_text = "?" if level < 0 else str(level)
            entries.append(f"{name.title()}: {level_text}")

        lines = []
        per_line = 4
        for i in range(0, len(entries), per_line):
            lines.append("  ".join(entries[i : i + per_line]))
        return "\n".join(lines)

    def check_xp_watcher(self) -> bool:
        """
        Check for XP gains via XP Watcher.
        Call this in your bot's main loop for automatic XP tracking.

        Returns:
            True if XP was detected and processed

        Example:
            def main_loop(self):
                while self.status == BotStatus.RUNNING:
                    # Your bot logic here
                    ...

                    # Check for XP gains
                    if self.check_xp_watcher():
                        self.log_msg("XP gained!")
        """
        self.log_msg("Checking XP watcher...")
        if self._xp_watcher and self._xp_watcher.should_check():
            self.log_msg("XP watcher active, checking for XP...")
            return self._xp_watcher.check_for_xp()

        return False
