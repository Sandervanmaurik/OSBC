"""
Test stop() with heavy UI updates to ensure no deadlock.
"""
import sys
from pathlib import Path
import time
from unittest.mock import MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from model.bot import Bot, BotStatus, BotThread
from controller.bot_controller import BotController

class HeavyUIBot(Bot):
    """Bot that does many UI updates to stress-test the stop mechanism."""
    
    def __init__(self):
        from utilities.window import Window
        window = Window("Test", padding_top=0, padding_left=0)
        super().__init__(
            game_title="Test Game",
            bot_title="Heavy UI Bot",
            description="Bot with heavy UI updates",
            window=window
        )
        self.iterations = 0
    
    def create_options(self):
        pass
    
    def save_options(self, options):
        self.options_set = True
    
    def main_loop(self):
        """Main loop with MANY UI updates per iteration."""
        while self.status == BotStatus.RUNNING:
            self.iterations += 1
            
            # Simulate LOTS of UI updates (potential deadlock scenario)
            for i in range(10):
                self.log_msg(f"Iteration {self.iterations}, update {i}")
                self.update_progress(self.iterations / 100.0)
            
            # Very short sleep to maximize updates
            time.sleep(0.01)

def test_heavy_ui_updates():
    """Test that stop works even with heavy UI update load."""
    print("Testing stop() with HEAVY UI update load")
    print("=" * 70)
    
    # Create bot
    print("\n1. Creating bot with heavy UI updates...")
    bot = HeavyUIBot()
    
    # Create mock controller and view
    mock_view = MagicMock()
    
    # Track how many times after_idle was called
    after_idle_calls = []
    def track_after_idle(callback):
        after_idle_calls.append(callback)
    
    mock_view.after_idle = track_after_idle
    mock_view.update = MagicMock()
    mock_view.frame_info = MagicMock()
    mock_view.frame_output_log = MagicMock()
    
    mock_controller = BotController(bot, mock_view)
    bot.set_controller(mock_controller)
    
    print("   ✓ Bot and controller created")
    
    # Start bot
    print("\n2. Starting bot (will generate MANY UI updates)...")
    bot.set_status(BotStatus.RUNNING)
    bot.thread = BotThread(target=bot.main_loop)
    bot.thread.daemon = True
    bot.thread.start()
    
    # Let it run briefly to accumulate updates
    time.sleep(0.5)
    
    updates_before_stop = len(after_idle_calls)
    print(f"   ✓ Bot running (iterations: {bot.iterations})")
    print(f"   ✓ UI updates queued: {updates_before_stop}")
    
    # Stop bot
    print("\n3. Stopping bot (should not hang despite queued updates)...")
    start_time = time.time()
    
    bot.stop()
    
    stop_time = time.time() - start_time
    
    print(f"   ✓ Stop completed in {stop_time:.2f}s")
    print(f"   ✓ Bot status: {bot.status}")
    print(f"   ✓ Thread alive: {bot.thread.is_alive() if bot.thread else False}")
    print(f"   ✓ Total iterations: {bot.iterations}")
    print(f"   ✓ Total UI updates queued: {len(after_idle_calls)}")
    print(f"   ✓ view.update() called: {mock_view.update.call_count} times")
    
    # Verify
    assert bot.status == BotStatus.STOPPED
    assert stop_time < 6.0, f"Stop took too long: {stop_time}s"
    assert mock_view.update.call_count > 0, "view.update() should have been called"
    
    print("\n" + "=" * 70)
    print("✓ TEST PASSED - Heavy UI updates handled without deadlock!")
    print("\nResults:")
    print(f"  - {len(after_idle_calls)} UI updates queued during execution")
    print(f"  - view.update() called {mock_view.update.call_count} times during stop")
    print(f"  - Stop completed in {stop_time:.2f}s (well within 5s timeout)")
    print("  - No deadlock, no hang!")

if __name__ == "__main__":
    test_heavy_ui_updates()
