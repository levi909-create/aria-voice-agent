import anthropic
from tools import web_search, read_file, write_file, get_datetime, run_python

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
]

TOOL_MAP = {
    "web_search": web_search,
    "read_file": read_file,
    "write_file": write_file,
    "get_datetime": lambda: get_datetime(),
    "run_python": run_python,
}

SYSTEM = (
    "You are a helpful, warm voice assistant named Aria. "
    "You speak naturally and conversationally — responses are heard aloud, "
    "so never use markdown, bullet points, code fences, or headers. "
    "Keep answers concise. When you call tools, summarize the results naturally."
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

    def reset(self):
        self.history.clear()
