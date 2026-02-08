#!/usr/bin/env python3
"""
Quick test to reproduce the trace trap issue
"""
import threading
import time
import sys

class TestThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
    
    def run(self):
        print("Thread started")
        while self.running:
            time.sleep(0.1)
        print("Thread stopped")
    
    def stop(self):
        self.running = False

def main():
    print(f"Python version: {sys.version}")
    print(f"PYTHONSTARTUP: {sys.base_prefix}")
    
    # Check for VS Code debugger
    if hasattr(sys, 'excepthook'):
        hook_str = str(sys.excepthook)
        if 'REPL' in hook_str or 'vscode' in hook_str.lower():
            print("⚠️  WARNING: VS Code debugging hooks detected!")
            print(f"   excepthook: {hook_str}")
        else:
            print("✓ No VS Code hooks detected")
    
    print("\nStarting thread test...")
    thread = TestThread()
    thread.daemon = True
    thread.start()
    
    time.sleep(1)
    print("Stopping thread...")
    thread.stop()
    thread.join(timeout=2)
    
    print("✓ Test completed successfully - no trace trap!")

if __name__ == "__main__":
    main()
