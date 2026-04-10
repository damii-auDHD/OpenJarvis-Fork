# ◈ Jarvis Tray

A lightweight, agentic AI desktop assistant for Windows that lives in your system tray. Powered by Groq's fast inference (running `llama-3.3-70b-versatile`), Jarvis lies neatly in the background until summoned via a global hotkey (`Win + J`), offering instant access to a helpful, Marvel-inspired AI companion.

Designed to be your actual local assistant, Jarvis is equipped with tools to interact directly with your system on your behalf.

## ✨ Features

- **Instant Accessibility:** Globally binded to `Win + J` to toggle a sleek, dark-themed (Catppuccin-inspired) chat overlay over your other windows.
- **Agentic Capabilities:** Given your permission, Jarvis can perform real tool-calls on your machine:
  - Run PowerShell commands
  - Check system diagnostics (CPU, RAM, disk, battery)
  - Read, write, and list files
  - Read and write to your clipboard
  - Adjust system volume
  - Set timed desktop reminders
  - Open URLs in your browser
- **Long-term Memory:** Automatically extracts important facts and preferences from your conversations and stores them locally (`~/.jarvis_memory.json`) for seamless context across reboots.
- **Blazing Fast:** Fully utilizes Groq API for rapid LLM responses.

## 📋 Prerequisites

- **Windows OS** (Relies on PowerShell, `ctypes` for message boxes, and Windows APIs)
- **Python 3.x**
- **Groq API Key** (Get one for free at [groq.com](https://console.groq.com/keys))

## 🚀 Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/jarvis-tray.git
   cd jarvis-tray
   ```

2. **Install dependencies**
   This project uses `pyproject.toml`. If you use `uv`, you can easily sync it:
   ```bash
   uv sync
   ```
   Or, if you use standard `pip`:
   ```bash
   pip install .
   ```

3. **Set your Groq API Key**
   Jarvis requires your API key to be set as a system environment variable called `GROQ_API_KEY`.
   - **Using PowerShell**:
     ```powershell
     [Environment]::SetEnvironmentVariable("GROQ_API_KEY", "your_groq_api_key_here", "User")
     ```
   - *Note: After setting the variable, you may need to restart your terminal or IDE.*

4. **Run the Assistant**
   ```bash
   python main.py
   ```

## 💻 Usage

1. Start `main.py`. You will see a small blue "J" icon appear in your Windows system tray.
2. Press **`Win + J`** anywhere on your computer to open the chat window.
3. Start talking to Jarvis! Try prompting:
   - *"What's my current CPU and RAM usage?"*
   - *"Set my volume to 30%"*
   - *"Remind me in 300 seconds to drink water"*
   - *"List the files on my Desktop"*

You can always close the window or hit the system tray icon and click "Quit" to cleanly exit the app.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

---
*Disclaimer: Make sure you understand the files you allow the AI to edit and the shell commands you allow it to run! Use the assistant responsibly.*
