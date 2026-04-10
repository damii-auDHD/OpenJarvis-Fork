import tkinter as tk
import threading
import re
from PIL import Image, ImageDraw
from src.config import APP_NAME
from src.api import ask_groq, clear_history

def make_icon():
    size = 64
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size-4, size-4], fill="#89b4fa")
    draw.text((18, 16), "J", fill="#1e1e2e")
    return img

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
        clear_history()
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
