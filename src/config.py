import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
MODEL        = "llama-3.3-70b-versatile"
HOTKEY       = "win+j"
APP_NAME     = "Jarvis"
MEMORY_FILE  = os.path.join(os.path.expanduser("~"), ".jarvis_memory.json")
USER_NAME    = os.environ.get("JARVIS_USER_NAME", "User")
