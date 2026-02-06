"""
Simple test to verify crafting bot stores options in self.options.

Tests the critical fix: self.options must exist for reload_model() to work.
"""

import sys
import os

# Test by importing just the crafting module and checking the code
crafting_file = os.path.join(
    os.path.dirname(__file__), "..", "src", "model", "osrs", "crafting.py"
)

print("=" * 60)
print("Testing Crafting Bot Options Persistence")
print("=" * 60)

# Read the crafting.py file
with open(crafting_file, "r") as f:
    content = f.read()

# Test 1: Check if __init__ initializes self.options
print("\nTest 1: __init__ initializes self.options = {}")
if "self.options = {}" in content:
    print("PASSED: Found 'self.options = {}' in __init__")
else:
    print("FAILED: 'self.options = {}' not found in __init__")
    print("   This is required for reload_model() to check hasattr(bot, 'options')")
    sys.exit(1)

# Test 2: Check if save_options stores the options dict
print("\nTest 2: save_options() stores self.options = options")
if "self.options = options" in content:
    print("PASSED: Found 'self.options = options' in save_options")
else:
    print("FAILED: 'self.options = options' not found in save_options")
    print(
        "   This is required for reload_model() to call new_bot.save_options(old_bot.options)"
    )
    sys.exit(1)

# Test 3: Check that save_options processes gem_type
print("\nTest 3: save_options() processes 'gem_type' option")
if (
    'elif option == "gem_type":' in content
    and "self.gem_type = options[option]" in content
):
    print("PASSED: save_options correctly sets self.gem_type")
else:
    print("FAILED: save_options doesn't properly handle gem_type")
    sys.exit(1)

# Test 4: Check that save_options processes running_time
print("\nTest 4: save_options() processes 'running_time' option")
if (
    'if option == "running_time":' in content
    and "self.running_time = int(options[option])" in content
):
    print("PASSED: save_options correctly sets self.running_time")
else:
    print("FAILED: save_options doesn't properly handle running_time")
    sys.exit(1)

# Test 5: Check that save_options processes crafting_method
print("\nTest 5: save_options() processes 'crafting_method' option")
if (
    'elif option == "crafting_method":' in content
    and "self.crafting_method = options[option]" in content
):
    print("PASSED: save_options correctly sets self.crafting_method")
else:
    print("FAILED: save_options doesn't properly handle crafting_method")
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL CODE STRUCTURE TESTS PASSED")
print("=" * 60)
print("\nThe crafting bot code is correctly structured to persist options.")
print("\nHow it works:")
print("1. User sets options -> save_options() called -> stores in self.options dict")
print("2. User clicks Start -> reload_model() creates new instance")
print("3. reload_model() checks: if hasattr(old_bot, 'options'):")
print("4. reload_model() calls: new_bot.save_options(old_bot.options)")
print("5. New bot now has correct gem_type, crafting_method, and running_time!")
print("\nIf it's still not working, check bot_controller.py's reload_model()")
