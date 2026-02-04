#!/usr/bin/env python3
"""
XP Watcher Debug Tool

Test the XP watcher and visualize the detection area.

Usage:
    # Save debug screenshot showing XP detection area
    python scripts/test_xp_watcher.py --screenshot

    # Test XP detection (prints when XP is detected)
    python scripts/test_xp_watcher.py --monitor

    # Test icon matching on a captured screenshot
    python scripts/test_xp_watcher.py --test-icon path/to/xp_area_closeup.png

    # Test with custom check interval
    python scripts/test_xp_watcher.py --monitor --interval 1.0
"""

import sys
import time
import argparse
from pathlib import Path
import cv2

# Add project root to path
_repo_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))

from utilities.window import Window
from utilities.xp_watcher import XPWatcher, SKILL_ICON_CONFIDENCE_THRESHOLD
from model.skills import SkillsManager


def test_screenshot(window_title: str = "RuneLite"):
    """
    Save debug screenshot showing XP detection area.

    Args:
        window_title: Game window title
    """
    print(" XP Watcher - Debug Screenshot Mode")
    print("=" * 50)

    # Initialize window
    try:
        print(f"Connecting to window: '{window_title}'...")
        window = Window(window_title, padding_top=26, padding_left=0)
        window.initialize()
        print(f" Connected successfully")
        print(f"   Client mode: {'Fixed' if window.client_fixed else 'Resizable'}")
    except Exception as e:
        print(f" Failed to initialize window: {e}")
        print("   Make sure the game client is running")
        return 1

    # Create XP watcher
    print("\n Creating XP watcher...")
    watcher = XPWatcher(window)

    # Save debug screenshot
    print("\n Saving debug screenshot...")
    output_path = watcher.save_debug_screenshot("xp_watcher_test")

    if output_path:
        print(f"\n Debug screenshot saved!")
        print(f"   Location: {output_path}")
        print(f"\n Next steps:")
        print(f"   1. Open the screenshot to verify XP detection area is correct")
        print(f"   2. If the area is wrong, adjust coordinates in xp_watcher.py")
        print(f"   3. Run this script again to verify changes")
    else:
        print(f"\n Failed to save debug screenshot")
        return 1

    return 0


def test_monitor(
    window_title: str = "RuneLite", check_interval: float = 2.0, duration: int = 60
):
    """
    Monitor XP detection in real-time.

    Args:
        window_title: Game window title
        check_interval: How often to check for XP (seconds)
        duration: How long to monitor (seconds)
    """
    print(" XP Watcher - Monitor Mode")
    print("=" * 50)
    print(f"Check interval: {check_interval}s")
    print(f"Duration: {duration}s")
    print("\n  Skill icons loaded automatically from src/images/bot/skills/")
    print("\n Start gaining XP in-game...")
    print("=" * 50)

    # Initialize window
    try:
        window = Window(window_title, padding_top=26, padding_left=0)
        window.initialize()
        print(f" Connected to '{window_title}'")
    except Exception as e:
        print(f" Failed to initialize window: {e}")
        return 1

    # Create XP watcher
    watcher = XPWatcher(window, debug=True)
    watcher.CHECK_INTERVAL = check_interval

    # Templates are auto-loaded in __init__, check status
    if not watcher._skill_templates_loaded:
        print("  Warning: No skill icon templates found")
        print("   XP amounts will be detected, but skills won't be identified")

    # Monitor loop
    start_time = time.time()
    checks = 0
    detections = 0

    print(f"\n Monitoring for XP...")

    try:
        while time.time() - start_time < duration:
            if watcher.should_check():
                checks += 1
                detected = watcher.check_for_xp()

                if detected:
                    detections += 1
                    print(f" XP detected! (#{detections})")

                # Print status every 10 checks
                if checks % 10 == 0:
                    elapsed = time.time() - start_time
                    print(
                        f"[{elapsed:.0f}s] Checks: {checks}, Detections: {detections}"
                    )

            time.sleep(0.1)  # Small sleep to prevent busy loop

    except KeyboardInterrupt:
        print(f"\n  Monitoring stopped by user")

    # Summary
    elapsed = time.time() - start_time
    print(f"\n Monitoring Summary:")
    print(f"   Duration: {elapsed:.1f}s")
    print(f"   Checks: {checks}")
    print(f"   Detections: {detections}")
    print(f"   Detection rate: {detections / checks * 100 if checks > 0 else 0:.1f}%")

    return 0


def test_area_adjustment(window_title: str = "RuneLite"):
    """
    Interactive tool to adjust XP detection area.

    Args:
        window_title: Game window title
    """
    print(" XP Watcher - Area Adjustment Mode")
    print("=" * 50)
    print("This will help you fine-tune the XP detection area")

    # Initialize window
    try:
        window = Window(window_title, padding_top=26, padding_left=0)
        window.initialize()
        print(f" Connected to '{window_title}'")
    except Exception as e:
        print(f" Failed to initialize window: {e}")
        return 1

    # Create watcher
    watcher = XPWatcher(window)

    print(f"\n Current XP Area Configuration:")
    print(f"   Left: {watcher._xp_area.left}")
    print(f"   Top: {watcher._xp_area.top}")
    print(f"   Width: {watcher._xp_area.width}")
    print(f"   Height: {watcher._xp_area.height}")

    print(f"\n Minimap Position (reference):")
    print(f"   Left: {window.minimap_area.left}")
    print(f"   Top: {window.minimap_area.top}")
    print(f"   Width: {window.minimap_area.width}")
    print(f"   Height: {window.minimap_area.height}")

    print(f"\n To adjust:")
    print(f"   1. Gain some XP in-game")
    print(f"   2. Run: python scripts/test_xp_watcher.py --screenshot")
    print(f"   3. Check if green box covers the XP popup")
    print(
        f"   4. Adjust values in src/utilities/xp_watcher.py (_calculate_xp_area method)"
    )
    print(f"   5. Repeat until correctly positioned")

    return 0


