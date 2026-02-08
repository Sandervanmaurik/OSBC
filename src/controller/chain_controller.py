"""
ChainController - Orchestrates sequential execution of script chains.

Handles:
    - Sequential execution of bot scripts
    - Retry logic for missing items (retry once, then skip)
    - Progress tracking for current script and overall chain
    - XP accumulation across scripts
    - State transitions between scripts
"""

import time
import threading
from typing import Dict, Callable, Optional
from model.bot import Bot, BotStatus, BotSession
from model.chain import ScriptChain, ChainEntry, ChainEntryStatus
from controller.bot_controller import BotController


class ChainController:
    """
    Controls execution of script chains.

    Wraps existing BotController to execute multiple bots sequentially.
    Implements retry logic and progress tracking.
    """

    def __init__(
        self,
        models: Dict[str, Bot],  # Map of bot_name -> Bot instance
        bot_controller: BotController,  # Existing controller for single bot execution
    ):
        """
        Args:
            models: Dictionary of all bot instances
            bot_controller: Existing BotController to use for individual script execution
        """
        self.models = models
        self.bot_controller = bot_controller

        # Execution state
        self.current_chain: Optional[ScriptChain] = None
        self.current_entry_index: int = -1
        self.is_running: bool = False
        self.chain_thread: Optional[threading.Thread] = None
        self.retry_count: int = 0  # Tracks retries for current script

        # Callbacks for UI updates
        self.on_chain_started: Optional[Callable] = None
        self.on_script_started: Optional[Callable[[ChainEntry, int]]] = (
            None  # (entry, index)
        )
        self.on_script_progress: Optional[Callable[[float, int]]] = (
            None  # (progress, remaining_seconds)
        )
        self.on_script_completed: Optional[Callable[[ChainEntry, int]]] = (
            None  # (entry, xp_gained)
        )
        self.on_script_skipped: Optional[Callable[[ChainEntry, str]]] = (
            None  # (entry, reason)
        )
        self.on_chain_progress: Optional[Callable[[float]]] = None  # (overall_progress)
        self.on_chain_completed: Optional[Callable[[ScriptChain]]] = None  # (chain)
        self.on_chain_stopped: Optional[Callable] = None

    # ============ Public API ============

    def run_chain(self, chain: ScriptChain):
        """
        Start executing a chain.

        Args:
            chain: ScriptChain to execute
        """
        if self.is_running:
            print("Chain already running")
            return

        self.current_chain = chain
        self.current_entry_index = -1
        self.is_running = True

        # Reset all entry statuses
        chain.reset_status()

        # Start execution in background thread
        self.chain_thread = threading.Thread(target=self._execute_chain, daemon=True)
        self.chain_thread.start()

    def stop_chain(self):
        """Stop the currently running chain."""
        if not self.is_running:
            return

        self.is_running = False

        # Stop current bot if running
        if (
            self.bot_controller.model
            and self.bot_controller.model.status == BotStatus.RUNNING
        ):
            self.bot_controller.stop()

        # Wait for thread to finish
        if self.chain_thread:
            self.chain_thread.join(timeout=5)

        # Notify UI
        if self.on_chain_stopped:
            self.on_chain_stopped()

    def get_current_script_info(self) -> Optional[tuple]:
        """
        Get info about the currently running script.

        Returns:
            Tuple of (entry, index, total_entries) or None if not running
        """
        if not self.is_running or self.current_entry_index < 0:
            return None

        entry = self.current_chain.entries[self.current_entry_index]
        total = len(self.current_chain.entries)
        return (entry, self.current_entry_index, total)

    def get_overall_progress(self) -> float:
        """
        Calculate overall chain progress (0.0 to 1.0).

        Returns:
            Progress as float between 0 and 1
        """
        if not self.current_chain or not self.current_chain.entries:
            return 0.0

        total_entries = len(self.current_chain.entries)
        completed = sum(
            1
            for e in self.current_chain.entries
            if e.status in [ChainEntryStatus.COMPLETED, ChainEntryStatus.SKIPPED]
        )

        # Add partial progress of current script
        if self.current_entry_index >= 0 and self.current_entry_index < total_entries:
            current_bot = self.bot_controller.model
            if current_bot:
                completed += current_bot.progress

        return min(1.0, completed / total_entries)

    # ============ Private Execution Logic ============

    def _execute_chain(self):
        """Main chain execution loop (runs in background thread)."""
        try:
            # Notify chain started
            if self.on_chain_started:
                self.on_chain_started()

            # Execute each entry sequentially
            for idx, entry in enumerate(self.current_chain.entries):
                if not self.is_running:
                    break

                self.current_entry_index = idx
                self._execute_entry(entry, idx)

            # Chain completed
            if self.is_running:
                self._finalize_chain()

        except Exception as e:
            print(f"Chain execution error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            self.is_running = False

    def _execute_entry(self, entry: ChainEntry, index: int):
        """
        Execute a single chain entry with retry logic.

        Args:
            entry: ChainEntry to execute
            index: Index of entry in chain
        """
        # Get bot instance
        bot = self.models.get(entry.script_name)
        if not bot:
            print(f"Bot '{entry.script_name}' not found, skipping")
            entry.status = ChainEntryStatus.SKIPPED
            if self.on_script_skipped:
                self.on_script_skipped(entry, "Bot not found")
            return

        # Apply saved options
        bot.save_options(entry.options)
        bot.options_set = True

        # Execute with retry logic (retry once on failure)
        self.retry_count = 0
        max_retries = 1

        while self.retry_count <= max_retries:
            if not self.is_running:
                return

            # Attempt execution
            success = self._run_single_script(bot, entry, index)

            if success:
                # Script completed successfully
                entry.status = ChainEntryStatus.COMPLETED
                entry.xp_gained = self._calculate_xp_gained(bot)

                if self.on_script_completed:
                    self.on_script_completed(entry, entry.xp_gained)
                break
            else:
                # Script failed (likely missing items)
                self.retry_count += 1

                if self.retry_count <= max_retries:
                    # Retry once
                    print(
                        f"Retrying script '{entry.script_name}' ({self.retry_count}/{max_retries})"
                    )
                    time.sleep(2)  # Brief delay before retry
                else:
                    # Out of retries, skip to next
                    entry.status = ChainEntryStatus.SKIPPED
                    if self.on_script_skipped:
                        self.on_script_skipped(entry, "Missing items after retry")
                    break

    def _run_single_script(self, bot: Bot, entry: ChainEntry, index: int) -> bool:
        """
        Run a single script for its configured duration.

        Args:
            bot: Bot instance to run
            entry: ChainEntry configuration
            index: Index in chain

        Returns:
            True if script completed successfully, False if failed
        """
        try:
            # Update entry status
            entry.status = ChainEntryStatus.RUNNING

            # Notify UI
            if self.on_script_started:
                self.on_script_started(entry, index)

            # Change bot model in controller
            self.bot_controller.change_model(bot)

            # Initialize window
            bot.win.focus()
            time.sleep(0.5)
            bot.win.initialize()

            # Reset and start bot
            bot.reset_progress()
            bot.set_status(BotStatus.RUNNING)

            # Call on_start hook if exists
            if hasattr(bot, "on_start"):
                try:
                    bot.on_start()
                except Exception as exc:
                    bot.log_msg(f"on_start failed: {exc}")

            # Run bot in this thread (synchronous execution)
            # Use BotSession for timed execution
            with BotSession(bot, entry.running_time) as session:
                # Start main loop in background thread
                from model.bot import BotThread

                bot_thread = BotThread(target=bot.main_loop)
                bot_thread.setDaemon(True)
                bot_thread.start()

                # Monitor progress
                while session.running and self.is_running:
                    # Update script progress
                    if self.on_script_progress:
                        self.on_script_progress(bot.progress, session.remaining_seconds)

                    # Update overall chain progress
                    if self.on_chain_progress:
                        self.on_chain_progress(self.get_overall_progress())

                    time.sleep(0.5)  # Update every 500ms

                # Stop bot thread
                if bot.status == BotStatus.RUNNING:
                    bot.set_status(BotStatus.STOPPED)
                    bot_thread.stop()
                    bot_thread.join(timeout=3)

            # Check if script completed successfully
            # (If bot status is STOPPED and we exited naturally, it's success)
            return bot.status == BotStatus.STOPPED

        except Exception as e:
            print(f"Script execution error: {e}")
            import traceback

            traceback.print_exc()

            # Ensure bot is stopped
            try:
                if bot.status == BotStatus.RUNNING:
                    bot.stop()
            except:
                pass

            return False

    def _calculate_xp_gained(self, bot: Bot) -> int:
        """
        Calculate total XP gained during bot execution.

        Args:
            bot: Bot instance

        Returns:
            Total XP gained across all skills
        """
        # This would require tracking initial XP and comparing to final XP
        # For now, return 0 as a placeholder
        # TODO: Implement XP tracking via OCR or game state monitoring
        return 0

    def _finalize_chain(self):
        """Complete chain execution and notify UI."""
        if self.on_chain_completed:
            self.on_chain_completed(self.current_chain)

        self.is_running = False
        self.current_entry_index = -1


class ChainExecutionCallbacks:
    """
    Helper class to bundle callback functions for chain execution.
    Makes it easier to wire up UI to controller.
    """

    def __init__(self):
        self.on_chain_started: Optional[Callable] = None
        self.on_script_started: Optional[Callable[[ChainEntry, int]]] = None
        self.on_script_progress: Optional[Callable[[float, int]]] = None
        self.on_script_completed: Optional[Callable[[ChainEntry, int]]] = None
        self.on_script_skipped: Optional[Callable[[ChainEntry, str]]] = None
        self.on_chain_progress: Optional[Callable[[float]]] = None
        self.on_chain_completed: Optional[Callable[[ScriptChain]]] = None
        self.on_chain_stopped: Optional[Callable] = None

    def bind_to_controller(self, controller: ChainController):
        """Bind all callbacks to a ChainController instance."""
        controller.on_chain_started = self.on_chain_started
        controller.on_script_started = self.on_script_started
        controller.on_script_progress = self.on_script_progress
        controller.on_script_completed = self.on_script_completed
        controller.on_script_skipped = self.on_script_skipped
        controller.on_chain_progress = self.on_chain_progress
        controller.on_chain_completed = self.on_chain_completed
        controller.on_chain_stopped = self.on_chain_stopped
