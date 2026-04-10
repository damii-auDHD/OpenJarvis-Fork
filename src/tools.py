import os
import subprocess
import tkinter as tk
import webbrowser
import ctypes
import threading
import time
from datetime import datetime, timedelta

def run_shell(cmd):
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=30
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        if err and not out:
            return f"[stderr] {err}"
        return out or "[done]"
    except subprocess.TimeoutExpired:
        return "[Error: command timed out]"
    except Exception as e:
        return f"[Error: {e}]"

def get_system_info():
    try:
        import psutil
        cpu  = psutil.cpu_percent(interval=0.5)
        ram  = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")
        bat  = psutil.sensors_battery()
        bat_str = f"{bat.percent:.0f}% ({'charging' if bat.power_plugged else 'on battery'})" if bat else "N/A"
        procs = len(psutil.pids())
        return (f"CPU: {cpu}% | RAM: {ram.percent}% used ({ram.available // 1024**2}MB free) | "
                f"Disk C: {disk.percent}% used | Battery: {bat_str} | Processes: {procs}")
    except Exception as e:
        return f"[Error: {e}]"

def read_file(path):
    try:
        with open(os.path.expandvars(os.path.expanduser(path)), "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[Error reading file: {e}]"

def write_file(path, content):
    try:
        full = os.path.expandvars(os.path.expanduser(path))
        parent = os.path.dirname(full)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return f"[Written to {full}]"
    except Exception as e:
        return f"[Error writing file: {e}]"

def get_clipboard():
    try:
        r = tk.Tk(); r.withdraw()
        text = r.clipboard_get()
        r.destroy()
        return text
    except:
        return "[Clipboard empty or unavailable]"

def set_clipboard(text):
    try:
        r = tk.Tk(); r.withdraw()
        r.clipboard_clear(); r.clipboard_append(text)
        r.update(); r.destroy()
        return "[Clipboard updated]"
    except Exception as e:
        return f"[Error: {e}]"

def list_dir(path="."):
    try:
        full = os.path.expandvars(os.path.expanduser(path))
        items = os.listdir(full)
        return "\n".join(items) if items else "[empty]"
    except Exception as e:
        return f"[Error: {e}]"

def open_url(url):
    try:
        webbrowser.open(url)
        return f"[Opened {url}]"
    except Exception as e:
        return f"[Error: {e}]"

def set_volume(level):
    try:
        script = f"""
$obj = New-Object -ComObject WScript.Shell
for ($i = 0; $i -lt 50; $i++) {{ $obj.SendKeys([char]174) }}
$vol = [math]::Round({level} / 2)
for ($i = 0; $i -lt $vol; $i++) {{ $obj.SendKeys([char]175) }}
"""
        run_shell(script)
        return f"[Volume set to approximately {level}%]"
    except Exception as e:
        return f"[Error: {e}]"

def add_reminder(message, seconds):
    def _fire():
        time.sleep(int(seconds))
        ctypes.windll.user32.MessageBoxW(0, message, "⏰ Jarvis Reminder", 0x40)
    threading.Thread(target=_fire, daemon=True).start()
    at = (datetime.now() + timedelta(seconds=int(seconds))).strftime("%H:%M")
    return f"[Reminder set for {at}: {message}]"

def execute_tool(name, params):
    try:
        if name == "run_shell":       return run_shell(params["cmd"])
        if name == "get_system_info": return get_system_info()
        if name == "read_file":       return read_file(params["path"])
        if name == "write_file":      return write_file(params["path"], params["content"])
        if name == "list_dir":        return list_dir(params.get("path", "."))
        if name == "get_clipboard":   return get_clipboard()
        if name == "set_clipboard":   return set_clipboard(params["text"])
        if name == "open_url":        return open_url(params["url"])
        if name == "set_volume":      return set_volume(int(params["level"]))
        if name == "add_reminder":    return add_reminder(params["message"], params["seconds"])
        return f"[Unknown tool: {name}]"
    except KeyError as e:
        return f"[Missing parameter: {e}]"
    except Exception as e:
        return f"[Tool error: {e}]"
