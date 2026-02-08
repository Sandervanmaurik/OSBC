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
from model.bot_session_state import BotSessionState
from model.skills import SKILL_ORDER
from utilities.random_util import truncated_normal_sample


class ChainBotController:
    """No-op controller for bots running in chains. Forwards logs to chain controller."""

    def __init__(self, log_callback=None):
        """
        Args:
            log_callback: Optional callback(msg, overwrite) to forward log messages
        """
        self.log_callback = log_callback

    def update_progress(self):
        """No-op: chain controller handles progress updates"""
        pass

    def update_status(self):
        """No-op: chain controller handles status updates"""
        pass

    def update_state(self, state: str):
        """No-op: chain controller handles state updates"""
        pass

    def update_skills(self, skills=None):
        """No-op: chain controller doesn't update skills display"""
        pass

    def update_behavior_display(self, behavior_config=None, stats=None):
        """No-op: chain controller doesn't update behavior display"""
        pass

    def update_log(self, msg: str, overwrite: bool = False):
        """Forward log messages to callback if provided"""
        if self.log_callback:
            self.log_callback(msg, overwrite)

    def clear_log(self):
        """No-op: chain controller doesn't clear log display"""
        pass


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

        # XP tracking for chain (thread-safe)
        self.chain_xp_gained: Dict[str, int] = {}  # Accumulated XP across all scripts
        self._xp_lock = threading.Lock()  # Protect concurrent XP updates

        # Window initialization synchronization
        self._window_init_event = threading.Event()

        # Callbacks for UI updates
        self.on_chain_started: Optional[Callable] = None
        self.on_script_started: Optional[Callable[[ChainEntry, int]]] = (
            None  # (entry, index)
        )
        self.on_init_window: Optional[Callable[[Bot], None]] = (
            None  # Callback to initialize window from main thread
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
        self.on_log_update: Optional[Callable[[str, bool]]] = None  # (msg, overwrite)

    # ============ Public API ============

    def run_chain(self, chain: ScriptChain):
        """
        Start executing a chain.

        Args:
            chain: ScriptChain to execute
        """
        print(f"[CHAIN DEBUG] run_chain() called for chain: {chain.name}")

        if self.is_running:
            print("[CHAIN DEBUG] Chain already running - aborting")
            return

        self.current_chain = chain
        self.current_entry_index = -1
        self.is_running = True

        # Reset all entry statuses
        chain.reset_status()

        # Reset chain XP tracking
        self.chain_xp_gained.clear()

        # Start execution in background thread
        print(f"[CHAIN DEBUG] Creating background thread for chain execution")
        self.chain_thread = threading.Thread(target=self._execute_chain, daemon=True)
        print(f"[CHAIN DEBUG] Starting background thread")
        self.chain_thread.start()
        print(f"[CHAIN DEBUG] Background thread started")

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

    def _log_error(self, message: str):
        """
        Log error message to console and UI callback.

        Args:
            message: Error message (without [ERROR] prefix)
        """
        error_msg = f"[ERROR] {message}"
        print(error_msg)
        if self.on_log_update:
            self.on_log_update(error_msg, False)

    # ============ Private Execution Logic ============

    def _execute_chain(self):
        """Main chain execution loop (runs in background thread)."""
        print(f"[CHAIN DEBUG] _execute_chain() started in background thread")
        try:
            # Notify chain started
            if self.on_chain_started:
                print(f"[CHAIN DEBUG] Calling on_chain_started callback")
                self.on_chain_started()

            # Execute each entry sequentially
            print(
                f"[CHAIN DEBUG] Starting to execute {len(self.current_chain.entries)} entries"
            )
            for idx, entry in enumerate(self.current_chain.entries):
                if not self.is_running:
                    print(f"[CHAIN DEBUG] Chain stopped by user, breaking loop")
                    break

                print(
                    f"[CHAIN DEBUG] Executing entry {idx + 1}/{len(self.current_chain.entries)}: {entry.script_name}"
                )
                self.current_entry_index = idx
                self._execute_entry(entry, idx)

            # Chain completed
            if self.is_running:
                print(f"[CHAIN DEBUG] Chain completed, calling _finalize_chain()")
                self._finalize_chain()

        except Exception as e:
            print(f"[ERROR] Chain execution error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            self.is_running = False
            print(f"[CHAIN DEBUG] _execute_chain() finished")

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
            self._log_error(f"Bot '{entry.script_name}' not found in loaded bots")
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
                # NOTE: entry.xp_gained is already set in _run_single_script() at line 456

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
                    time.sleep(
                        truncated_normal_sample(1.5, 3.0)
                    )  # Randomized delay before retry
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
        # Save original controller and replace with chain controller at method level
        # This prevents crashes when bot tries to call controller.update_progress()
        # during chain execution (when controller.model is None)
        print(
            f"[CHAIN DEBUG] Saving original controller and replacing with ChainBotController"
        )
        original_controller = bot.controller

        # Create log callback that forwards to chain controller
        def log_callback(msg: str, overwrite: bool = False):
            if self.on_log_update:
                self.on_log_update(msg, overwrite)

        bot.controller = ChainBotController(log_callback=log_callback)

        try:
            print(f"[CHAIN DEBUG] Starting script: {entry.script_name}")

            # Update entry status
            entry.status = ChainEntryStatus.RUNNING

            # Notify UI
            if self.on_script_started:
                print(f"[CHAIN DEBUG] Notifying UI that script started")
                self.on_script_started(entry, index)

            # DON'T call change_model - it updates the wrong view
            # The bot is already configured and ready to run

            # Initialize window on main thread (thread-safe via callback)
            if self.on_init_window:
                print(f"[CHAIN DEBUG] Requesting window initialization")
                # Clear event before requesting initialization
                self._window_init_event.clear()
                # Request window initialization from main thread
                self.on_init_window(bot)
                # Wait for initialization to complete (with timeout)
                print(f"[CHAIN DEBUG] Waiting for window initialization event...")
                if not self._window_init_event.wait(timeout=10):
                    self._log_error(
                        f"Window initialization timed out for {entry.script_name} (10s timeout)"
                    )
                    return False
                else:
                    print(f"[CHAIN DEBUG] Window initialized successfully")
                    # Add delay after window initialization (human-like behavior)
                    delay = truncated_normal_sample(0.3, 0.8)
                    print(f"[CHAIN DEBUG] Sleeping for {delay:.2f}s after window init")
                    time.sleep(delay)
                    print(f"[CHAIN DEBUG] Sleep completed, continuing execution")

            print(f"[CHAIN DEBUG] Resetting bot progress and starting thread")
            # Reset bot state directly (don't call methods that update UI via controller)
            bot.progress = 0
            bot.status = BotStatus.RUNNING

            # Don't reset BotSessionState during chains - we want to track cumulative XP
            # from the start of the chain. _starting_xp will be set the first time
            # XP is detected, and subsequent scripts will continue accumulating.
            session_state = BotSessionState()
            # session_state.reset()  # REMOVED - was clearing _starting_xp prematurely

            # Call on_start hook if exists
            if hasattr(bot, "on_start"):
                try:
                    print(f"[CHAIN DEBUG] Calling bot.on_start()")
                    bot.on_start()
                except Exception as exc:
                    print(f"[ERROR] on_start failed for {bot.bot_title}: {exc}")

            # Start the bot thread
            from model.bot import BotThread

            print(f"[CHAIN DEBUG] Creating and starting bot thread")
            bot.thread = BotThread(target=bot.main_loop)
            bot.thread.setDaemon(True)
            bot.thread.start()
            print(f"[CHAIN DEBUG] Bot thread started")

            # Use BotSession for timed execution
            print(
                f"[CHAIN DEBUG] Starting monitoring loop for {entry.running_time} minutes"
            )
            with BotSession(bot, entry.running_time) as session:
                # Monitor progress
                last_update_time = time.time()
                update_interval = 2.0  # Update UI every 2 seconds to avoid flooding

                while session.running and self.is_running:
                    current_time = time.time()

                    # Only update UI every 2 seconds to avoid overwhelming the event loop
                    if current_time - last_update_time >= update_interval:
                        print(
                            f"[CHAIN DEBUG] Firing progress callbacks - progress={bot.progress:.2f}, remaining={session.remaining_seconds}"
                        )
                        # Update script progress
                        if self.on_script_progress:
                            self.on_script_progress(
                                bot.progress, session.remaining_seconds
                            )

                        # Update overall chain progress
                        if self.on_chain_progress:
                            self.on_chain_progress(self.get_overall_progress())

                        last_update_time = current_time

                    time.sleep(
                        truncated_normal_sample(0.3, 0.8)
                    )  # Randomized update interval

            print(f"[CHAIN DEBUG] Monitoring loop ended, stopping bot thread")
            # Stop bot thread after session ends
            if bot.status == BotStatus.RUNNING:
                bot.status = BotStatus.STOPPED  # Set directly without controller
                if bot.thread is not None:
                    bot.thread.stop()
                    bot.thread.join(timeout=3)

            # Capture XP gained for this script and accumulate
            xp_gained = self._capture_script_xp()
            entry.xp_gained = sum(xp_gained.values())

            print(f"[CHAIN DEBUG] Script completed successfully")
            # Check if script completed successfully
            return bot.status == BotStatus.STOPPED

        except Exception as e:
            self._log_error(f"Script '{entry.script_name}' failed: {str(e)}")
            import traceback

            traceback.print_exc()

            # Ensure bot is stopped
            try:
                if bot.status == BotStatus.RUNNING:
                    bot.stop()
            except Exception as e2:
                self._log_error(f"Failed to stop bot '{entry.script_name}': {str(e2)}")

            return False

        finally:
            # Always stop thread if it was started
            if hasattr(bot, "thread") and bot.thread is not None:
                try:
                    if bot.thread.is_alive():
                        bot.thread.stop()
                        bot.thread.join(timeout=3)
                except Exception as cleanup_error:
                    print(f"[ERROR] Thread cleanup failed: {cleanup_error}")

            # Always restore the original controller
            print(f"[CHAIN DEBUG] Restoring original controller")
            bot.controller = original_controller

    def _capture_script_xp(self) -> Dict[str, int]:
        """
        Capture XP gained during the last script run and accumulate to chain totals.

        Returns:
            Dictionary mapping skill name to XP gained in this script
        """
        session_state = BotSessionState()
        script_xp = {}

        # Get XP gained for each skill in this script
        for skill in SKILL_ORDER:
            xp = session_state.get_xp_gained(skill)
            if xp > 0:
                script_xp[skill] = xp
                # Accumulate to chain totals (thread-safe)
                with self._xp_lock:
                    self.chain_xp_gained[skill] = (
                        self.chain_xp_gained.get(skill, 0) + xp
                    )

        return script_xp

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
        self.on_log_update: Optional[Callable[[str, bool]]] = None

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
        controller.on_log_update = self.on_log_update