def test_icon_matching(screenshot_path: Path, window_title: str = "RuneLite"):
    """
    Test skill icon matching on a captured XP popup screenshot.

    Args:
        screenshot_path: Path to XP popup screenshot
        window_title: Game window title (for watcher initialization)
    """
    print("🎯 XP Watcher - Icon Matching Test")
    print("=" * 50)

    # Load screenshot
    if not screenshot_path.exists():
        print(f"❌ Screenshot not found: {screenshot_path}")
        return 1

    screenshot = cv2.imread(str(screenshot_path))
    if screenshot is None:
        print(f"❌ Failed to load screenshot: {screenshot_path}")
        return 1

    print(f"📸 Loaded screenshot: {screenshot_path}")
    print(f"   Size: {screenshot.shape[1]}x{screenshot.shape[0]} pixels")

    # Initialize window (needed for XPWatcher init, but won't be used)
    try:
        window = Window(window_title, padding_top=26, padding_left=0)
        window.initialize()
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to window (using dummy window)")
        print(f"   This is OK for icon testing - proceeding anyway...")
        # Create a minimal window object for testing
        from utilities.geometry import Rectangle

        window = Window(window_title, padding_top=26, padding_left=0)
        window.minimap_area = Rectangle(left=100, top=100, width=146, height=151)

    # Create XP watcher with debug mode
    print("\n🔧 Initializing XP watcher...")
    watcher = XPWatcher(window, debug=True)

    if not watcher._skill_templates_loaded:
        print(f"❌ No skill templates loaded!")
        print(f"   Expected location: src/images/bot/skills/")
        return 1

    print(f"✅ Loaded {len(watcher._skill_templates)} skill templates")

    # Test icon matching
    print(f"\n🔍 Testing icon matching...")
    skill_name, confidence = watcher._match_skill_icon(screenshot)

    # Display results
    print(f"\n" + "=" * 50)
    print(f"📊 Results:")
    print(f"=" * 50)
    print(f"   Skill detected: {skill_name or 'None'}")
    print(f"   Confidence: {confidence:.2%}")
    print(f"   Threshold: {SKILL_ICON_CONFIDENCE_THRESHOLD:.2%}")
    print(f"=" * 50)

    if skill_name:
        print(f"\n✅ Match successful!")
        print(f"   The XP popup was identified as: {skill_name.upper()}")
        print(
            f"   Confidence is {confidence:.2%} (above {SKILL_ICON_CONFIDENCE_THRESHOLD:.2%} threshold)"
        )
    else:
        print(f"\n❌ No match found")
        if confidence > 0:
            best_skill_msg = f" (best match had {confidence:.2%} confidence)"
        else:
            best_skill_msg = ""
        print(f"   Confidence too low{best_skill_msg}")
        print(f"\n💡 Suggestions:")
        print(
            f"   - Ensure the screenshot shows the XP popup icon in the first 25 pixels from the left"
        )
        print(f"   - Check that the icon is clearly visible and not blurred")
        print(f"   - Verify the screenshot is from the XP popup area (not full client)")
        if confidence > 0.5:
            print(
                f"   - The confidence ({confidence:.2%}) is close to threshold ({SKILL_ICON_CONFIDENCE_THRESHOLD:.2%})"
            )
            print(
                f"     Consider adjusting SKILL_ICON_CONFIDENCE_THRESHOLD in xp_watcher.py"
            )

    return 0 if skill_name else 1


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="XP Watcher Debug and Test Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--window", default="RuneLite", help="Game window title")

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--screenshot",
        action="store_true",
        help="Save debug screenshot showing XP detection area",
    )
    mode_group.add_argument(
        "--monitor", action="store_true", help="Monitor for XP detection in real-time"
    )
    mode_group.add_argument(
        "--adjust",
        action="store_true",
        help="Show current area configuration and adjustment guide",
    )
    mode_group.add_argument(
        "--test-icon",
        type=Path,
        metavar="SCREENSHOT",
        help="Test icon matching on a captured XP popup screenshot",
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Check interval for monitor mode (seconds)",
    )
    parser.add_argument(
        "--duration", type=int, default=60, help="Duration for monitor mode (seconds)"
    )

    args = parser.parse_args()

    try:
        if args.screenshot:
            return test_screenshot(args.window)
        elif args.monitor:
            return test_monitor(args.window, args.interval, args.duration)
        elif args.adjust:
            return test_area_adjustment(args.window)
        elif args.test_icon:
            return test_icon_matching(args.test_icon, args.window)

    except Exception as e:
        print(f"\n Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
