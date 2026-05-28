import datetime
import os
import subprocess
import threading
import time
import webbrowser

import psutil
import pyautogui
import requests
from ddgs import DDGS

INBOX = os.path.join(os.path.dirname(__file__), "inbox")

pyautogui.FAILSAFE = False


# ── Web ──────────────────────────────────────────────────────────────────────

def web_search(query: str, max_results: int = 5) -> str:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    if not results:
        return "No results found."
    return "\n\n".join(f"{r['title']}: {r['body']}  ({r['href']})" for r in results)


def get_weather(city: str = "San Antonio") -> str:
    try:
        r = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
        return r.text.strip()
    except Exception as e:
        return f"Couldn't get weather: {e}"


# ── Files ─────────────────────────────────────────────────────────────────────

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


def list_directory(path: str = "C:\\Users\\Levitikus") -> str:
    try:
        items = os.listdir(path)
        dirs  = [f"[folder] {i}" for i in items if os.path.isdir(os.path.join(path, i))]
        files = [f"[file]   {i}" for i in items if os.path.isfile(os.path.join(path, i))]
        return "\n".join(dirs + files) or "Empty."
    except Exception as e:
        return f"Error: {e}"


# ── Inbox ─────────────────────────────────────────────────────────────────────

def list_inbox() -> str:
    files = [f for f in os.listdir(INBOX) if f != ".gitkeep"]
    return "Files in inbox: " + ", ".join(files) if files else "The inbox is empty."


def read_inbox_file(filename: str) -> str:
    path = os.path.join(INBOX, filename)
    if not os.path.exists(path):
        return f"'{filename}' not found. Inbox has: {list_inbox()}"
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            return "\n".join(p.extract_text() or "" for p in PdfReader(path).pages)
        except Exception as e:
            return f"PDF error: {e}"
    if ext in (".docx", ".doc"):
        try:
            from docx import Document
            return "\n".join(p.text for p in Document(path).paragraphs)
        except Exception as e:
            return f"Word error: {e}"
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"


# ── Apps & Browser ────────────────────────────────────────────────────────────

APP_ALIASES = {
    "chrome": "chrome.exe", "google chrome": "chrome.exe", "browser": "chrome.exe",
    "firefox": "firefox.exe", "edge": "msedge.exe",
    "notepad": "notepad.exe", "calculator": "calc.exe", "calc": "calc.exe",
    "explorer": "explorer.exe", "file explorer": "explorer.exe",
    "spotify": "spotify.exe", "discord": "discord.exe",
    "vs code": "code.exe", "vscode": "code.exe",
    "word": "winword.exe", "excel": "excel.exe", "powerpoint": "powerpnt.exe",
    "paint": "mspaint.exe", "task manager": "taskmgr.exe",
    "settings": "ms-settings:", "terminal": "wt.exe", "powershell": "powershell.exe",
}

def open_app(name: str) -> str:
    exe = APP_ALIASES.get(name.lower(), name)
    try:
        subprocess.Popen(exe, shell=True)
        return f"Opened {name}"
    except Exception as e:
        return f"Couldn't open {name}: {e}"


