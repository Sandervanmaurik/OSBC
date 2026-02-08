"""
Test script for platform window abstraction.
"""
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from platform_utils.window import create_window
from platform_utils.detection import get_platform

def test_window_backend():
    """Test the window backend with RuneLite."""
    print(f"Platform: {get_platform()}")
    print("=" * 60)
    
    # Test window creation
    print("\n1. Creating window for 'RuneLite'...")
    try:
        window = create_window("RuneLite")
        print(f"   ✓ Window created: {window.title}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return
    
    # Test get_rect (measures performance)
    print("\n2. Testing get_rect() performance...")
    start = time.time()
    try:
        rect = window.get_rect()
        elapsed = (time.time() - start) * 1000
        print(f"   ✓ Rect: {rect.left}, {rect.top}, {rect.width}x{rect.height}")
        print(f"   ⏱  Time: {elapsed:.1f}ms")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        print(f"   ✗ Failed: {e}")
        print(f"   ⏱  Time: {elapsed:.1f}ms")
    
    # Test is_active
    print("\n3. Testing is_active() performance...")
    start = time.time()
    try:
        is_active = window.is_active()
        elapsed = (time.time() - start) * 1000
        print(f"   ✓ Active: {is_active}")
        print(f"   ⏱  Time: {elapsed:.1f}ms")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        print(f"   ✗ Failed: {e}")
        print(f"   ⏱  Time: {elapsed:.1f}ms")
    
    # Test activate
    print("\n4. Testing activate() performance...")
    start = time.time()
    try:
        window.activate()
        elapsed = (time.time() - start) * 1000
        print(f"   ✓ Activated")
        print(f"   ⏱  Time: {elapsed:.1f}ms")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        print(f"   ✗ Failed: {e}")
        print(f"   ⏱  Time: {elapsed:.1f}ms")
    
    # Test compatibility properties
    print("\n5. Testing pywinctl compatibility properties...")
    try:
        box = window.box
        is_active = window.isActive
        is_min = window.isMinimized
        print(f"   ✓ .box: {box.width}x{box.height}")
        print(f"   ✓ .isActive: {is_active}")
        print(f"   ✓ .isMinimized: {is_min}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Phase 1 test complete!")

if __name__ == "__main__":
    test_window_backend()
