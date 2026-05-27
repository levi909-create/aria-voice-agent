import datetime
import os
import subprocess
import webbrowser

from ddgs import DDGS

INBOX = os.path.join(os.path.dirname(__file__), "inbox")


def web_search(query: str, max_results: int = 5) -> str:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    if not results:
        return "No results found."
    lines = []
    for r in results:
        lines.append(f"{r['title']}: {r['body']}  ({r['href']})")
    return "\n\n".join(lines)


def read_file(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"


def write_file(path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written to {path}"
    except Exception as e:
        return f"Error: {e}"


def list_inbox() -> str:
    """List files currently in the inbox folder."""
    files = os.listdir(INBOX)
    if not files:
        return "The inbox is empty."
    return "Files in inbox: " + ", ".join(files)


def read_inbox_file(filename: str) -> str:
    """Read a file from the inbox folder. Supports txt, pdf, docx, and most text formats."""
    path = os.path.join(INBOX, filename)
    if not os.path.exists(path):
        files = os.listdir(INBOX)
        return f"File '{filename}' not found. Inbox contains: {', '.join(files) or 'nothing'}"

    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            return f"Error reading PDF: {e}"

    if ext in (".docx", ".doc"):
        try:
            from docx import Document
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            return f"Error reading Word doc: {e}"

    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def open_app(name: str) -> str:
    """Open an application by name (e.g. notepad, chrome, spotify, calculator)."""
    aliases = {
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "browser": "chrome.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "spotify": "spotify.exe",
        "discord": "discord.exe",
        "vs code": "code.exe",
        "vscode": "code.exe",
        "word": "winword.exe",
        "excel": "excel.exe",
        "paint": "mspaint.exe",
        "task manager": "taskmgr.exe",
    }
    exe = aliases.get(name.lower(), name)
    try:
        subprocess.Popen(exe, shell=True)
        return f"Opened {name}"
    except Exception as e:
        return f"Couldn't open {name}: {e}"


def open_url(url: str) -> str:
    """Open a URL in the default web browser."""
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"


def take_screenshot() -> str:
    """Take a screenshot and save it to the inbox folder."""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        path = os.path.join(INBOX, "screenshot.png")
        img.save(path)
        return f"Screenshot saved to inbox as screenshot.png"
    except Exception as e:
        return f"Error taking screenshot: {e}"


def list_directory(path: str = "C:\\Users\\Levitikus") -> str:
    """List files and folders in a directory."""
    try:
        items = os.listdir(path)
        dirs = [f"[folder] {i}" for i in items if os.path.isdir(os.path.join(path, i))]
        files = [f"[file] {i}" for i in items if os.path.isfile(os.path.join(path, i))]
        return "\n".join(dirs + files) or "Empty folder."
    except Exception as e:
        return f"Error: {e}"


def get_clipboard() -> str:
    """Read whatever is currently on the clipboard."""
    try:
        import pyperclip
        text = pyperclip.paste()
        return text or "(clipboard is empty)"
    except Exception as e:
        return f"Error: {e}"


def set_clipboard(text: str) -> str:
    """Write text to the clipboard."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return "Copied to clipboard."
    except Exception as e:
        return f"Error: {e}"


def get_datetime() -> str:
    return datetime.datetime.now().strftime("%A, %B %d %Y — %I:%M %p")


def run_python(code: str) -> str:
    try:
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        out = result.stdout
        if result.stderr:
            out += f"\nstderr: {result.stderr}"
        return out.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: timed out (10s limit)"
    except Exception as e:
        return f"Error: {e}"
