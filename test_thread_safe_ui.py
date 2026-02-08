"""
Test script for Phase 4: Thread-safe UI updates.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, call

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from controller.bot_controller import BotController
from model.bot import Bot, BotStatus

def test_thread_safe_ui_updates():
    """Test that BotController methods use thread-safe UI updates."""
    print("Testing Phase 4: Thread-Safe UI Updates")
    print("=" * 60)
    
    # Create mock model and view
    print("\n1. Setting up mock model and view...")
    model = MagicMock(spec=Bot)
    model.status = BotStatus.STOPPED
    model.progress = "50%"
    
    view = MagicMock()
    view.after_idle = MagicMock()
    view.frame_info = MagicMock()
    view.frame_skills = MagicMock()
    view.frame_output_log = MagicMock()
    
    controller = BotController(model, view)
    print("   ✓ Mock controller created")
    
    # Test _schedule_ui_update exists
    print("\n2. Testing _schedule_ui_update method exists...")
    assert hasattr(controller, '_schedule_ui_update'), "Missing _schedule_ui_update"
    print("   ✓ _schedule_ui_update method exists")
    
    # Test update_status uses after_idle
    print("\n3. Testing update_status is thread-safe...")
    model.status = BotStatus.RUNNING
    controller.update_status()
    
    # Verify after_idle was called
    assert view.after_idle.called, "update_status should call after_idle"
    print(f"   ✓ after_idle called: {view.after_idle.call_count} time(s)")
    
    # Execute the scheduled callback
    callback = view.after_idle.call_args[0][0]
    callback()
    
    # Verify the UI was updated
    assert view.frame_info.update_status_running.called, "Should update UI"
    print("   ✓ UI update callback works correctly")
    
    # Test update_log uses after_idle
    print("\n4. Testing update_log is thread-safe...")
    view.after_idle.reset_mock()
    controller.update_log("Test message")
    
    assert view.after_idle.called, "update_log should call after_idle"
    print("   ✓ update_log uses after_idle")
    
    # Execute callback
    callback = view.after_idle.call_args[0][0]
    callback()
    assert view.frame_output_log.update_log.called, "Should call update_log"
    print("   ✓ Log update callback works")
    
    # Test update_progress uses after_idle
    print("\n5. Testing update_progress is thread-safe...")
    view.after_idle.reset_mock()
    controller.update_progress()
    
    assert view.after_idle.called, "update_progress should call after_idle"
    print("   ✓ update_progress uses after_idle")
    
    # Test update_state uses after_idle
    print("\n6. Testing update_state is thread-safe...")
    view.after_idle.reset_mock()
    controller.update_state("Mining ore")
    
    assert view.after_idle.called, "update_state should call after_idle"
    print("   ✓ update_state uses after_idle")
    
    # Test update_skills uses after_idle
    print("\n7. Testing update_skills is thread-safe...")
    view.after_idle.reset_mock()
    controller.update_skills({"Mining": 50})
    
    assert view.after_idle.called, "update_skills should call after_idle"
    print("   ✓ update_skills uses after_idle")
    
    # Test clear_log uses after_idle
    print("\n8. Testing clear_log is thread-safe...")
    view.after_idle.reset_mock()
    controller.clear_log()
    
    assert view.after_idle.called, "clear_log should call after_idle"
    print("   ✓ clear_log uses after_idle")
    
    # Test fallback when view doesn't have after_idle
    print("\n9. Testing fallback for views without after_idle...")
    view_no_idle = MagicMock()
    del view_no_idle.after_idle  # Remove after_idle
    view_no_idle.frame_output_log = MagicMock()
    
    controller_fallback = BotController(model, view_no_idle)
    controller_fallback.update_log("Fallback test")
    
    # Should call update_log directly
    assert view_no_idle.frame_output_log.update_log.called, "Fallback should work"
    print("   ✓ Fallback to direct call works")
    
    print("\n" + "=" * 60)
    print("✓ Phase 4 test complete!")
    print("\nKey improvements:")
    print("  - All UI update methods now use _schedule_ui_update()")
    print("  - Updates are deferred to main thread via after_idle()")
    print("  - Prevents cross-thread Tkinter access (beach ball on macOS)")
    print("  - Values captured before scheduling to avoid race conditions")

if __name__ == "__main__":
    test_thread_safe_ui_updates()
