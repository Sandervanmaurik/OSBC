#!/usr/bin/env python3
import sys
import faulthandler
import signal
import traceback

# Enable detailed crash reporting
faulthandler.enable()

def signal_handler(signum, frame):
    print(f"\n!!! SIGNAL CAUGHT: {signum} ({signal.Signals(signum).name}) !!!")
    print(f"Frame: {frame}")
    print("\nTraceback:")
    traceback.print_stack(frame)
    sys.exit(1)

# Catch SIGTRAP
signal.signal(signal.SIGTRAP, signal_handler)

# Add src to path
sys.path.insert(0, 'src')

print("Importing modules...")
from OSBC import App

print("Creating app...")
app = App()

print("Starting app...")
app.start()
