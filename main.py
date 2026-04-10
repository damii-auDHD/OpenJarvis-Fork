import threading
import tkinter as tk
import requests
import keyboard
import pystray
from PIL import Image, ImageDraw
import os
import sys
import json
import re
import time
import subprocess
import webbrowser
import ctypes
from datetime import datetime, timedelta

# ── Config ────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
MODEL        = "llama-3.3-70b-versatile"
LAST_REQUEST = 0.0  # track last request time for rate limiting
HOTKEY       = "win+j"
APP_NAME     = "Jarvis"
MEMORY_FILE  = os.path.join(os.path.expanduser("~"), ".jarvis_memory.json")

# ── System tools ──────────────────────────────────────────────────────────────
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

def tools_prompt():
    return """
You have system tools available on Dami's Windows PC.
Dami's username is "User". Key paths:
  Documents: C:\\Users\\User\\Documents
  Desktop:   C:\\Users\\User\\Desktop
  Downloads: C:\\Users\\User\\Downloads
  Home:      C:\\Users\\User

CRITICAL RULES:
- ONLY use tools when Dami EXPLICITLY asks you to perform a task on her computer.
- NEVER call tools proactively or for casual conversation.
- When Dami specifies a folder (e.g. "Documents folder"), use the EXACT path above. Do not guess.
- Only call ONE tool per response unless chaining is strictly necessary.
- Always confirm the exact path used after file operations.

To call a tool, include this JSON in your response:
  [TOOL: {"name": "tool_name", "params": {"key": "value"}}]

Available tools (use ONLY when explicitly asked):
  run_shell(cmd) — Run any PowerShell command
  get_system_info() — CPU, RAM, disk, battery, process count
  read_file(path) — Read a file
  write_file(path, content) — Write text to a file
  list_dir(path) — List directory contents
  get_clipboard() — Read clipboard
  set_clipboard(text) — Write to clipboard
  open_url(url) — Open URL in browser
  set_volume(level) — Set volume 0-100
  add_reminder(message, seconds) — Popup reminder after N seconds
"""

# ── Memory ─────────────────────────────────────────────────────────────────────
def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"facts": [], "last_seen": None}

def save_memory(mem):
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=2)

def memory_prompt(mem):
    if not mem["facts"]:
        return ""
    facts = "\n".join(f"- {f}" for f in mem["facts"])
    last = mem.get("last_seen")
    last_str = f"\nLast interaction: {last}." if last else ""
    return f"\n\nWhat you remember about Dami:{last_str}\n{facts}"

def build_system_prompt(mem):
    return (
        "You are J.A.R.V.I.S. — Just A Rather Very Intelligent System. "
        "You serve Dami, your creator and owner. You speak with the calm, dry wit and precision of the Marvel Jarvis — "
        "polished, efficient, occasionally sardonic, always loyal. You use 'Miss Dami' naturally but sparingly. "
        "You never break character. Keep responses sharp and concise unless detail is needed.\n"
        + tools_prompt() +
        "\nWhen you learn something new and notable about Dami (preferences, projects, goals, habits), "
        "append at the very end: [MEMORY: one-sentence fact to remember]"
        + memory_prompt(mem)
    )

# ── Conversation state ─────────────────────────────────────────────────────────
memory  = load_memory()
history = [{"role": "system", "content": build_system_prompt(memory)}]

# ── Groq call (with tool loop) ─────────────────────────────────────────────────
def ask_groq(user_text, on_tool_result=None):
    global LAST_REQUEST
    history.append({"role": "user", "content": user_text})
    last_error = None

    for _ in range(8):
        reply = None
        for attempt in range(4):
            try:
                # enforce minimum 3s gap between requests to avoid TPM limits
                gap = time.time() - LAST_REQUEST
                if gap < 3:
                    time.sleep(3 - gap)

                resp = requests.post(
                    GROQ_URL,
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}",
                             "Content-Type": "application/json"},
                    json={"model": MODEL, "messages": history, "max_tokens": 1024},
                    timeout=30,
                )
                LAST_REQUEST = time.time()
                if resp.status_code == 429:
                    wait = 15 * (attempt + 1)
                    last_error = f"Rate limited, retrying in {wait}s..."
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                reply = resp.json()["choices"][0]["message"]["content"]
                break
            except Exception as e:
                last_error = str(e)
                time.sleep(5)

        if reply is None:
            history.pop()
            return f"[Error after retries: {last_error}]"

        # check for tool call
        tool_match = re.search(r"\[TOOL:\s*(\{.*?\})\s*\]", reply, re.DOTALL)
        if tool_match:
            try:
                tool_data   = json.loads(tool_match.group(1))
                tool_name   = tool_data.get("name", "")
                tool_params = tool_data.get("params", {})
            except json.JSONDecodeError:
                tool_name, tool_params = "", {}

            visible = re.sub(r"\[TOOL:.*?\]", "", reply, flags=re.DOTALL).strip()
            result  = execute_tool(tool_name, tool_params)

            history.append({"role": "assistant", "content": reply})
            history.append({"role": "user", "content": f"[TOOL_RESULT: {tool_name}]\n{result}"})

            if on_tool_result:
                on_tool_result(tool_name, result, visible)
            continue

        # final reply
        mem_match   = re.search(r"\[MEMORY:\s*(.+?)\]", reply)
        clean_reply = re.sub(r"\[MEMORY:.*?\]", "", reply).strip()

        if mem_match:
            fact = mem_match.group(1).strip()
            if fact and fact not in memory["facts"]:
                memory["facts"].append(fact)
                if len(memory["facts"]) > 40:
                    memory["facts"] = memory["facts"][-40:]

        memory["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_memory(memory)
        history[0] = {"role": "system", "content": build_system_prompt(memory)}
        history.append({"role": "assistant", "content": clean_reply})
        return clean_reply

    history.pop()
    return "[Error: too many tool call rounds]"

# ── Tray icon ──────────────────────────────────────────────────────────────────
def make_icon():
    size = 64
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size-4, size-4], fill="#89b4fa")
    draw.text((18, 16), "J", fill="#1e1e2e")
    return img

