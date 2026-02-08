import sys
import signal
import threading
import time

def sigtrap_handler(signum, frame):
    import traceback
    print(f"\n!!! SIGTRAP #{signum} CAUGHT !!!")
    print("Stack trace:")
    traceback.print_stack(frame)
    import os
    os._exit(1)

signal.signal(signal.SIGTRAP, sigtrap_handler)

sys.path.insert(0, 'src')

from OSBC import App

print("Creating app...")
app = App(test=False)

print("Starting mainloop in 3 seconds...")
print("(App will auto-close after 2 seconds)")

def close_app():
    time.sleep(2)
    print("\nClosing app...")
    app.quit()
    app.destroy()

# Start a thread to close the app after 2 seconds
closer = threading.Thread(target=close_app, daemon=True)
closer.start()

print("Calling app.start()...")
try:
    app.start()
    print("App.start() returned normally")
except KeyboardInterrupt:
    print("Interrupted")
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
