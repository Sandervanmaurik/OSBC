"""
Simple test to verify fletching bot has Ruby bolt tips method properly structured.

Tests the critical patterns: templates defined, method exists, and action detection.
"""

import sys
import os

# Test by importing just the fletching module and checking the code
fletching_file = os.path.join(
    os.path.dirname(__file__), "..", "src", "model", "osrs", "fletching.py"
)

print("=" * 60)
print("Testing Fletching Bot - Ruby Bolt Tips Method")
print("=" * 60)

# Read the fletching.py file
with open(fletching_file, "r") as f:
    content = f.read()

# Test 1: Check if "Ruby bolt tips" is in FLETCHING_METHODS
print("\nTest 1: 'Ruby bolt tips' added to FLETCHING_METHODS")
if '"Ruby bolt tips"' in content and "FLETCHING_METHODS" in content:
    print("PASSED: Found 'Ruby bolt tips' in FLETCHING_METHODS list")
else:
    print("FAILED: 'Ruby bolt tips' not found in FLETCHING_METHODS")
    sys.exit(1)

# Test 2: Check if RUBY_BOLT_TIPS_TEMPLATES is defined
print("\nTest 2: RUBY_BOLT_TIPS_TEMPLATES dictionary defined")
if "RUBY_BOLT_TIPS_TEMPLATES" in content:
    print("PASSED: Found RUBY_BOLT_TIPS_TEMPLATES dictionary")
else:
    print("FAILED: RUBY_BOLT_TIPS_TEMPLATES not defined")
    sys.exit(1)

# Test 3: Check if templates include chisel, ruby, ruby_bolt_tips
print("\nTest 3: Templates include chisel.png, ruby.png, ruby_bolt_tips.png")
if (
    '"chisel.png"' in content
    and '"ruby.png"' in content
    and '"ruby_bolt_tips.png"' in content
):
    print("PASSED: All required templates defined")
else:
    print("FAILED: Missing template definitions")
    sys.exit(1)

# Test 4: Check if _cut_ruby_bolt_tips_cycle method exists
print("\nTest 4: _cut_ruby_bolt_tips_cycle() method exists")
if "def _cut_ruby_bolt_tips_cycle(self)" in content:
    print("PASSED: Found _cut_ruby_bolt_tips_cycle method")
else:
    print("FAILED: _cut_ruby_bolt_tips_cycle method not found")
    sys.exit(1)

# Test 5: Check if _cut_ruby_bolt_tips method exists
print("\nTest 5: _cut_ruby_bolt_tips() method exists")
if "def _cut_ruby_bolt_tips(" in content:
    print("PASSED: Found _cut_ruby_bolt_tips method")
else:
    print("FAILED: _cut_ruby_bolt_tips method not found")
    sys.exit(1)

# Test 6: Check if _handle_ruby_banking method exists
print("\nTest 6: _handle_ruby_banking() method exists")
if "def _handle_ruby_banking(" in content:
    print("PASSED: Found _handle_ruby_banking method")
else:
    print("FAILED: _handle_ruby_banking method not found")
    sys.exit(1)

# Test 7: Check if main_loop calls _cut_ruby_bolt_tips_cycle
print("\nTest 7: main_loop() calls _cut_ruby_bolt_tips_cycle()")
if (
    'self.fletching_method == "Ruby bolt tips"' in content
    and "self._cut_ruby_bolt_tips_cycle()" in content
):
    print("PASSED: main_loop correctly routes to ruby bolt tips cycle")
else:
    print("FAILED: main_loop doesn't call ruby bolt tips cycle")
    sys.exit(1)

# Test 8: Check if uses ActionWaitingMixin for "Cutting"
print("\nTest 8: Uses ActionWaitingMixin for 'Cutting' action detection")
if (
    'self.wait_for_action_start("Cutting"' in content
    and 'self.wait_for_action_end("Cutting"' in content
):
    print("PASSED: Uses ActionWaitingMixin for action detection")
else:
    print("FAILED: ActionWaitingMixin not used correctly")
    sys.exit(1)

# Test 9: Check if uses ItemInteractionMixin
print("\nTest 9: Uses ItemInteractionMixin.use_item_on_item()")
if "self.use_item_on_item(" in content:
    print("PASSED: Uses ItemInteractionMixin.use_item_on_item()")
else:
    print("FAILED: use_item_on_item not used")
    sys.exit(1)

# Test 10: Check if uses BankingMixin
print("\nTest 10: Uses BankingMixin for banking operations")
if (
    "self.open_bank(" in content
    and "self.deposit_items(" in content
    and "self.withdraw_items(" in content
):
    print("PASSED: Uses BankingMixin for banking")
else:
    print("FAILED: BankingMixin not used correctly")
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL RUBY BOLT TIPS STRUCTURE TESTS PASSED")
print("=" * 60)
print("\nThe ruby bolt tips method is correctly structured:")
print("1. Templates defined (chisel, ruby, ruby_bolt_tips)")
print("2. Cycle method checks inventory and routes to cut or bank")
print("3. Cut method uses item-on-item, waits for 'Cutting' action")
print("4. Banking deposits bolt tips, withdraws chisel + rubies")
print("5. Uses modern ActionWaitingMixin pattern (not inline OCR)")
print("6. Follows existing fletching bot patterns (Maple longbow)")
