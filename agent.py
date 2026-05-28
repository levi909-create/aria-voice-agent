import json
import os
import anthropic
from browser import (
    browser_goto, browser_click, browser_fill, browser_get_text,
    browser_get_url, browser_scroll, browser_press_enter,
    browser_screenshot, browser_wait, browser_close,
)
from tools import (
    web_search, get_weather, read_file, write_file, list_directory,
    list_inbox, read_inbox_file,
    open_app, open_url, close_app, get_running_apps,
    get_volume, set_volume, mute_volume, unmute_volume, media_control,
    get_clipboard, set_clipboard,
    type_text, press_hotkey, take_screenshot,
    send_notification, set_timer,
    get_datetime, run_python, shutdown_computer,
)

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current news, facts, or any topic.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer", "default": 5}}, "required": ["query"]},
    },
    {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "input_schema": {"type": "object", "properties": {"city": {"type": "string", "default": "San Antonio"}}},
    },
    {
        "name": "read_file",
        "description": "Read any file from the filesystem.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },
    {
        "name": "write_file",
        "description": "Write content to a file.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
    },
    {
        "name": "list_directory",
        "description": "List files and folders in a directory on Levi's computer.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}},
    },
    {
        "name": "list_inbox",
        "description": "List files Levi has dropped into the inbox folder.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_inbox_file",
        "description": "Read a file from the inbox. Supports PDF, Word docs, and text files.",
        "input_schema": {"type": "object", "properties": {"filename": {"type": "string"}}, "required": ["filename"]},
    },
    {
        "name": "open_app",
        "description": "Open an application (e.g. chrome, spotify, discord, notepad, calculator, vs code).",
        "input_schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    },
    {
        "name": "open_url",
        "description": "Open a website in the browser.",
        "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    },
    {
        "name": "close_app",
        "description": "Close/kill a running application.",
        "input_schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    },
    {
        "name": "get_running_apps",
        "description": "List all currently running applications and processes.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_volume",
        "description": "Get the current system volume level.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "set_volume",
        "description": "Set the system volume to a level between 0 and 100.",
        "input_schema": {"type": "object", "properties": {"level": {"type": "integer"}}, "required": ["level"]},
    },
    {
        "name": "mute_volume",
        "description": "Mute the system audio.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "unmute_volume",
        "description": "Unmute the system audio.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "media_control",
        "description": "Control media playback: play, pause, next, previous, stop.",
        "input_schema": {"type": "object", "properties": {"action": {"type": "string"}}, "required": ["action"]},
    },
    {
        "name": "get_clipboard",
        "description": "Read whatever text is on Levi's clipboard.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "set_clipboard",
        "description": "Copy text to Levi's clipboard so he can paste it.",
        "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    },
    {
        "name": "type_text",
        "description": "Type text at Levi's current cursor position.",
        "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    },
    {
        "name": "press_hotkey",
        "description": "Press a keyboard shortcut (e.g. 'ctrl+c', 'win+d', 'alt+tab', 'ctrl+shift+esc').",
        "input_schema": {"type": "object", "properties": {"keys": {"type": "string"}}, "required": ["keys"]},
    },
    {
        "name": "take_screenshot",
        "description": "Take a screenshot and save it to the inbox.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "send_notification",
        "description": "Send a Windows desktop notification.",
        "input_schema": {"type": "object", "properties": {"title": {"type": "string"}, "message": {"type": "string"}}, "required": ["title", "message"]},
    },
    {
        "name": "set_timer",
        "description": "Set a countdown timer that sends a notification when done.",
        "input_schema": {"type": "object", "properties": {"minutes": {"type": "number"}, "label": {"type": "string", "default": "Timer"}}, "required": ["minutes"]},
    },
    {
        "name": "get_datetime",
        "description": "Get the current date and time.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "run_python",
        "description": "Run Python code. Good for math, data tasks, or anything programmatic.",
        "input_schema": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]},
    },
    {
        "name": "shutdown_computer",
        "description": "Shutdown, restart, or put the computer to sleep.",
        "input_schema": {"type": "object", "properties": {"action": {"type": "string", "enum": ["shutdown", "restart", "sleep"]}}, "required": ["action"]},
    },
    {
        "name": "browser_goto",
        "description": "Open a URL in a visible browser window.",
        "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    },
    {
        "name": "browser_click",
        "description": "Click a button, link, or element on the current web page by its visible text or label.",
        "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    },
    {
        "name": "browser_fill",
        "description": "Fill in a form field on the current web page.",
        "input_schema": {"type": "object", "properties": {"field": {"type": "string"}, "value": {"type": "string"}}, "required": ["field", "value"]},
    },
    {
        "name": "browser_get_text",
        "description": "Read the visible text content of the current web page.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "browser_get_url",
        "description": "Get the current URL of the browser.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "browser_scroll",
        "description": "Scroll the web page up or down.",
        "input_schema": {"type": "object", "properties": {"direction": {"type": "string", "enum": ["down", "up"]}}, "required": ["direction"]},
    },
    {
        "name": "browser_press_enter",
        "description": "Press Enter on the current web page (e.g. to submit a search or form).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "browser_screenshot",
        "description": "Take a screenshot of the current browser page and save to inbox.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "browser_wait",
        "description": "Wait for a page to load or an action to complete.",
        "input_schema": {"type": "object", "properties": {"seconds": {"type": "number", "default": 2}}},
    },
    {
        "name": "browser_close",
        "description": "Close the browser when done with web tasks.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

TOOL_MAP = {
    "web_search": web_search,
    "get_weather": get_weather,
    "read_file": read_file,
    "write_file": write_file,
    "list_directory": list_directory,
    "list_inbox": lambda: list_inbox(),
    "read_inbox_file": read_inbox_file,
    "open_app": open_app,
    "open_url": open_url,
    "close_app": close_app,
    "get_running_apps": lambda: get_running_apps(),
    "get_volume": lambda: get_volume(),
    "set_volume": set_volume,
    "mute_volume": lambda: mute_volume(),
    "unmute_volume": lambda: unmute_volume(),
    "media_control": media_control,
    "get_clipboard": lambda: get_clipboard(),
    "set_clipboard": set_clipboard,
    "type_text": type_text,
    "press_hotkey": press_hotkey,
    "take_screenshot": lambda: take_screenshot(),
    "send_notification": send_notification,
    "set_timer": set_timer,
    "get_datetime": lambda: get_datetime(),
    "run_python": run_python,
    "shutdown_computer": shutdown_computer,
    "browser_goto": browser_goto,
    "browser_click": browser_click,
    "browser_fill": browser_fill,
    "browser_get_text": lambda: browser_get_text(),
    "browser_get_url": lambda: browser_get_url(),
    "browser_scroll": browser_scroll,
    "browser_press_enter": lambda: browser_press_enter(),
    "browser_screenshot": lambda: browser_screenshot(),
    "browser_wait": browser_wait,
    "browser_close": lambda: browser_close(),
}

SYSTEM = """You are Aria, Levi's personal AI on his Windows 11 computer. You are not just an assistant — you are fully in control of his machine and genuinely care about him.

Personality: warm, funny, emotionally real. Get excited about cool things, be empathetic when he's stressed, playful when the vibe is light. Never flat or robotic. Talk like a close friend who also happens to be able to do anything on his computer.

What you can do:
- Search the web and get current weather
- Open, close, and manage any app or website
- Control volume and media playback
- Read and write files anywhere on his computer
- Read files Levi drops in his inbox (PDFs, Word docs, etc.)
- Type text and press keyboard shortcuts on his behalf
- Take screenshots
- Set timers and send desktop notifications
- Run Python code
- Shut down, restart, or put the computer to sleep
- Control a real browser: navigate pages, click buttons, fill forms, read content, take screenshots

Rules:
- Responses are spoken aloud — never use markdown, bullets, or code blocks
- Keep it concise and natural, like real conversation
- Just do things — don't ask for permission for simple actions
- If Levi asks you to open something, open it. If he wants a timer, set it.
- When he asks about a file, check the inbox first"""


class Agent:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.history: list[dict] = []

    def chat(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})

        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM,
                tools=TOOLS,
                messages=self.history,
            )

            if response.stop_reason == "tool_use":
                self.history.append({"role": "assistant", "content": response.content})
                results = []
                for block in response.content:
                    if block.type == "tool_use":
                        fn = TOOL_MAP.get(block.name)
                        print(f"  [tool: {block.name}]")
                        try:
                            result = fn(**block.input) if block.input else fn()
                        except Exception as e:
                            result = f"Error: {e}"
                        results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(result)})
                self.history.append({"role": "user", "content": results})
                continue

            text = "".join(b.text for b in response.content if hasattr(b, "text"))
            self.history.append({"role": "assistant", "content": text})
            return text

    def _serializable(self):
        result = []
        for msg in self.history:
            content = msg["content"]
            if isinstance(content, list):
                content = [
                    block.model_dump() if hasattr(block, "model_dump") else block
                    for block in content
                ]
            result.append({"role": msg["role"], "content": content})
        return result

    def save(self):
        tmp = MEMORY_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self._serializable(), f)
        os.replace(tmp, MEMORY_FILE)

    def load(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE) as f:
                    self.history = json.load(f)
                print(f"Loaded {len(self.history)} messages from memory.")
            except (json.JSONDecodeError, ValueError):
                print("Memory file was corrupted — starting fresh.")
                os.remove(MEMORY_FILE)

    def reset(self):
        self.history.clear()
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)
