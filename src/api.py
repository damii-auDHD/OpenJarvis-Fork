import time
import requests
import re
import json
from datetime import datetime
from src.config import GROQ_API_KEY, GROQ_URL, MODEL
from src.tools import execute_tool
from src.memory import load_memory, save_memory
from src.prompts import build_system_prompt

memory = load_memory()
history = [{"role": "system", "content": build_system_prompt(memory)}]
LAST_REQUEST = 0.0

def ask_groq(user_text, on_tool_result=None):
    global LAST_REQUEST, memory, history
    history.append({"role": "user", "content": user_text})
    last_error = None

    for _ in range(8):
        reply = None
        for attempt in range(4):
            try:
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

def clear_history():
    global history
    history = [history[0]]