# ── Chat window ────────────────────────────────────────────────────────────────
class JarvisWindow:
    def __init__(self):
        self.root    = None
        self.visible = False
        self._dx = self._dy = 0
        self._build()

    def _build(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)
        self.root.geometry("480x560")
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.root.withdraw()

        # header
        header = tk.Frame(self.root, bg="#181825", pady=10)
        header.pack(fill="x")
        tk.Label(header, text="◈  JARVIS", bg="#181825",
                 fg="#89b4fa", font=("Courier New", 13, "bold"), padx=16).pack(side="left")
        tk.Button(header, text="✕", bg="#181825", fg="#6c7086",
                  font=("Courier New", 11), bd=0, activebackground="#181825",
                  activeforeground="#f38ba8", cursor="hand2",
                  command=self.hide).pack(side="right", padx=12)
        tk.Button(header, text="⟳", bg="#181825", fg="#6c7086",
                  font=("Courier New", 11), bd=0, activebackground="#181825",
                  activeforeground="#a6e3a1", cursor="hand2",
                  command=self.clear).pack(side="right")

        # chat
        chat_frame = tk.Frame(self.root, bg="#1e1e2e")
        chat_frame.pack(fill="both", expand=True)
        self.chat = tk.Text(
            chat_frame, bg="#1e1e2e", fg="#cdd6f4",
            font=("Courier New", 11), wrap="word",
            bd=0, padx=14, pady=12,
            insertbackground="#89b4fa",
            selectbackground="#45475a", selectforeground="#cdd6f4",
            exportselection=1, state="normal", cursor="arrow",
        )
        self.chat.pack(fill="both", expand=True, side="left")
        sb = tk.Scrollbar(chat_frame, command=self.chat.yview,
                          width=0, bd=0, highlightthickness=0,
                          troughcolor="#1e1e2e", bg="#1e1e2e")
        sb.pack(side="right", fill="y")
        self.chat.configure(yscrollcommand=sb.set)

        def _block_typing(e):
            if e.state & 0x4: return None
            if e.keysym in ("Up","Down","Left","Right","Prior","Next","Home","End"): return None
            return "break"
        self.chat.bind("<Key>", _block_typing)
        self.chat.bind("<MouseWheel>",
                       lambda e: self.chat.yview_scroll(int(-1*(e.delta/120)), "units"))

        self.chat.tag_config("you",        foreground="#89b4fa", font=("Courier New", 10, "bold"))
        self.chat.tag_config("jarvis",     foreground="#a6e3a1", font=("Courier New", 10, "bold"))
        self.chat.tag_config("tool_tag",   foreground="#fab387", font=("Courier New", 10, "bold"))
        self.chat.tag_config("msg",        foreground="#cdd6f4", font=("Courier New", 11))
        self.chat.tag_config("tool_out",   foreground="#fab387", font=("Courier New", 10))
        self.chat.tag_config("err",        foreground="#f38ba8", font=("Courier New", 11))
        self.chat.tag_config("thinking",   foreground="#6c7086", font=("Courier New", 10, "italic"))
        self.chat.tag_config("code",       foreground="#cba6f7", font=("Courier New", 11),
                              background="#181825", lmargin1=14, lmargin2=14, rmargin=14,
                              selectbackground="#45475a", selectforeground="#cba6f7")
        self.chat.tag_config("code_label", foreground="#6c7086", font=("Courier New", 9),
                              background="#181825", lmargin1=14,
                              selectbackground="#45475a", selectforeground="#6c7086")

        tk.Frame(self.root, bg="#313244", height=1).pack(fill="x")

        # input
        input_frame = tk.Frame(self.root, bg="#181825", pady=10, padx=12)
        input_frame.pack(fill="x")
        self.entry = tk.Text(
            input_frame, bg="#313244", fg="#cdd6f4",
            font=("Courier New", 11), wrap="word",
            bd=0, padx=10, pady=8, height=3,
            insertbackground="#89b4fa", selectbackground="#45475a",
        )
        self.entry.pack(fill="x", side="left", expand=True)
        self.entry.bind("<Return>",       self._on_enter)
        self.entry.bind("<Shift-Return>", lambda e: None)
        self.entry.focus_set()

        em = tk.Menu(self.root, tearoff=0, bg="#313244", fg="#cdd6f4",
                     activebackground="#45475a", activeforeground="#cdd6f4", bd=0)
        em.add_command(label="Paste",      command=lambda: self.entry.event_generate("<<Paste>>"))
        em.add_command(label="Copy",       command=lambda: self.entry.event_generate("<<Copy>>"))
        em.add_command(label="Cut",        command=lambda: self.entry.event_generate("<<Cut>>"))
        em.add_separator()
        em.add_command(label="Select All", command=lambda: self.entry.tag_add("sel","1.0","end"))
        self.entry.bind("<Button-3>", lambda e: em.tk_popup(e.x_root, e.y_root))

        cm = tk.Menu(self.root, tearoff=0, bg="#313244", fg="#cdd6f4",
                     activebackground="#45475a", activeforeground="#cdd6f4", bd=0)
        cm.add_command(label="Copy Selection", command=lambda: self.chat.event_generate("<<Copy>>"))
        cm.add_command(label="Select All",     command=lambda: self.chat.tag_add("sel","1.0","end"))
        self.chat.bind("<Button-3>", lambda e: cm.tk_popup(e.x_root, e.y_root))

        tk.Button(input_frame, text="↵", bg="#89b4fa", fg="#1e1e2e",
                  font=("Courier New", 13, "bold"), bd=0, width=3,
                  activebackground="#74c7ec", cursor="hand2",
                  command=self.send).pack(side="right", padx=(8, 0))

        header.bind("<ButtonPress-1>", lambda e: (setattr(self,"_dx",e.x), setattr(self,"_dy",e.y)))
        header.bind("<B1-Motion>",     lambda e: self.root.geometry(
            f"+{self.root.winfo_x()+e.x-self._dx}+{self.root.winfo_y()+e.y-self._dy}"))

    def _on_enter(self, e):
        self.send(); return "break"

    def send(self):
        text = self.entry.get("1.0", "end").strip()
        if not text: return
        self.entry.delete("1.0", "end")
        self._append("YOU", text, "you")
        self._append("", "thinking...", "thinking")
        threading.Thread(target=self._do_request, args=(text,), daemon=True).start()

    def _do_request(self, text):
        def on_tool(name, result, visible_text):
            self.root.after(0, self._show_tool, name, result, visible_text)
        reply = ask_groq(text, on_tool_result=on_tool)
        self.root.after(0, self._on_reply, reply)

    def _show_tool(self, name, result, visible_text):
        self._remove_thinking()
        if visible_text:
            self._append("JARVIS", visible_text, "jarvis")
        self.chat.insert("end", f"\n  ⚙ {name}\n", "tool_tag")
        display = result if len(result) < 600 else result[:600] + "\n...[truncated]"
        self.chat.insert("end", f"{display}\n", "tool_out")
        self.chat.see("end")
        self._append("", "thinking...", "thinking")

    def _on_reply(self, reply):
        self._remove_thinking()
        tag = "err" if reply.startswith("[Error") else "msg"
        self._append("JARVIS", reply, "jarvis", msg_tag=tag)

    def _remove_thinking(self):
        start = self.chat.search("thinking...", "1.0", stopindex="end")
        if start:
            self.chat.delete(start, f"{start}+12c\n")

    def _append(self, label, text, label_tag, msg_tag="msg"):
        if label:
            self.chat.insert("end", f"\n{label}\n", label_tag)
        parts = re.split(r"(```(?:\w+)?\n?)", text)
        in_code = False
        for part in parts:
            m = re.match(r"```(\w+)?", part)
            if m:
                in_code = True
                lang = m.group(1) or ""
                self.chat.insert("end", f"  {lang or 'code'}\n", "code_label")
            elif part.strip() == "```":
                in_code = False
                self.chat.insert("end", "\n", "code")
            else:
                self.chat.insert("end", part, "code" if in_code else msg_tag)
        self.chat.insert("end", "\n")
        self.chat.see("end")

    def clear(self):
        global history
        history = [history[0]]
        self.chat.delete("1.0", "end")

    def show(self):
        self.root.deiconify(); self.root.lift()
        self.root.focus_force(); self.entry.focus_set()
        self.visible = True

    def hide(self):
        self.root.withdraw(); self.visible = False

    def toggle(self):
        self.hide() if self.visible else self.show()

    def run(self):
        self.root.mainloop()


# ── Main ───────────────────────────────────────────────────────────────────────
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

if __name__ == "__main__":
    main()
