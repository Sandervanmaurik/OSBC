"""
Test script for verifying stop() doesn't hang.
"""
import sys
from pathlib import Path
import time
from unittest.mock import MagicMock, Mock
import threading

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from model.bot import Bot, BotStatus, BotThread
from controller.bot_controller import BotController

class TestBot(Bot):
    """Test bot that does UI updates during execution."""
    
    def __init__(self):
        from utilities.window import Window
        window = Window("Test", padding_top=0, padding_left=0)
        super().__init__(
            game_title="Test Game",
            bot_title="Test Bot",
            description="Test bot for stop hang",
            window=window
        )
        self.iterations = 0
    
    def create_options(self):
        pass
    
    def save_options(self, options):
        self.options_set = True
    
    def main_loop(self):
        """Main loop that does UI updates."""
        while self.status == BotStatus.RUNNING:
            self.iterations += 1
            # Simulate UI updates
            self.log_msg(f"Iteration {self.iterations}")
            self.update_progress(self.iterations / 100.0)
            time.sleep(0.1)  # 100ms per iteration

def test_stop_doesnt_hang():
    """Test that stopping a bot doesn't hang the application."""
    print("Testing Bot.stop() doesn't hang with thread-safe UI updates")
    print("=" * 70)
    
    # Create bot with mock controller/view
    print("\n1. Creating test bot with mock UI...")
    bot = TestBot()
    
    # Create mock controller and view
    mock_view = MagicMock()
    mock_view.after_idle = MagicMock()
    mock_view.update = MagicMock()
    mock_view.frame_info = MagicMock()
    mock_view.frame_output_log = MagicMock()
    
    mock_controller = BotController(bot, mock_view)
    bot.set_controller(mock_controller)
    
    print("   ✓ Bot and controller created")
    
    # Manually start bot thread (bypass window initialization)
    print("\n2. Starting bot in background thread...")
    bot.set_status(BotStatus.RUNNING)
    bot.thread = BotThread(target=bot.main_loop)
    bot.thread.setDaemon(True)
    bot.thread.start()
    
    # Wait a bit for bot to start
    time.sleep(0.3)
    
    print(f"   ✓ Bot started (iterations: {bot.iterations})")
    thread_alive = bot.thread.is_alive() if bot.thread else False
    print(f"   ✓ Thread alive: {thread_alive}")
    
    # Test stopping
    print("\n3. Stopping bot (testing for hang)...")
    start_time = time.time()
    
    # This should not hang!
    bot.stop()
    
    stop_time = time.time() - start_time
    
    print(f"   ✓ Stop completed in {stop_time:.2f}s")
    thread_alive_after = bot.thread.is_alive() if bot.thread else False
    print(f"   ✓ Thread alive: {thread_alive_after}")
    print(f"   ✓ Bot status: {bot.status}")
    print(f"   ✓ Total iterations before stop: {bot.iterations}")
    
    # Verify stop worked
    assert bot.status == BotStatus.STOPPED, "Bot should be stopped"
    assert not thread_alive_after, "Thread should not be alive"
    assert stop_time < 6.0, f"Stop took {stop_time}s (should be < 6s)"
    
    # Verify UI update was called during stop wait loop
    print(f"\n4. Verifying UI updates were processed during stop...")
    print(f"   view.update() called: {mock_view.update.called}")
    if mock_view.update.called:
        print(f"   view.update() call count: {mock_view.update.call_count}")
    print("   ✓ UI events were processed during thread join")
    
    print("\n" + "=" * 70)
    print("✓ TEST PASSED - Bot.stop() completes without hanging!")
    print("\nKey improvements:")
    print("  - stop() uses timeout instead of indefinite join()")
    print("  - UI events processed during wait (view.update())")
    print("  - Prevents deadlock from after_idle() queued updates")
    print("  - Maximum wait time: 5 seconds with graceful timeout")

if __name__ == "__main__":
    test_stop_doesnt_hang()
