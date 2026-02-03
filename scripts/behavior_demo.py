"""
Demonstration script for the behavior system.

This script demonstrates all features of the behavior system without
requiring a full bot setup.

Run with: python -m scripts.behavior_demo
"""

import time
from unittest.mock import Mock


# Mock bot for demonstration
class MockBot:
    """Mock bot for testing behavior system."""

    def __init__(self):
        self.mouse = Mock()
        self.win = Mock()
        self.win.game_view = Mock()
        self.win.game_view.random_point = Mock(return_value=(100, 100))
        self.win.cp_tabs = [Mock() for _ in range(11)]
        self.win.inventory_slots = [Mock() for _ in range(28)]
        self.move_camera = Mock()

    def log_msg(self, msg, overwrite=False):
        """Print log messages."""
        print(f"[BOT] {msg}")


def demo_timing_behavior(bot):
    """Demonstrate timing behavior module."""
    print("\n" + "=" * 70)
    print("TIMING BEHAVIOR DEMONSTRATION")
    print("=" * 70)

    from utilities.behavior import BehaviorManager

    manager = BehaviorManager(bot, profile="experienced")

    print("\n1. Testing preset sleep durations:")
    for preset in ["instant", "very_fast", "fast", "short"]:
        print(f"   - {preset}...", end=" ", flush=True)
        start = time.time()
        manager.timing.sleep(preset)
        elapsed = time.time() - start
        print(f"took {elapsed:.3f}s")

    print("\n2. Testing custom range:")
    print("   - Custom (0.1, 0.2)...", end=" ", flush=True)
    start = time.time()
    manager.timing.sleep((0.1, 0.2))
    elapsed = time.time() - start
    print(f"took {elapsed:.3f}s")

    print("\n3. Testing fixed duration:")
    print("   - Fixed 0.1s...", end=" ", flush=True)
    start = time.time()
    manager.timing.sleep(0.1)
    elapsed = time.time() - start
    print(f"took {elapsed:.3f}s")

    print("\n4. Testing speed multiplier (2x slower):")
    manager.update_speed_multiplier(2.0)
    print("   - 'fast' preset with 2x multiplier...", end=" ", flush=True)
    start = time.time()
    manager.timing.sleep("fast")
    elapsed = time.time() - start
    print(f"took {elapsed:.3f}s (should be ~2x normal)")

    print("\n5. Testing reaction delay:")
    print("   - Reaction delay...", end=" ", flush=True)
    start = time.time()
    manager.timing.reaction_delay()
    elapsed = time.time() - start
    print(f"took {elapsed:.3f}s")


def demo_mouse_behavior(bot):
    """Demonstrate mouse behavior module."""
    print("\n" + "=" * 70)
    print("MOUSE BEHAVIOR DEMONSTRATION")
    print("=" * 70)

    from utilities.behavior import BehaviorManager
    from utilities.geometry import Point

    manager = BehaviorManager(bot, profile="experienced")

    print("\n1. Testing move_to with Point:")
    target = Point(100, 200)
    manager.mouse.move_to(target)
    print(f"   [OK] Moved to {target}")

    print("\n2. Testing move_to with tuple:")
    manager.mouse.move_to((150, 250))
    print("   [OK] Moved to (150, 250)")

    print("\n3. Testing move_to with speed override:")
    manager.mouse.move_to(target, mouseSpeed="slow")
    print("   [OK] Moved with slow speed")

    print("\n4. Testing click:")
    manager.mouse.click()
    print("   [OK] Clicked")

    print("\n5. Testing right click:")
    manager.mouse.right_click()
    print("   [OK] Right clicked")


def demo_action_behavior(bot):
    """Demonstrate action behavior module."""
    print("\n" + "=" * 70)
    print("ACTION BEHAVIOR DEMONSTRATION")
    print("=" * 70)

    from utilities.behavior import BehaviorManager
    from utilities.geometry import Point

    # High probability for demo
    manager = BehaviorManager(
        bot,
        profile="experienced",
        custom_config={
            "action": {
                "misclick_chance": 1.0,  # Always misclick for demo
                "hesitation_chance": 1.0,  # Always hesitate for demo
            }
        },
    )

    # Need to set behavior on bot for cross-module calls
    bot.behavior = manager

    print("\n1. Testing misclick probability:")
    should_misclick = manager.action.should_misclick()
    print(f"   Should misclick: {should_misclick} (chance: 100%)")

    print("\n2. Testing hesitation probability:")
    should_hesitate = manager.action.should_hesitate()
    print(f"   Should hesitate: {should_hesitate} (chance: 100%)")

    print("\n3. Testing hesitate execution:")
    print("   Hesitating...", end=" ", flush=True)
    start = time.time()
    manager.action.hesitate()
    elapsed = time.time() - start
    print(f"took {elapsed:.3f}s")

    print("\n4. Testing pre-click delay:")
    print("   Pre-click delay...", end=" ", flush=True)
    start = time.time()
    manager.action.pre_click_delay()
    elapsed = time.time() - start
    print(f"took {elapsed:.3f}s")

    print("\n4. Testing pre-click delay:")
    print("   Pre-click delay...", end=" ", flush=True)
    start = time.time()
    manager.action.pre_click_delay()
    elapsed = time.time() - start
    print(f"took {elapsed:.3f}s")


