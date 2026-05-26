from playwright.sync_api import sync_playwright
from typing import Optional


class PlaywrightFetcher:
    """Fetch JS-rendered pages using headless Chromium."""

    def __init__(self):
        self._pw = None
        self._browser = None

    def _ensure_browser(self):
        if self._browser is None:
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=True)

    def fetch(self, url: str, wait_selector: str = None, timeout: int = 30000) -> tuple[Optional[str], int]:
        self._ensure_browser()
        page = self._browser.new_page()
        try:
            response = page.goto(url, timeout=timeout, wait_until="networkidle")
            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=10000)
            status = response.status if response else 0
            content = page.content()
            return content, status
        except Exception:
            return None, 0
        finally:
            page.close()

    def close(self):
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()
