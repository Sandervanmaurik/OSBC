import sys
import signal
import importlib
import threading
import time

def sigtrap_handler(signum, frame):
    import traceback
    print(f"\n!!! SIGTRAP #{signum} CAUGHT !!!")
    traceback.print_stack(frame)
    import os
    os._exit(1)

signal.signal(signal.SIGTRAP, sigtrap_handler)

sys.path.insert(0, 'src')

from OSBC import App

app = App(test=False)

def test_reload():
    time.sleep(1)
    print("\n=== Testing reload inside Tkinter event loop ===")
    
    try:
        from model.osrs.cooking import OSRSCooking
        bot = OSRSCooking()
        
        module_name = bot.__class__.__module__
        module = sys.modules[module_name]
        
        print(f"Reloading {module_name}...")
        importlib.reload(module)
        print("✓ Reload successful inside Tkinter!")
        
    except Exception as e:
        print(f"✗ Reload failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        time.sleep(1)
        print("Closing app...")
        app.quit()

thread = threading.Thread(target=test_reload, daemon=True)
thread.start()

print("Starting Tkinter mainloop...")
app.start()
print("Mainloop exited")