def demo_attention_behavior(bot):
    """Demonstrate attention behavior module."""
    print("\n" + "=" * 70)
    print("ATTENTION BEHAVIOR DEMONSTRATION")
    print("=" * 70)

    from utilities.behavior import BehaviorManager

    manager = BehaviorManager(bot, profile="experienced")
    bot.behavior = manager  # Set for cross-module calls

    print("\n1. Testing random camera movement:")
    manager.attention.random_camera_movement()
    if bot.move_camera.called:
        print("   [OK] Camera moved")

    print("\n2. Testing mini camera adjust:")
    manager.attention.mini_camera_adjust()
    print("   [OK] Mini camera adjust performed")

    print("\n3. Testing camera disable:")
    manager.configure(camera_enabled=False)
    bot.move_camera.reset_mock()
    manager.attention.random_camera_movement()
    if not bot.move_camera.called:
        print("   [OK] Camera movement correctly disabled")

    print("\n4. Re-enabling camera:")
    manager.configure(camera_enabled=True)
    print("   [OK] Camera re-enabled")


def demo_break_behavior(bot):
    """Demonstrate break behavior module."""
    print("\n" + "=" * 70)
    print("BREAK BEHAVIOR DEMONSTRATION")
    print("=" * 70)

    from utilities.behavior import BehaviorManager

    # Disabled by default
    manager = BehaviorManager(bot, profile="experienced")

    print("\n1. Testing should_take_break (disabled):")
    should_break = manager.breaks.should_take_break()
    print(f"   Should take break: {should_break} (breaks disabled)")

    print("\n2. Enabling breaks:")
    manager.configure(breaks_enabled=True)
    manager.breaks.update_config(chance_per_check=1.0)  # 100% for demo
    should_break = manager.breaks.should_take_break()
    print(f"   Should take break: {should_break} (chance: 100%)")

    print("\n3. Testing short break (1s for demo):")
    import time
    from unittest.mock import patch

    # Patch time.sleep for quick demo
    with patch("time.sleep"):
        manager.breaks.update_config(duration_min=1.0, duration_max=1.0)
        duration = manager.breaks.take_break()
        print(f"   ✓ Break taken (would have been {duration:.1f}s)")


def demo_profiles(bot):
    """Demonstrate different behavior profiles."""
    print("\n" + "=" * 70)
    print("BEHAVIOR PROFILES DEMONSTRATION")
    print("=" * 70)

    from utilities.behavior import BehaviorManager, BehaviorProfiles

    print("\n1. Available profiles:")
    for profile_name in BehaviorProfiles.list_profiles():
        desc = BehaviorProfiles.get_profile_description(profile_name)
        print(f"   - {profile_name.capitalize()}: {desc}")

    print("\n2. Profile comparison (timing with 'short' preset):")
    for profile_name in ["cautious", "experienced", "focused"]:
        manager = BehaviorManager(bot, profile=profile_name)

        print(f"\n   {profile_name.capitalize()} profile:")
        print(f"   - Speed multiplier: {manager.timing.config['speed_multiplier']}x")
        print(f"   - Misclick chance: {manager.action.config['misclick_chance']:.1%}")

        print(f"   - Testing 'short' sleep...", end=" ", flush=True)
        start = time.time()
        manager.timing.sleep("short")
        elapsed = time.time() - start
        print(f"took {elapsed:.3f}s")


def demo_manager(bot):
    """Demonstrate behavior manager features."""
    print("\n" + "=" * 70)
    print("BEHAVIOR MANAGER DEMONSTRATION")
    print("=" * 70)

    from utilities.behavior import BehaviorManager

    print("\n1. Creating manager with custom config:")
    manager = BehaviorManager(
        bot,
        profile="experienced",
        custom_config={
            "timing": {"speed_multiplier": 1.5},
            "attention": {"camera_enabled": False},
        },
    )
    print("   [OK] Manager created")

    print("\n2. Checking configuration:")
    print(f"   - Speed multiplier: {manager.timing.config['speed_multiplier']}x")
    print(f"   - Camera enabled: {manager.attention.config['camera_enabled']}")

    print("\n3. Runtime configuration:")
    manager.configure(camera_enabled=True, breaks_enabled=True)
    print(f"   - Camera enabled: {manager.attention.config['camera_enabled']}")
    print(f"   - Breaks enabled: {manager.breaks.enabled}")

    print("\n4. Disable all modules:")
    manager.disable_all()
    print(f"   - Timing enabled: {manager.timing.enabled}")
    print(f"   - Mouse enabled: {manager.mouse.enabled}")

    print("\n5. Enable all modules:")
    manager.enable_all()
    print(f"   - Timing enabled: {manager.timing.enabled}")
    print(f"   - Mouse enabled: {manager.mouse.enabled}")

    print("\n6. Configuration summary:")
    print(manager.summary())


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("BEHAVIOR SYSTEM DEMONSTRATION")
    print("=" * 70)
    print("\nThis script demonstrates all features of the behavior system.")
    print("Each module will be tested independently.\n")

    # Create mock bot
    bot = MockBot()

    # Run demonstrations
    try:
        demo_timing_behavior(bot)
        demo_mouse_behavior(bot)
        demo_action_behavior(bot)
        demo_attention_behavior(bot)
        demo_break_behavior(bot)
        demo_profiles(bot)
        demo_manager(bot)

        print("\n" + "=" * 70)
        print("ALL DEMONSTRATIONS COMPLETE!")
        print("=" * 70)
        print("\nThe behavior system is ready to use in your bots.")
        print("See README.md for full documentation.")

    except Exception as e:
        print(f"\n[ERROR] Error during demonstration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
