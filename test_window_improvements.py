"""
Test script for Phase 2: Window utility with focus caching.
"""
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utilities.window import Window

def test_window_improvements():
    """Test the improved Window class."""
    print("Testing Phase 2: Window Utility Improvements")
    print("=" * 60)
    
    # Create Window instance
    print("\n1. Creating Window instance...")
    window = Window("RuneLite", padding_top=0, padding_left=0)
    print("   ✓ Window created")
    
    # Test platform window is created lazily
    print("\n2. Testing lazy window initialization...")
    assert window._platform_window is None, "Platform window should be None initially"
    print("   ✓ Platform window not created yet")
    
    # Test first access creates platform window
    print("\n3. Testing first window access...")
    start = time.time()
    _ = window.window
    elapsed = (time.time() - start) * 1000
    print(f"   ✓ First access: {elapsed:.1f}ms")
    assert window._platform_window is not None, "Platform window should be created"
    print("   ✓ Platform window cached")
    
    # Test cached access is faster
    print("\n4. Testing cached window access...")
    start = time.time()
    for _ in range(10):
        _ = window.window
    elapsed = (time.time() - start) * 1000
    avg = elapsed / 10
    print(f"   ✓ 10 accesses: {elapsed:.1f}ms total, {avg:.1f}ms avg")
    
    # Test position() and rectangle()
    print("\n5. Testing position() and rectangle()...")
    start = time.time()
    pos = window.position()
    rect = window.rectangle()
    elapsed = (time.time() - start) * 1000
    print(f"   ✓ Position: ({pos.x}, {pos.y})")
    print(f"   ✓ Rectangle: {rect.width}x{rect.height}")
    print(f"   ⏱  Time: {elapsed:.1f}ms")
    
    # Test focus caching
    print("\n6. Testing smart focus checking...")
    
    # First check should actually check
    print("   - First check (should check)...")
    start = time.time()
    should_check = window.should_check_focus()
    elapsed = (time.time() - start) * 1000
    print(f"     should_check_focus(): {should_check}, {elapsed:.3f}ms")
    assert should_check, "First check should return True"
    
    # Do the cached check
    start = time.time()
    result1 = window.check_focus_cached()
    elapsed = (time.time() - start) * 1000
    print(f"     check_focus_cached(): {result1}, {elapsed:.1f}ms")
    
    # Immediate second check should use cache
    print("   - Immediate second check (should use cache)...")
    start = time.time()
    should_check = window.should_check_focus()
    elapsed = (time.time() - start) * 1000
    print(f"     should_check_focus(): {should_check}, {elapsed:.3f}ms")
    assert not should_check, "Immediate check should use cache"
    
    start = time.time()
    result2 = window.check_focus_cached()
    elapsed = (time.time() - start) * 1000
    print(f"     check_focus_cached(): {result2}, {elapsed:.3f}ms (cached!)")
    assert result1 == result2, "Cached result should match"
    
    # Test focus sequence
    print("\n7. Testing focus_sequence context manager...")
    start = time.time()
    with window.focus_sequence():
        # These should not check focus
        for i in range(5):
            should_check = window.should_check_focus()
            print(f"     Iteration {i+1}: should_check = {should_check}")
            assert not should_check, f"Check {i+1} should use sequence state"
    elapsed = (time.time() - start) * 1000
    print(f"   ✓ Sequence completed in {elapsed:.1f}ms")
    
    # After sequence, cache should be invalidated
    print("   - After sequence, cache should be invalidated...")
    should_check = window.should_check_focus()
    print(f"     should_check_focus(): {should_check}")
    assert should_check, "Cache should be invalidated after sequence"
    
    print("\n" + "=" * 60)
    print("✓ Phase 2 test complete!")

if __name__ == "__main__":
    test_window_improvements()
