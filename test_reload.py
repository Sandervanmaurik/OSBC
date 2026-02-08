#!/usr/bin/env python3
"""Test importlib.reload with threading"""
import importlib
import sys
import time

# Create a simple module to reload
test_module_code = '''
import threading
class TestBot:
    def __init__(self):
        self.value = 42
    
    def main_loop(self):
        print("Bot running...")
        time.sleep(1)
        print("Bot done")
'''

# Write module to file
with open('test_bot_module.py', 'w') as f:
    f.write(test_module_code)

# Import module
import test_bot_module

print("Creating instance...")
bot = test_bot_module.TestBot()
print(f"Bot value: {bot.value}")

print("\nReloading module...")
importlib.reload(test_bot_module)

print("Creating new instance from reloaded module...")
NewBotClass = getattr(test_bot_module, 'TestBot')
new_bot = NewBotClass()
print(f"New bot value: {new_bot.value}")

print("\n✓ Reload test passed!")

# Cleanup
import os
os.remove('test_bot_module.py')
if os.path.exists('test_bot_module.pyc'):
    os.remove('test_bot_module.pyc')
