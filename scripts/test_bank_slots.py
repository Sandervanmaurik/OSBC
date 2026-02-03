#!/usr/bin/env python3
"""
Bank Slot Testing Tool - Tests dynamic OCR-based bank slot detection

This script tests the new locate_bank_slots() method that uses OCR to find
"The Bank of Gielinor" title and dynamically calculate bank slot positions.

IMPORTANT: Open the bank interface in-game BEFORE running this script!
"""

import sys
import time
from pathlib import Path

# Add project root and src/ to path
_repo_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))

import cv2
from utilities.window import Window, BankDetectionError


def main():
    """Main test function."""
    print("Bank Slot OCR Detection Test")
    print("=" * 70)
    print()
    print("INSTRUCTIONS:")
    print("  1. Make sure RuneLite is running (Fixed or Resizable mode)")
    print("  2. Open the bank interface in-game")
    print("  3. Run this script")
    print()
    print("This test uses OCR to find 'The Bank of Gielinor' title and")
    print("dynamically calculates bank slot positions. Works in both modes!")
    print()

    # Find and initialize window
    print("Initializing RuneLite window...")
    try:
        window = Window("RuneLite", padding_top=26, padding_left=0)
        window.initialize()
        print(f"Connected to window")
        print(f"   Client mode: {'Fixed' if window.client_fixed else 'Resizable'}")
        print(f"   Game view: {window.game_view.width}x{window.game_view.height}")
        print(
            f"   Control panel at: ({window.control_panel.left}, {window.control_panel.top})"
        )
    except Exception as e:
        print(f"Failed to initialize window: {e}")
        print("   Make sure RuneLite is running and visible!")
        return 1

    # Test bank slot detection with verbose logging
    print("\\nDetecting bank slots with OCR...")
    print("-" * 70)
    try:
        window.locate_bank_slots(verbose=True)
        print("-" * 70)
        print(f"Successfully detected {len(window.bank_slots)} bank slots")
    except BankDetectionError as e:
        print(f"Bank detection failed: {e}")
        print("\\nTroubleshooting:")
        print("  - Is the bank interface open?")
        print("  - Is 'The Bank of Gielinor' title visible?")
        print("  - Try both fixed and resizable modes")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # Create output directory
    output_dir = Path("debug_screenshots")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    session_dir = output_dir / f"{timestamp}_bank_ocr_test"
    session_dir.mkdir(parents=True, exist_ok=True)
    print(f"\\nSaving visual validation to: {session_dir}")

    # Capture and visualize
    print("\\nCreating visual validation...")
    try:
        game_view_img = window.game_view.screenshot()

        # Save raw
        raw_path = session_dir / "bank_raw.png"
        cv2.imwrite(str(raw_path), game_view_img)
        print(f"   Raw screenshot: bank_raw.png")

        # Create overlay with slot rectangles
        overlay = game_view_img.copy()

        for i, slot in enumerate(window.bank_slots):
            # Calculate relative position within game view
            rel_x = slot.left - window.game_view.left
            rel_y = slot.top - window.game_view.top

            # Draw green rectangle for each slot
            cv2.rectangle(
                overlay,
                (rel_x, rel_y),
                (rel_x + slot.width, rel_y + slot.height),
                (0, 255, 0),  # Green
                1,
            )

            # Draw slot number (smaller font for 9x9 grid)
            cv2.putText(
                overlay,
                str(i),
                (rel_x + 2, rel_y + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.25,  # Smaller font for 9x9 grid
                (0, 255, 0),
                1,
            )

        # Save overlay
        overlay_path = session_dir / "bank_with_slots.png"
        cv2.imwrite(str(overlay_path), overlay)
        print(f"   Slot overlay: bank_with_slots.png")

        # Capture individual slots (useful for debugging item detection)
        slots_dir = session_dir / "individual_bank_slots"
        slots_dir.mkdir(exist_ok=True)

        captured_count = 0
        for i, slot in enumerate(window.bank_slots):
            try:
                slot_screenshot = slot.screenshot()
                slot_path = slots_dir / f"bank_slot_{i:02d}.png"
                cv2.imwrite(str(slot_path), slot_screenshot)
                captured_count += 1
            except Exception as e:
                print(f"   Failed to capture slot {i}: {e}")

        print(
            f"   Individual slots: {captured_count}/{len(window.bank_slots)} in individual_bank_slots/"
        )

        # Save test report
        report_path = session_dir / "test_report.txt"
        with open(report_path, "w") as f:
            f.write("Bank Slot OCR Detection Test Report\\n")
            f.write("=" * 70 + "\\n\\n")
            f.write(f"Timestamp: {timestamp}\\n")
            f.write(
                f"Client Mode: {'Fixed' if window.client_fixed else 'Resizable'}\\n\\n"
            )
            f.write(f"Window Dimensions:\\n")
            f.write(
                f"  Game View: {window.game_view.width}x{window.game_view.height} at ({window.game_view.left}, {window.game_view.top})\\n"
            )
            f.write(
                f"  Control Panel: at ({window.control_panel.left}, {window.control_panel.top})\\n\\n"
            )
            f.write(f"Bank Slot Grid:\\n")
            f.write(f"  Total slots detected: {len(window.bank_slots)}\\n")
            f.write(f"  Expected: 81 slots (9 rows x 9 columns)\\n")
            f.write(f"  Match: {'YES' if len(window.bank_slots) == 81 else 'NO'}\\n\\n")
            f.write(f"Sample Slot Positions:\\n")
            f.write(
                f"  Slot 0 (top-left): ({window.bank_slots[0].left}, {window.bank_slots[0].top})\\n"
            )
            f.write(
                f"  Slot 8 (top-right): ({window.bank_slots[8].left}, {window.bank_slots[8].top})\\n"
            )
            f.write(
                f"  Slot 40 (center): ({window.bank_slots[40].left}, {window.bank_slots[40].top})\\n"
            )
            f.write(
                f"  Slot 72 (bottom-left): ({window.bank_slots[72].left}, {window.bank_slots[72].top})\\n"
            )
            f.write(
                f"  Slot 80 (bottom-right): ({window.bank_slots[80].left}, {window.bank_slots[80].top})\\n\\n"
            )
            f.write(f"Detection Method:\\n")
            f.write(f"  Uses OCR to find 'The Bank of Gielinor' title\\n")
            f.write(f"  Dynamically calculates bank interface position\\n")
            f.write(f"  Generates 9x9 grid (81 slots) with proper spacing\\n")
            f.write(f"  Works in both Fixed and Resizable modes\\n")

        print(f"   Test report: test_report.txt")

        print("\\n" + "=" * 70)
        print("TEST SUCCESSFUL!")
        print("=" * 70)
        print(f"\\nVisual Validation File:")
        print(f"   {overlay_path.absolute()}")
        print("\\nVerification Checklist:")
        print("   1. Open bank_with_slots.png")
        print("   2. Check that green rectangles align with bank item slots")
        print("   3. Verify slot numbers 0-80 are visible and in correct order")
        print("   4. Confirm grid covers all 9 rows x 9 columns")
        print("\\nNext Steps:")
        print("   - If alignment looks good, the OCR detection is working!")
        print("   - Test in both Fixed and Resizable modes")
        print("   - Try with different bank interfaces (booth, chest, NPC)")

    except Exception as e:
        print(f"Failed to create visualizations: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
