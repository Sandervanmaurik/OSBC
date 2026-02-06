"""
Test that cooking bot options persist across reload_model() calls.

This test verifies the fix for the bug where selecting "Raw salmon" in options
would reset to "Raw shrimp" when clicking Start due to reload_model() creating
a new instance without transferring options.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from model.osrs.cooking import OSRSCooking


def test_options_persistence():
    """Test that options are stored and can be retrieved."""
    print("Test 1: Options are stored in self.options")

    # Create bot instance
    bot = OSRSCooking()

    # Verify defaults
    assert bot.fish_type == "Raw shrimp", (
        f"Expected 'Raw shrimp', got '{bot.fish_type}'"
    )
    assert bot.running_time == 60, f"Expected 60, got {bot.running_time}"

    # Save options
    options = {"fish_type": "Raw salmon", "running_time": 111}
    bot.save_options(options)

    # Verify options were applied
    assert bot.fish_type == "Raw salmon", (
        f"Expected 'Raw salmon', got '{bot.fish_type}'"
    )
    assert bot.running_time == 111, f"Expected 111, got {bot.running_time}"

    # CRITICAL: Verify options dict is stored for reload_model()
    assert hasattr(bot, "options"), (
        "Bot must have 'options' attribute for reload_model()"
    )
    assert bot.options == options, f"Expected {options}, got {bot.options}"

    print("✓ Test 1 PASSED")


def test_reload_model_simulation():
    """Simulate what reload_model() does and verify options transfer."""
    print("\nTest 2: Simulating reload_model() behavior")

    # Create first bot instance
    old_bot = OSRSCooking()

    # Save options
    options = {"fish_type": "Raw lobster", "running_time": 222}
    old_bot.save_options(options)

    print(
        f"  Old bot: fish_type='{old_bot.fish_type}', running_time={old_bot.running_time}"
    )

    # Simulate reload_model() creating new instance
    new_bot = OSRSCooking()

    print(
        f"  New bot (before transfer): fish_type='{new_bot.fish_type}', running_time={new_bot.running_time}"
    )

    # Simulate reload_model() transferring options
    if hasattr(old_bot, "options"):
        new_bot.save_options(old_bot.options)
        print(
            f"  New bot (after transfer): fish_type='{new_bot.fish_type}', running_time={new_bot.running_time}"
        )
    else:
        print("  ERROR: old_bot has no 'options' attribute!")
        assert False, "Old bot must have 'options' attribute"

    # Verify transfer worked
    assert new_bot.fish_type == "Raw lobster", (
        f"Expected 'Raw lobster', got '{new_bot.fish_type}'"
    )
    assert new_bot.running_time == 222, f"Expected 222, got {new_bot.running_time}"

    print("✓ Test 2 PASSED")


def test_all_fish_types():
    """Test that all fish types can be selected and persisted."""
    print("\nTest 3: Testing all fish types")

    for fish_type in OSRSCooking.FISH_TYPES:
        bot = OSRSCooking()
        options = {"fish_type": fish_type, "running_time": 100}
        bot.save_options(options)

        assert bot.fish_type == fish_type, (
            f"Expected '{fish_type}', got '{bot.fish_type}'"
        )
        assert bot.options["fish_type"] == fish_type, (
            f"Options dict not updated for {fish_type}"
        )
        print(f"  ✓ {fish_type} works")

    print("✓ Test 3 PASSED")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Cooking Bot Options Persistence")
    print("=" * 60)

    try:
        test_options_persistence()
        test_reload_model_simulation()
        test_all_fish_types()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nThe cooking bot should now correctly persist options when")
        print("you click Start (which triggers reload_model()).")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