def open_url(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"


def close_app(name: str) -> str:
    killed = 0
    for proc in psutil.process_iter(["name"]):
        if name.lower() in proc.info["name"].lower():
            try:
                proc.kill()
                killed += 1
            except Exception:
                pass
    return f"Closed {killed} process(es) matching '{name}'." if killed else f"No running app found matching '{name}'."


def get_running_apps() -> str:
    names = sorted({p.info["name"] for p in psutil.process_iter(["name"]) if p.info["name"]})
    return ", ".join(names)


# ── Volume & Media ────────────────────────────────────────────────────────────

def get_volume() -> str:
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        vol = cast(interface, POINTER(IAudioEndpointVolume))
        level = round(vol.GetMasterVolumeLevelScalar() * 100)
        muted = vol.GetMute()
        return f"Volume is at {level}%{' (muted)' if muted else ''}."
    except Exception as e:
        return f"Couldn't get volume: {e}"


def set_volume(level: int) -> str:
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        vol = cast(interface, POINTER(IAudioEndpointVolume))
        vol.SetMasterVolumeLevelScalar(max(0, min(100, level)) / 100.0, None)
        return f"Volume set to {level}%."
    except Exception as e:
        return f"Couldn't set volume: {e}"


def mute_volume() -> str:
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        vol = cast(interface, POINTER(IAudioEndpointVolume))
        vol.SetMute(1, None)
        return "Muted."
    except Exception as e:
        return f"Error: {e}"


def unmute_volume() -> str:
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        vol = cast(interface, POINTER(IAudioEndpointVolume))
        vol.SetMute(0, None)
        return "Unmuted."
    except Exception as e:
        return f"Error: {e}"


def media_control(action: str) -> str:
    actions = {
        "play": "playpause", "pause": "playpause", "play/pause": "playpause",
        "next": "nexttrack", "skip": "nexttrack",
        "previous": "prevtrack", "back": "prevtrack",
        "stop": "stop",
    }
    key = actions.get(action.lower())
    if not key:
        return f"Unknown action '{action}'. Try: play, pause, next, previous, stop."
    pyautogui.press(key)
    return f"Media: {action}"


# ── Clipboard ─────────────────────────────────────────────────────────────────

def get_clipboard() -> str:
    try:
        import pyperclip
        return pyperclip.paste() or "(clipboard is empty)"
    except Exception as e:
        return f"Error: {e}"


def set_clipboard(text: str) -> str:
    try:
        import pyperclip
        pyperclip.copy(text)
        return "Copied to clipboard."
    except Exception as e:
        return f"Error: {e}"


# ── Keyboard & Screen ─────────────────────────────────────────────────────────

def type_text(text: str) -> str:
    try:
        import pyperclip
        pyperclip.copy(text)
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "v")
        return f"Typed text."
    except Exception as e:
        return f"Error: {e}"


def press_hotkey(keys: str) -> str:
    try:
        key_list = [k.strip() for k in keys.replace("+", " ").split()]
        pyautogui.hotkey(*key_list)
        return f"Pressed {keys}."
    except Exception as e:
        return f"Error: {e}"


def take_screenshot() -> str:
    try:
        from PIL import ImageGrab
        path = os.path.join(INBOX, "screenshot.png")
        ImageGrab.grab().save(path)
        return "Screenshot saved to inbox."
    except Exception as e:
        return f"Error: {e}"


# ── Notifications & Timers ────────────────────────────────────────────────────

def send_notification(title: str, message: str) -> str:
    try:
        from plyer import notification
        notification.notify(title=title, message=message, timeout=8)
        return "Notification sent."
    except Exception as e:
        return f"Error: {e}"


def set_timer(minutes: float, label: str = "Timer") -> str:
    def _run():
        time.sleep(minutes * 60)
        send_notification(label, f"Your {minutes}-minute timer is up!")
    threading.Thread(target=_run, daemon=True).start()
    return f"Timer set for {minutes} minute{'s' if minutes != 1 else ''}."


# ── System ────────────────────────────────────────────────────────────────────

def get_datetime() -> str:
    return datetime.datetime.now().strftime("%A, %B %d %Y — %I:%M %p")


def run_python(code: str) -> str:
    try:
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True, text=True, timeout=10,
        )
        out = result.stdout
        if result.stderr:
            out += f"\nstderr: {result.stderr}"
        return out.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: timed out (10s limit)"
    except Exception as e:
        return f"Error: {e}"


def shutdown_computer(action: str = "shutdown") -> str:
    actions = {"shutdown": "shutdown /s /t 10", "restart": "shutdown /r /t 10", "sleep": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"}
    cmd = actions.get(action.lower())
    if not cmd:
        return f"Unknown action. Use: shutdown, restart, or sleep."
    subprocess.run(cmd, shell=True)
    return f"Computer will {action} shortly."
