import os
from playwright.sync_api import sync_playwright, Browser, Page, Playwright

INBOX = os.path.join(os.path.dirname(__file__), "inbox")

_pw: Playwright | None = None
_browser: Browser | None = None
_page: Page | None = None


def _get_page() -> Page:
    global _pw, _browser, _page
    if _pw is None:
        _pw = sync_playwright().start()
    if _browser is None or not _browser.is_connected():
        _browser = _pw.chromium.launch(headless=False, args=["--start-maximized"])
    if _page is None or _page.is_closed():
        _page = _browser.new_page()
    return _page


def browser_goto(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    page = _get_page()
    page.goto(url, wait_until="domcontentloaded", timeout=20000)
    return f"Opened {url} — page title: {page.title()}"


def browser_click(text: str) -> str:
    page = _get_page()
    strategies = [
        lambda: page.get_by_role("button", name=text).first.click(),
        lambda: page.get_by_role("link", name=text).first.click(),
        lambda: page.get_by_text(text, exact=False).first.click(),
        lambda: page.locator(f"[aria-label*='{text}' i]").first.click(),
        lambda: page.locator(f"[placeholder*='{text}' i]").first.click(),
    ]
    for strategy in strategies:
        try:
            strategy()
            page.wait_for_load_state("domcontentloaded", timeout=5000)
            return f"Clicked '{text}'."
        except Exception:
            continue
    return f"Couldn't find anything to click matching '{text}'."


def browser_fill(field: str, value: str) -> str:
    page = _get_page()
    strategies = [
        lambda: page.get_by_label(field, exact=False).first.fill(value),
        lambda: page.get_by_placeholder(field, exact=False).first.fill(value),
        lambda: page.locator(f"input[name*='{field}' i]").first.fill(value),
        lambda: page.locator(f"textarea[name*='{field}' i]").first.fill(value),
    ]
    for strategy in strategies:
        try:
            strategy()
            return f"Filled '{field}' with '{value}'."
        except Exception:
            continue
    return f"Couldn't find a field matching '{field}'."


def browser_get_text() -> str:
    page = _get_page()
    try:
        text = page.inner_text("body")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return "\n".join(lines[:150])  # first 150 non-empty lines
    except Exception as e:
        return f"Error reading page: {e}"


def browser_get_url() -> str:
    return _get_page().url


def browser_scroll(direction: str = "down") -> str:
    page = _get_page()
    key = "PageDown" if direction.lower() == "down" else "PageUp"
    page.keyboard.press(key)
    return f"Scrolled {direction}."


def browser_press_enter() -> str:
    _get_page().keyboard.press("Enter")
    return "Pressed Enter."


def browser_screenshot() -> str:
    page = _get_page()
    path = os.path.join(INBOX, "browser_screenshot.png")
    page.screenshot(path=path, full_page=False)
    return "Browser screenshot saved to inbox."


def browser_wait(seconds: float = 2.0) -> str:
    import time
    time.sleep(seconds)
    return f"Waited {seconds} seconds."


def browser_close() -> str:
    global _browser, _page, _pw
    try:
        if _page and not _page.is_closed():
            _page.close()
        if _browser and _browser.is_connected():
            _browser.close()
        if _pw:
            _pw.stop()
    except Exception:
        pass
    _page = _browser = _pw = None
    return "Browser closed."
