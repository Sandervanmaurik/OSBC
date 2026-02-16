"""Test enhanced logging for behavior profiles."""

from utilities.behavior.manager import BehaviorManager
from utilities.behavior.profiles import ActivityProfile


class FakeBot:
    """Minimal fake bot with logging."""

    def __init__(self):
        self.logs = []

    def log_msg(self, msg):
        """Capture log messages."""
        self.logs.append(msg)
        print(msg)


def test_initialization_logging():
    """Test that initialization logs profile details."""
    print("\n" + "=" * 60)
    print("Testing Initialization Logging")
    print("=" * 60)

    bot = FakeBot()

    manager = BehaviorManager(
        bot=bot,
        activity_profile=ActivityProfile.BANK_STANDING_ACTIVE,
        cycle_enabled=True,
    )

    # Check that logs were created
    assert len(bot.logs) > 0, "No logs created"

    # Check for key info in logs
    log_text = " ".join(bot.logs)
    assert "BEHAVIOR" in log_text and "PROFILE INITIALIZED" in log_text
    assert "Bank Standing Active" in log_text
    assert "ENABLED" in log_text  # Cycling enabled

    print(f"\n[OK] Initialization logged {len(bot.logs)} messages")
    return True


def test_profile_switch_logging():
    """Test that profile switches are logged."""
    print("\n" + "=" * 60)
    print("Testing Profile Switch Logging")
    print("=" * 60)

    bot = FakeBot()

    manager = BehaviorManager(
        bot=bot,
        activity_profile=ActivityProfile.BANK_STANDING_ACTIVE,
        cycle_enabled=True,
    )

    # Clear initialization logs
    bot.logs = []

    # Manually switch profile
    manager.switch_to_profile(ActivityProfile.BANK_STANDING_AFK)

    # Check logs
    assert len(bot.logs) > 0, "No switch logs created"

    log_text = " ".join(bot.logs)
    assert "PROFILE SWITCHED" in log_text
    assert "bank_standing_afk" in log_text

    print(f"\n[OK] Profile switch logged {len(bot.logs)} messages")
    return True


def test_inventory_complete_logging():
    """Test that inventory completion is logged."""
    print("\n" + "=" * 60)
    print("Testing Inventory Complete Logging")
    print("=" * 60)

    bot = FakeBot()

    manager = BehaviorManager(
        bot=bot,
        activity_profile=ActivityProfile.BANK_STANDING_ACTIVE,
        cycle_enabled=True,
    )

    # Clear initialization logs
    bot.logs = []

    # Call inventory complete
    manager.on_inventory_complete()

    # Check logs
    assert len(bot.logs) > 0, "No inventory logs created"

    log_text = " ".join(bot.logs)
    assert "Inventory #1 complete" in log_text

    print(f"\n[OK] Inventory complete logged {len(bot.logs)} messages")

    # Try a few more times to potentially trigger a switch
    bot.logs = []
    for i in range(10):
        manager.on_inventory_complete()

    log_text = " ".join(bot.logs)
    if "PROFILE SWITCHED" in log_text:
        print(f"[OK] Profile switch occurred and was logged!")
    else:
        print(f"[OK] No switch in 10 tries (normal, 5% chance)")

    return True


def test_profile_status_logging():
    """Test that profile status can be logged on demand."""
    print("\n" + "=" * 60)
    print("Testing Profile Status Logging")
    print("=" * 60)

    bot = FakeBot()

    manager = BehaviorManager(
        bot=bot, activity_profile=ActivityProfile.SKILLING_AFK, cycle_enabled=True
    )

    # Clear initialization logs
    bot.logs = []

    # Log status
    manager.log_profile_status()

    # Check logs
    assert len(bot.logs) > 0, "No status logs created"

    log_text = " ".join(bot.logs)
    assert "BEHAVIOR" in log_text and "STATUS" in log_text
    assert "Skilling AFK" in log_text

    print(f"\n[OK] Status logged {len(bot.logs)} messages")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   Enhanced Logging Test Suite")
    print("=" * 60)

    try:
        test1 = test_initialization_logging()
        test2 = test_profile_switch_logging()
        test3 = test_inventory_complete_logging()
        test4 = test_profile_status_logging()

        if test1 and test2 and test3 and test4:
            print("\n" + "=" * 60)
            print("         ALL LOGGING TESTS PASSED!")
            print("=" * 60)
            print()
        else:
            print("\n" + "=" * 60)
            print("         SOME TESTS FAILED!")
            print("=" * 60)
    except Exception as e:
        print(f"\n[FAIL] Test crashed: {e}")
        import traceback

        traceback.print_exc()
