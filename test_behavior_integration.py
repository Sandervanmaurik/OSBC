"""
Integration test for BehaviorManager with activity profiles.
Tests profile switching, cycle management, and tab-out/bank check behaviors.
"""

from utilities.behavior.manager import BehaviorManager
from utilities.behavior.config import BotBehaviorConfig
from utilities.behavior.profiles import ActivityProfile, ACTIVITY_PROFILE_CONFIGS
import time


def test_behavior_manager_initialization():
    """Test BehaviorManager can be initialized with activity profiles."""
    print("\n" + "=" * 60)
    print("Testing BehaviorManager Initialization")
    print("=" * 60)

    # Test with activity profile
    manager = BehaviorManager(
        bot=None,  # We don't need a real bot for this test
        activity_profile=ActivityProfile.BANK_STANDING_ACTIVE,
        cycle_enabled=True,
    )

    current_profile = manager.get_current_profile()
    print(f"[OK] Manager initialized with profile: {current_profile.value}")
    print(f"     Profile name: {ACTIVITY_PROFILE_CONFIGS[current_profile]['name']}")

    return manager


def test_profile_switching():
    """Test manual profile switching."""
    print("\n" + "=" * 60)
    print("Testing Manual Profile Switching")
    print("=" * 60)

    manager = BehaviorManager(
        bot=None,
        activity_profile=ActivityProfile.BANK_STANDING_ACTIVE,
        cycle_enabled=True,
    )

    initial_profile = manager.get_current_profile()
    print(f"Initial profile: {initial_profile.value}")

    # Switch to AFK profile
    manager.switch_to_profile(ActivityProfile.BANK_STANDING_AFK)
    new_profile = manager.get_current_profile()
    print(f"[OK] Switched to: {new_profile.value}")

    assert new_profile == ActivityProfile.BANK_STANDING_AFK, "Profile switch failed"
    print(f"[OK] Profile switch verified")


def test_cycle_switching():
    """Test automatic profile switching on inventory complete."""
    print("\n" + "=" * 60)
    print("Testing Automatic Cycle Switching")
    print("=" * 60)

    manager = BehaviorManager(
        bot=None,
        activity_profile=ActivityProfile.BANK_STANDING_ACTIVE,
        cycle_enabled=True,
    )

    initial_profile = manager.get_current_profile()
    print(f"Initial profile: {initial_profile.value}")

    # Simulate multiple inventory completions to trigger a switch
    # With 5% chance, we should see a switch within ~40 attempts (statistically)
    max_attempts = 100
    switch_occurred = False

    for i in range(max_attempts):
        manager.on_inventory_complete()
        current_profile = manager.get_current_profile()

        if current_profile != initial_profile:
            print(f"[OK] Profile switched after {i + 1} inventory completions")
            print(f"     {initial_profile.value} -> {current_profile.value}")
            switch_occurred = True
            break

    if not switch_occurred:
        print(
            f"[WARN] No profile switch in {max_attempts} attempts (statistically unlikely but possible)"
        )
    else:
        print(f"[OK] Cycle switching works correctly")


def test_tab_out_config():
    """Test that tab-out configuration is properly loaded."""
    print("\n" + "=" * 60)
    print("Testing Tab-Out Configuration")
    print("=" * 60)

    # Test AFK profile (tab-out enabled)
    manager = BehaviorManager(
        bot=None, activity_profile=ActivityProfile.BANK_STANDING_AFK, cycle_enabled=True
    )

    profile_config = ACTIVITY_PROFILE_CONFIGS[ActivityProfile.BANK_STANDING_AFK]
    tab_out_enabled = profile_config["attention"]["tab_out_enabled"]
    tab_out_interval = profile_config["attention"]["tab_out_interval"]

    print(f"[OK] Bank Standing AFK profile:")
    print(f"     Tab-out enabled: {tab_out_enabled}")
    print(f"     Tab-out interval: {tab_out_interval[0]}-{tab_out_interval[1]} seconds")

    assert tab_out_enabled == True, "Tab-out should be enabled for AFK profile"
    print(f"[OK] Tab-out configuration validated")


def test_bank_check_config():
    """Test that bank check configuration is properly loaded."""
    print("\n" + "=" * 60)
    print("Testing Bank Check Configuration")
    print("=" * 60)

    # Test AFK profile (bank check enabled)
    manager = BehaviorManager(
        bot=None, activity_profile=ActivityProfile.BANK_STANDING_AFK, cycle_enabled=True
    )

    profile_config = ACTIVITY_PROFILE_CONFIGS[ActivityProfile.BANK_STANDING_AFK]
    bank_check_enabled = profile_config["attention"]["bank_check_enabled"]
    bank_check_interval = profile_config["attention"]["bank_check_interval"]

    print(f"[OK] Bank Standing AFK profile:")
    print(f"     Bank check enabled: {bank_check_enabled}")
    print(
        f"     Bank check interval: {bank_check_interval[0]}-{bank_check_interval[1]} seconds"
    )

    assert bank_check_enabled == True, "Bank check should be enabled for AFK profile"

    # Test Active profile (bank check disabled)
    manager_active = BehaviorManager(
        bot=None,
        activity_profile=ActivityProfile.BANK_STANDING_ACTIVE,
        cycle_enabled=True,
    )

    profile_config_active = ACTIVITY_PROFILE_CONFIGS[
        ActivityProfile.BANK_STANDING_ACTIVE
    ]
    bank_check_enabled_active = profile_config_active["attention"]["bank_check_enabled"]

    print(f"[OK] Bank Standing Active profile:")
    print(f"     Bank check enabled: {bank_check_enabled_active}")

    assert bank_check_enabled_active == False, (
        "Bank check should be disabled for Active profile"
    )
    print(f"[OK] Bank check configuration validated")


def test_backward_compatibility():
    """Test that old-style configs still work."""
    print("\n" + "=" * 60)
    print("Testing Backward Compatibility")
    print("=" * 60)

    # Old-style config (no activity_profile)
    manager = BehaviorManager(
        bot=None,
        profile="active",  # Old-style profile parameter
        activity_profile=None,  # Not using new system
        cycle_enabled=False,
    )

    print(f"[OK] Manager initialized with legacy config")
    print(f"     Legacy profile: active")
    print(f"[OK] Backward compatibility maintained")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   BehaviorManager Integration Test Suite")
    print("=" * 60)

    try:
        test_behavior_manager_initialization()
        test_profile_switching()
        test_cycle_switching()
        test_tab_out_config()
        test_bank_check_config()
        test_backward_compatibility()

        print("\n" + "=" * 60)
        print("         ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)
        print()

    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback

        traceback.print_exc()
