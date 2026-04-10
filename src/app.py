import sys
import threading
import keyboard
import pystray
from src.config import GROQ_API_KEY, HOTKEY, APP_NAME
from src.ui import JarvisWindow, make_icon

def main():
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set.")
        sys.exit(1)

    win = JarvisWindow()
    keyboard.add_hotkey(HOTKEY, lambda: win.root.after(0, win.toggle), suppress=False)
    print(f"Jarvis online. {HOTKEY} to summon.")

    def on_show(icon, item): win.root.after(0, win.show)
    def on_quit(icon, item): icon.stop(); win.root.after(0, win.root.destroy)

    icon = pystray.Icon(APP_NAME, make_icon(), APP_NAME,
        menu=pystray.Menu(
            pystray.MenuItem("Show / Hide", on_show),
            pystray.MenuItem("Quit", on_quit),
        ))
    threading.Thread(target=icon.run, daemon=True).start()
    win.run()
