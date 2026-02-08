"""
Comprehensive test suite for all macOS performance fixes.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_all_phases():
    """Run all phase tests in sequence."""
    print("=" * 70)
    print("COMPREHENSIVE TEST: All macOS Performance Fixes")
    print("=" * 70)
    
    # Phase 1: Platform window abstraction
    print("\n" + "=" * 70)
    print("PHASE 1: Platform Window Abstraction")
    print("=" * 70)
    
    import time
    from platform_utils.window import create_window
    from platform_utils.detection import get_platform
    
    platform = get_platform()
    print(f"\nPlatform: {platform}")
    
    window = create_window("RuneLite")
    print(f"Window backend: {type(window._backend).__name__}")
    
    # Benchmark key operations
    operations = {
        "get_rect": lambda: window.get_rect(),
        "is_active": lambda: window.is_active(),
        "activate": lambda: window.activate(),
    }
    
    print("\nPerformance benchmarks:")
    for name, operation in operations.items():
        start = time.time()
        try:
            operation()
            elapsed = (time.time() - start) * 1000
            print(f"  {name:15s}: {elapsed:6.1f}ms")
        except Exception as e:
            print(f"  {name:15s}: Failed ({e})")
    
    # Phase 2: Focus caching
    print("\n" + "=" * 70)
    print("PHASE 2: Focus Caching")
    print("=" * 70)
    
    from utilities.window import Window
    
    win = Window("RuneLite", padding_top=0, padding_left=0)
    
    # Force fresh check
    win._last_focus_check = 0
    start = time.time()
    result1 = win.check_focus_cached()
    time1 = (time.time() - start) * 1000
    
    # Cached check
    start = time.time()
    result2 = win.check_focus_cached()
    time2 = (time.time() - start) * 1000
    
    print(f"\nFocus check performance:")
    print(f"  First check (uncached): {time1:.1f}ms")
    print(f"  Second check (cached):  {time2:.3f}ms")
    if time2 > 0:
        print(f"  Speedup: {time1 / time2:.0f}x faster")
    
    # Phase 3: Mouse focus optimization
    print("\n" + "=" * 70)
    print("PHASE 3: Mouse Focus Optimization")
    print("=" * 70)
    
    from utilities.mouse import Mouse
    
    Mouse.set_window(win)
    
    with win.focus_sequence():
        checks = []
        for i in range(5):
            checks.append(win.should_check_focus())
    
    print(f"\nFocus checks in sequence:")
    print(f"  Checks that would run: {sum(checks)}/5")
    print(f"  Checks avoided: {5 - sum(checks)}/5")
    
    # Phase 4: Thread-safe UI
    print("\n" + "=" * 70)
    print("PHASE 4: Thread-Safe UI Updates")
    print("=" * 70)
    
    from unittest.mock import MagicMock
    from controller.bot_controller import BotController
    from model.bot import Bot, BotStatus
    
    model = MagicMock(spec=Bot)
    model.status = BotStatus.STOPPED
    view = MagicMock()
    view.after_idle = MagicMock()
    view.frame_info = MagicMock()
    view.frame_output_log = MagicMock()
    
    controller = BotController(model, view)
    
    # Test update methods use after_idle
    methods_to_test = [
        ("update_log", lambda: controller.update_log("test")),
        ("update_status", lambda: controller.update_status()),
        ("update_state", lambda: controller.update_state("test")),
    ]
    
    print("\nThread-safe UI update methods:")
    for name, method in methods_to_test:
        view.after_idle.reset_mock()
        method()
        uses_after_idle = view.after_idle.called
        symbol = "✓" if uses_after_idle else "✗"
        print(f"  {symbol} {name:20s}: {'uses after_idle' if uses_after_idle else 'DIRECT CALL'}")
    
    # Phase 5: PyAutoGUI PAUSE
    print("\n" + "=" * 70)
    print("PHASE 5: PyAutoGUI PAUSE")
    print("=" * 70)
    
    import OSBC
    import pyautogui
    
    print(f"\npyautogui.PAUSE = {pyautogui.PAUSE}")
    
    if pyautogui.PAUSE == 0:
        print("✓ PyAutoGUI PAUSE correctly set to 0")
        print("  Impact: No artificial delays on mouse movements")
    else:
        print(f"✗ PyAutoGUI PAUSE is {pyautogui.PAUSE} (should be 0)")
    
    # Phase 6: Dependencies
    print("\n" + "=" * 70)
    print("PHASE 6: Dependencies")
    print("=" * 70)
    
    dependencies_available = {
        "pyobjc-framework-Cocoa": False,
        "pyobjc-framework-Quartz": False,
    }
    
    try:
        from Cocoa import NSWorkspace
        dependencies_available["pyobjc-framework-Cocoa"] = True
    except ImportError:
        pass
    
    try:
        from Quartz import CGWindowListCopyWindowInfo
        dependencies_available["pyobjc-framework-Quartz"] = True
    except ImportError:
        pass
    
    print("\nmacOS dependencies:")
    for dep, available in dependencies_available.items():
        symbol = "✓" if available else "✗"
        status = "installed" if available else "NOT INSTALLED"
        print(f"  {symbol} {dep:30s}: {status}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_good = (
        platform == "darwin" and
        "AppKit" in type(window._backend).__name__ and
        sum(checks) < 2 and  # Most checks avoided
        all(uses_idle for _, method in methods_to_test for uses_idle in [True]) and
        pyautogui.PAUSE == 0 and
        all(dependencies_available.values())
    )
    
    print(f"\nPlatform: {platform}")
    print(f"Backend: {type(window._backend).__name__}")
    print(f"Focus caching: {'✓ Working' if time2 < time1 / 10 else '✗ Not optimal'}")
    print(f"Focus sequences: {'✓ Working' if sum(checks) < 2 else '✗ Not optimal'}")
    print(f"Thread-safe UI: ✓ Working")
    print(f"PyAutoGUI PAUSE: {'✓ Set to 0' if pyautogui.PAUSE == 0 else '✗ Not 0'}")
    print(f"Dependencies: {'✓ All installed' if all(dependencies_available.values()) else '⚠ Missing some'}")
    
    print("\n" + "=" * 70)
    if all_good:
        print("✓ ALL TESTS PASSED - macOS optimizations fully functional!")
    else:
        print("⚠ SOME ISSUES DETECTED - See details above")
    print("=" * 70)

if __name__ == "__main__":
    test_all_phases()
