"""
Base class for background watcher threads.

Provides automatic background tracking pattern for game state watchers.
Encapsulates threading logic following the BehaviorManager pattern.
"""

import threading
import time
import weakref
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from utilities.window import Window

if TYPE_CHECKING:
    from model.bot import Bot


class BackgroundWatcher(ABC):
    """
    Base class for watchers that can run in background threads.

    Subclasses implement _poll() for their specific detection logic.
    Background threads automatically start/stop with bot lifecycle.

    Pattern based on BehaviorManager._fidget_thread.

    Example:
        class MyWatcher(BackgroundWatcher):
            POLL_INTERVAL = 1.0

            def _poll(self) -> None:
                # Perform detection and update state
                pass

        # In bot:
        watcher = MyWatcher(self.win)
        watcher.start_background(self)  # Spawns thread
        # ... bot runs ...
        watcher.stop_background()  # Stops thread cleanly
    """

    # Override in subclasses
    POLL_INTERVAL: float = 2.0

    def __init__(self, window: Window):
        """
        Initialize the background watcher.

        Args:
            window: Window instance with initialized game client
        """
        self.window = window
        self._stop_event: Optional[threading.Event] = None
        self._thread: Optional[threading.Thread] = None
        self._bot_ref: Optional[weakref.ref] = None
        self._background_started: bool = False

    @abstractmethod
    def _poll(self) -> None:
        """
        Perform one poll cycle.

        Implemented by subclasses to call their check() method.
        Called automatically by the background thread at POLL_INTERVAL.
        """
        pass

    def start_background(self, bot: "Bot") -> None:
        """
        Start background polling thread.

        The thread will automatically call _poll() at POLL_INTERVAL until
        the bot stops or stop_background() is called.

        Args:
            bot: Bot instance for status checking
        """
        if self._background_started:
            print(f"[{self.__class__.__name__}] Already running, skipping start")
            return  # Already running

        # Use weakref to avoid circular reference with bot
        self._bot_ref = weakref.ref(bot)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._background_loop,
            daemon=True,
            name=f"{self.__class__.__name__}Thread",
        )
        self._thread.start()
        self._background_started = True
        print(
            f"[{self.__class__.__name__}] Background thread started (poll interval: {self.POLL_INTERVAL}s)"
        )

    def stop_background(self) -> None:
        """
        Stop background thread cleanly.

        Signals the thread to stop and waits up to 2 seconds for it to exit.
        """
        if not self._background_started:
            print(f"[{self.__class__.__name__}] Not running, skipping stop")
            return

        print(f"[{self.__class__.__name__}] Stopping background thread...")

        # Set flag FIRST to prevent race condition with start_background()
        self._background_started = False

        if self._stop_event:
            self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            if self._thread.is_alive():
                print(
                    f"[{self.__class__.__name__}] Warning: Thread did not exit cleanly"
                )
            else:
                print(
                    f"[{self.__class__.__name__}] Background thread stopped successfully"
                )

        # Clean up all state
        self._stop_event = None
        self._thread = None
        self._bot_ref = None

    def _should_stop(self) -> bool:
        """
        Check if thread should exit.

        Returns:
            True if stop event is set or bot status is STOPPED
        """
        if self._stop_event and self._stop_event.is_set():
            return True

        # Check bot status (weak reference may be None if bot was garbage collected)
        bot = self._bot_ref() if self._bot_ref else None
        if bot is None:
            return True

        from model.bot import BotStatus

        # Only exit on STOPPED, not on PAUSED (thread continues during pause)
        if bot.status == BotStatus.STOPPED:
            return True

        return False

    def _background_loop(self) -> None:
        """
        Main polling loop (runs in background thread).

        Calls _poll() at POLL_INTERVAL until _should_stop() returns True.
        Sleeps in small chunks (0.25s) for responsive shutdown.
        """
        while not self._should_stop():
            try:
                self._poll()
            except Exception as e:
                # Log errors but don't crash the thread
                # Subclasses can override _poll() for custom error handling
                print(f"[{self.__class__.__name__}] Error in background thread: {e}")

            # Sleep in chunks to be responsive to stop signal
            slept = 0.0
            while slept < self.POLL_INTERVAL and not self._should_stop():
                time.sleep(0.25)
                slept += 0.25
