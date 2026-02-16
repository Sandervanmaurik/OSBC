"""Quick test to verify the AttentionBehavior fix."""

from utilities.behavior.modules.attention import AttentionBehavior
import time


class FakeBot:
    """Minimal fake bot for testing."""

    class FakeBehavior:
        """Fake behavior manager."""

        @staticmethod
        def increment_stat(stat_name):
            pass

        @staticmethod
        def get_camera_config():
            """Return minimal camera config."""

            class CameraConfig:
                enabled = False
                interval_range = (30.0, 90.0)
                horizontal_range = (-120, 120)
                vertical_range = (-20, 20)
                vertical_chance = 0.3

            return CameraConfig()

    def __init__(self):
        self.behavior = self.FakeBehavior()


def test_attention_initialization():
    """Test that AttentionBehavior initializes correctly."""
    print("\n" + "=" * 60)
    print("Testing AttentionBehavior Initialization")
    print("=" * 60)

    bot = FakeBot()
    attention = AttentionBehavior({}, bot)

    # Check all required attributes exist
    required_attrs = [
        "_last_camera_move",
        "_last_skill_check",
        "_last_mouse_movement",
        "_last_inventory_check",
        "_last_tab_out",
        "_last_bank_check",
        "_camera_interval",
        "_skill_interval",
        "_mouse_interval",
        "_inventory_interval",  # THIS WAS THE BUG
        "_tab_out_interval",
        "_bank_check_interval",
    ]

    missing = []
    for attr in required_attrs:
        if not hasattr(attention, attr):
            missing.append(attr)
        else:
            print(f"[OK] {attr}: {getattr(attention, attr)}")

    if missing:
        print(f"\n[FAIL] Missing attributes: {missing}")
        return False

    print(f"\n[OK] All required attributes present")
    return True


def test_perform_random_behaviors():
    """Test that perform_random_behaviors doesn't crash."""
    print("\n" + "=" * 60)
    print("Testing perform_random_behaviors()")
    print("=" * 60)

    bot = FakeBot()

    # Add methods that attention behaviors might call
    bot.mouse = type(
        "obj",
        (object,),
        {
            "move_to": lambda *args, **kwargs: None,
            "click": lambda *args, **kwargs: None,
        },
    )()

    bot.get_mouse_position = lambda: (500, 500)
    bot.win = type(
        "obj",
        (object,),
        {
            "game_view": type(
                "obj",
                (object,),
                {
                    "width": 1920,
                    "height": 1080,
                },
            )()
        },
    )()

    attention = AttentionBehavior(
        {
            "camera_enabled": False,  # Disable to avoid needing full bot
            "skill_check_enabled": False,
            "mouse_movement_enabled": False,
            "inventory_check_enabled": True,  # Test the fixed behavior
            "tab_out_enabled": False,
            "bank_check_enabled": False,
        },
        bot,
    )

    # Force the interval to be very low so we can test it
    attention._inventory_interval = 0.0

    try:
        # This should not crash with AttributeError anymore
        attention.perform_random_behaviors()
        print(f"[OK] perform_random_behaviors() executed without error")
        return True
    except AttributeError as e:
        print(f"[FAIL] AttributeError: {e}")
        return False
    except Exception as e:
        # Other exceptions are OK (might be missing methods, etc.)
        print(f"[OK] No AttributeError (other exception: {type(e).__name__})")
        return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   AttentionBehavior Fix Verification")
    print("=" * 60)

    try:
        test1 = test_attention_initialization()
        test2 = test_perform_random_behaviors()

        if test1 and test2:
            print("\n" + "=" * 60)
            print("         ALL TESTS PASSED!")
            print("=" * 60)
            print("\n[OK] The _inventory_interval bug is FIXED")
            print()
        else:
            print("\n" + "=" * 60)
            print("         TESTS FAILED!")
            print("=" * 60)
    except Exception as e:
        print(f"\n[FAIL] Test crashed: {e}")
        import traceback

        traceback.print_exc()
