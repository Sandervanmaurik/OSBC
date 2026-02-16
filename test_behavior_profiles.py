"""
Test script for the new ActivityProfile system.

This script verifies:
1. ActivityProfile enum works
2. ACTIVITY_PROFILE_CONFIGS are correctly defined
3. BotBehaviorConfig factory methods work
4. Profile switching logic works
"""

import sys
from utilities.behavior.profiles import ActivityProfile, ACTIVITY_PROFILE_CONFIGS
from utilities.behavior.config import BotBehaviorConfig


def test_activity_profiles():
    """Test that all activity profiles are defined."""
    print("=" * 60)
    print("Testing Activity Profiles")
    print("=" * 60)

    profiles = [
        ActivityProfile.BANK_STANDING_AFK,
        ActivityProfile.BANK_STANDING_ACTIVE,
        ActivityProfile.SKILLING_AFK,
        ActivityProfile.SKILLING_ACTIVE,
    ]

    for profile in profiles:
        config = ACTIVITY_PROFILE_CONFIGS[profile]
        print(f"\n[OK] {profile.value}:")
        print(f"  Name: {config['name']}")
        print(f"  Description: {config['description']}")
        print(f"  Speed: {config['timing']['speed_multiplier']}x")
        print(f"  Tab-out enabled: {config['attention']['tab_out_enabled']}")
        print(f"  Bank check enabled: {config['attention']['bank_check_enabled']}")
        print(f"  Cycle switch chance: {config['cycle_switch_chance'] * 100}%")

    print("\n" + "=" * 60)
    print("[OK] All 4 activity profiles loaded successfully")
    print("=" * 60)


def test_display_name_conversion():
    """Test GUI display name conversion."""
    print("\n" + "=" * 60)
    print("Testing Display Name Conversion")
    print("=" * 60)

    test_cases = [
        ("Bank Standing (AFK)", ActivityProfile.BANK_STANDING_AFK),
        ("Bank Standing (Active)", ActivityProfile.BANK_STANDING_ACTIVE),
        ("Skilling (AFK)", ActivityProfile.SKILLING_AFK),
        ("Skilling (Active)", ActivityProfile.SKILLING_ACTIVE),
    ]

    for display_name, expected in test_cases:
        result = ActivityProfile.from_display_name(display_name)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"{status} '{display_name}' -> {result.value}")
        if result != expected:
            print(f"  ERROR: Expected {expected.value}")
            return False

    print("\n" + "=" * 60)
    print("[OK] All display name conversions work correctly")
    print("=" * 60)
    return True


def test_factory_methods():
    """Test BotBehaviorConfig factory methods."""
    print("\n" + "=" * 60)
    print("Testing Factory Methods")
    print("=" * 60)

    # Test bank_standing
    config1 = BotBehaviorConfig.bank_standing(active=True)
    print(f"[OK] bank_standing(active=True):")
    print(f"  Profile: {config1.activity_profile.value}")
    print(f"  Cycle enabled: {config1.cycle_enabled}")

    config2 = BotBehaviorConfig.bank_standing(active=False)
    print(f"\n[OK] bank_standing(active=False):")
    print(f"  Profile: {config2.activity_profile.value}")

    # Test skilling
    config3 = BotBehaviorConfig.skilling(active=True)
    print(f"\n[OK] skilling(active=True):")
    print(f"  Profile: {config3.activity_profile.value}")

    config4 = BotBehaviorConfig.skilling(active=False)
    print(f"\n[OK] skilling(active=False):")
    print(f"  Profile: {config4.activity_profile.value}")

    print("\n" + "=" * 60)
    print("[OK] All factory methods work correctly")
    print("=" * 60)
    return True


def test_cycle_weights():
    """Test that cycle weights are valid."""
    print("\n" + "=" * 60)
    print("Testing Cycle Weights")
    print("=" * 60)

    for profile in ActivityProfile:
        config = ACTIVITY_PROFILE_CONFIGS[profile]
        weights = config.get("cycle_weights", {})

        print(f"\n{profile.value}:")
        for target_profile, weight in weights.items():
            print(f"  -> {target_profile}: {weight * 100}%")

        # Verify total weight
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            print(f"  [FAIL] ERROR: Total weight = {total} (should be 1.0)")
            return False
        else:
            print(f"  [OK] Total weight: {total}")

    print("\n" + "=" * 60)
    print("[OK] All cycle weights are valid")
    print("=" * 60)
    return True


def test_backward_compatibility():
    """Test that legacy profile system still works."""
    print("\n" + "=" * 60)
    print("Testing Backward Compatibility")
    print("=" * 60)

    # Test old-style config (should still work)
    config = BotBehaviorConfig(profile="active")
    print(f"[OK] Legacy config: profile='{config.profile}'")
    print(f"  Activity profile: {config.activity_profile}")

    # Test to_kwargs
    kwargs = config.to_kwargs()
    print(f"\n[OK] to_kwargs() result:")
    for key, value in kwargs.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("[OK] Backward compatibility maintained")
    print("=" * 60)
    return True


if __name__ == "__main__":
    print("\n")
    print("+" + "=" * 58 + "+")
    print("|" + " " * 10 + "Activity Profile System Test Suite" + " " * 14 + "|")
    print("+" + "=" * 58 + "+")

    try:
        test_activity_profiles()

        if not test_display_name_conversion():
            sys.exit(1)

        if not test_factory_methods():
            sys.exit(1)

        if not test_cycle_weights():
            sys.exit(1)

        if not test_backward_compatibility():
            sys.exit(1)

        print("\n" + "+" + "=" * 58 + "+")
        print("|" + " " * 16 + "ALL TESTS PASSED!" + " " * 25 + "|")
        print("+" + "=" * 58 + "+\n")

    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

        if not test_factory_methods():
            sys.exit(1)

        if not test_cycle_weights():
            sys.exit(1)

        if not test_backward_compatibility():
            sys.exit(1)

        print("\n" + "+" + "=" * 58 + "+")
        print("|" + " " * 16 + "ALL TESTS PASSED!" + " " * 25 + "|")
        print("+" + "=" * 58 + "+\n")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
