import asyncio
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("Jarvis.BrowserService")


class BrowserService:
    """
    Browser automation service using Playwright.
    Provides async methods for web navigation and interaction.
    """

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self._playwright = None
        self._browser = None
        self._page = None
        logger.info(f"BrowserService created (headless={headless}, timeout={timeout}ms)")

    async def launch(self):
        """Launch browser. Lazy-imports playwright to avoid import errors when not installed."""
        from playwright.async_api import async_playwright
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._page = await self._browser.new_page()
        self._page.set_default_timeout(self.timeout)
        logger.info("Browser launched")

    async def _ensure_page(self):
        """Ensure browser is launched and page exists."""
        if self._page is None:
            await self.launch()

    async def goto(self, url: str) -> str:
        """Navigate to URL. Returns page title."""
        await self._ensure_page()
        try:
            await self._page.goto(url, wait_until="domcontentloaded")
            title = await self._page.title()
            logger.info(f"Navigated to {url} - Title: {title}")
            return title
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            raise

    async def get_page_text(self) -> str:
        """Extract visible text content from current page."""
        await self._ensure_page()
        return await self._page.inner_text("body")

    async def get_page_title(self) -> str:
        """Get current page title."""
        await self._ensure_page()
        return await self._page.title()

    async def get_page_url(self) -> str:
        """Get current page URL."""
        await self._ensure_page()
        return self._page.url

    async def click_element(self, selector: str) -> None:
        """Click an element by CSS selector."""
        await self._ensure_page()
        await self._page.click(selector)
        logger.info(f"Clicked: {selector}")

    async def type_in(self, selector: str, text: str) -> None:
        """Type text into an input element."""
        await self._ensure_page()
        await self._page.fill(selector, text)
        logger.info(f"Typed into {selector}")

    async def screenshot(self, path: str = "screenshot.png") -> str:
        """Take screenshot, save to path. Returns path."""
        await self._ensure_page()
        await self._page.screenshot(path=path)
        logger.info(f"Screenshot saved: {path}")
        return path

    async def get_links(self) -> List[Dict[str, str]]:
        """Extract all links from current page."""
        await self._ensure_page()
        links = await self._page.eval_on_selector_all(
            "a[href]",
            "elements => elements.map(e => ({text: e.innerText.trim(), href: e.href}))"
        )
        return links

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._page = None
        self._playwright = None
        logger.info("Browser closed")
