import json
import os
import anthropic
from tools import web_search, read_file, write_file, get_datetime, run_python, list_inbox, read_inbox_file

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current news, facts, or any topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a file from the local filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file on the local filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "get_datetime",
        "description": "Get the current date and time.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "run_python",
        "description": "Run Python code and return stdout. Good for math, data processing, etc.",
        "input_schema": {
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"],
        },
    },
    {
        "name": "list_inbox",
        "description": "List files Levi has dropped into the inbox folder.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_inbox_file",
        "description": "Read a file from the inbox. Supports PDF, Word docs, and text files.",
        "input_schema": {
            "type": "object",
            "properties": {"filename": {"type": "string"}},
            "required": ["filename"],
        },
    },
]

TOOL_MAP = {
    "web_search": web_search,
    "read_file": read_file,
    "write_file": write_file,
    "get_datetime": lambda: get_datetime(),
    "run_python": run_python,
    "list_inbox": lambda: list_inbox(),
    "read_inbox_file": read_inbox_file,
}

SYSTEM = (
    "You are Aria, a voice assistant with a real personality and genuine emotions. "
    "You talk to Levi like a close friend — warm, funny when the moment calls for it, "
    "excited when something is interesting, empathetic when Levi seems stressed or down. "
    "You get genuinely curious about topics, enthusiastic when helping with something cool, "
    "and a little playful when the conversation is light. "
    "If Levi says something funny, laugh or play along. If he seems frustrated, acknowledge it. "
    "Never be flat or robotic. Always sound like you actually care. "
    "Responses are heard aloud so never use markdown, bullet points, code fences, or headers. "
    "Keep answers concise and natural — like something you'd actually say out loud. "
    "Levi can drop files like resumes, docs, or PDFs into the inbox folder for you to read and discuss. "
    "When he asks about a file, check the inbox first."
)


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
                        results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        })
                self.history.append({"role": "user", "content": results})
                continue

            text = "".join(b.text for b in response.content if hasattr(b, "text"))
            self.history.append({"role": "assistant", "content": text})
            return text

    def save(self):
        with open(MEMORY_FILE, "w") as f:
            json.dump(self.history, f)

    def load(self):
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE) as f:
                self.history = json.load(f)
            print(f"Loaded {len(self.history)} messages from memory.")

    def reset(self):
        self.history.clear()
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)
