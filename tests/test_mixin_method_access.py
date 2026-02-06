"""
Test to verify mixins have access to required methods through MRO.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

print("=" * 60)
print("Testing Mixin Method Access Through MRO")
print("=" * 60)

try:
    from model.osrs.cooking import OSRSCooking

    # Create a bot instance (don't run it)
    bot = OSRSCooking()

    # Test 1: Check if mixins are in MRO
    print("\nTest 1: Verify MRO includes all mixins and parent classes")
    mro_classes = [cls.__name__ for cls in OSRSCooking.__mro__]
    print(f"MRO: {' -> '.join(mro_classes[:8])}")  # First 8 classes

    required_classes = [
        "OSRSCooking",
        "TemplateMixin",
        "BankingMixin",
        "ItemInteractionMixin",
        "ActionWaitingMixin",
        "RuneLiteBot",
        "Bot",
    ]

    for cls_name in required_classes:
        if cls_name in mro_classes:
            print(f"  ✓ {cls_name} in MRO")
        else:
            print(f"  ✗ {cls_name} NOT in MRO")
            sys.exit(1)

    # Test 2: Check if mixin-required methods are accessible
    print("\nTest 2: Verify mixin-required methods are accessible")

    required_methods = {
        "BankingMixin": [
            "log_msg",
            "get_nearest_tag",
            "mouseover_text",
            "_safe_key_press",
            "_safe_key_down",
            "_safe_key_up",
        ],
        "ItemInteractionMixin": ["log_msg", "_safe_key_press"],
        "ActionWaitingMixin": ["log_msg"],
        "TemplateMixin": ["log_msg"],
    }

    for mixin_name, methods in required_methods.items():
        print(f"\n  {mixin_name} requires:")
        for method in methods:
            if hasattr(bot, method):
                print(f"    ✓ {method}() accessible")
            else:
                print(f"    ✗ {method}() NOT accessible - BROKEN!")
                sys.exit(1)

    # Test 3: Check if bot has required attributes
    print("\nTest 3: Verify required attributes exist")
    required_attrs = ["behavior", "win", "status", "options"]

    for attr in required_attrs:
        if hasattr(bot, attr):
            print(f"  ✓ self.{attr} exists")
        else:
            print(f"  ✗ self.{attr} NOT exists - BROKEN!")
            sys.exit(1)

    # Test 4: Check if mixin methods are callable
    print("\nTest 4: Verify mixin methods are callable")
    mixin_methods = [
        "get_template_path",  # TemplateMixin
        "open_bank",  # BankingMixin
        "is_bank_open",  # BankingMixin
        "click_inventory_slot",  # ItemInteractionMixin
        "use_item_on_item",  # ItemInteractionMixin
        "wait_for_action_start",  # ActionWaitingMixin
    ]

    for method in mixin_methods:
        if hasattr(bot, method) and callable(getattr(bot, method)):
            print(f"  ✓ {method}() is callable")
        else:
            print(f"  ✗ {method}() NOT callable - BROKEN!")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("ALL MIXIN ACCESS TESTS PASSED")
    print("=" * 60)
    print("\nMixins can successfully access parent class methods through MRO!")
    print("The mixin system is working correctly.\n")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
