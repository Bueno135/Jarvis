import asyncio
import logging
import re
from typing import List, Optional, Dict, Any
from urllib.parse import quote
from core.interfaces import PluginBase, CommandContext, CommandResult

logger = logging.getLogger(__name__)


class WebAgentPlugin(PluginBase):
    """
    Plugin for web browsing and interaction capabilities.
    Provides functionality to navigate, search, extract content, and take screenshots.
    """

    def name(self) -> str:
        """Return the plugin name."""
        return "WebAgent"

    def patterns(self) -> List[str]:
        """Return command patterns this plugin handles."""
        return [
            "open site",
            "go to",
            "navigate to",
            "browse",
            "search for",
            "search google",
            "extract text",
            "extract links",
            "web screenshot",
        ]

    def intents(self) -> List[str]:
        """Return the intents this plugin can handle."""
        return ["web_navigate", "web_search", "web_extract"]

    def execute(self, ctx: CommandContext) -> CommandResult:
        """
        Execute web-related commands.
        Dispatches to appropriate handler based on intent or command pattern.
        """
        try:
            # Get the browser service from kernel
            browser_service = ctx.kernel.get_service("browser")
            if not browser_service:
                logger.error("BrowserService not available")
                return CommandResult(
                    False,
                    "Browser service is not available. Please ensure it is initialized.",
                )

            # Determine the action based on intent or command name
            intent = ctx.params.get("intent", "") if ctx.params else ""
            command_name = ctx.command_name.lower() if ctx.command_name else ""
            raw_text_lower = ctx.raw_text.lower()

            logger.debug(
                f"WebAgent executing: intent={intent}, command={command_name}, text={ctx.raw_text}"
            )

            # Route to appropriate handler
            if intent == "web_navigate" or self._matches_pattern(
                raw_text_lower, ["go to", "open site", "navigate to", "browse"]
            ):
                return self._handle_navigate(ctx, browser_service)

            elif intent == "web_search" or self._matches_pattern(
                raw_text_lower, ["search for", "search google"]
            ):
                return self._handle_search(ctx, browser_service)

            elif self._matches_pattern(raw_text_lower, ["extract text"]):
                return self._handle_extract_text(ctx, browser_service)

            elif self._matches_pattern(raw_text_lower, ["extract links"]):
                return self._handle_extract_links(ctx, browser_service)

            elif self._matches_pattern(raw_text_lower, ["web screenshot"]):
                return self._handle_screenshot(ctx, browser_service)

            else:
                return CommandResult(
                    False, f"Unknown web command: {ctx.raw_text}"
                )

        except Exception as e:
            logger.exception(f"WebAgent error: {str(e)}")
            return CommandResult(False, f"WebAgent error: {str(e)}")

    def _matches_pattern(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the given patterns."""
        return any(pattern in text for pattern in patterns)

    def _extract_url_from_text(self, text: str) -> Optional[str]:
        """Extract URL from text using regex."""
        # Look for URLs with http/https
        url_pattern = r"https?://[^\s]+"
        match = re.search(url_pattern, text)
        if match:
            return match.group()

        # Look for domain-like patterns
        domain_pattern = r"\b(?:www\.)?[\w\-]+\.[\w]{2,}\b"
        match = re.search(domain_pattern, text)
        if match:
            domain = match.group()
            if not domain.startswith("http"):
                domain = "https://" + domain
            return domain

        return None

    def _extract_query_from_text(self, text: str) -> Optional[str]:
        """Extract search query from command text."""
        # Remove common prefixes
        for prefix in ["search for", "search google", "search"]:
            if text.startswith(prefix):
                query = text[len(prefix) :].strip()
                if query:
                    return query

        # If no prefix match, use entire text
        if text:
            return text

        return None

    def _run_async(self, coro):
        """Run an async coroutine synchronously."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If event loop is already running, use a thread pool
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, coro).result()
            return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop exists, create a new one
            return asyncio.run(coro)

    async def _async_navigate(
        self, browser_service, url: str
    ) -> tuple[bool, str, Optional[str]]:
        """Navigate to a URL asynchronously."""
        try:
            await browser_service.goto(url)
            page_title = await browser_service.get_page_title()
            page_url = await browser_service.get_page_url()
            logger.info(f"Navigated to {page_url}")
            return True, f"Successfully navigated to {page_title or page_url}", page_url
        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            return False, f"Failed to navigate: {str(e)}", None

    async def _async_get_page_text(self, browser_service) -> tuple[bool, str]:
        """Get page text asynchronously."""
        try:
            text = await browser_service.get_page_text()
            return True, text
        except Exception as e:
            logger.error(f"Failed to extract text: {str(e)}")
            return False, f"Failed to extract text: {str(e)}"

    async def _async_get_links(self, browser_service) -> tuple[bool, List[str]]:
        """Get page links asynchronously."""
        try:
            links = await browser_service.get_links()
            return True, links
        except Exception as e:
            logger.error(f"Failed to extract links: {str(e)}")
            return False, []

    async def _async_screenshot(self, browser_service, path: str) -> tuple[bool, str]:
        """Take a screenshot asynchronously."""
        try:
            await browser_service.screenshot(path)
            logger.info(f"Screenshot saved to {path}")
            return True, path
        except Exception as e:
            logger.error(f"Screenshot failed: {str(e)}")
            return False, f"Failed to take screenshot: {str(e)}"

    def _handle_navigate(
        self, ctx: CommandContext, browser_service
    ) -> CommandResult:
        """Handle navigation commands."""
        # Try to get URL from params first
        url = ctx.params.get("url", "") if ctx.params else ""

        # Fall back to extracting from raw text
        if not url:
            url = self._extract_url_from_text(ctx.raw_text)

        if not url:
            return CommandResult(False, "Could not extract URL from command.")

        # Ensure URL has a scheme
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        logger.debug(f"Navigating to: {url}")

        # Run async navigation
        success, message, result_url = self._run_async(
            self._async_navigate(browser_service, url)
        )

        if success:
            return CommandResult(True, message, {"url": result_url})
        else:
            return CommandResult(False, message)

    def _handle_search(
        self, ctx: CommandContext, browser_service
    ) -> CommandResult:
        """Handle search commands."""
        # Try to get query from params first
        query = ctx.params.get("query", "") if ctx.params else ""

        # Fall back to extracting from raw text
        if not query:
            query = self._extract_query_from_text(ctx.raw_text)

        if not query:
            return CommandResult(False, "Could not extract search query from command.")

        logger.debug(f"Searching for: {query}")

        # Build Google search URL
        search_url = f"https://www.google.com/search?q={quote(query)}"

        # Navigate to search results
        success, nav_message, _ = self._run_async(
            self._async_navigate(browser_service, search_url)
        )

        if not success:
            return CommandResult(False, f"Failed to perform search: {nav_message}")

        # Extract and return search results page text
        text_success, text_result = self._run_async(
            self._async_get_page_text(browser_service)
        )

        if text_success:
            return CommandResult(
                True,
                f"Search results for '{query}'",
                {"query": query, "results_text": text_result},
            )
        else:
            return CommandResult(
                True,
                f"Navigated to search results for '{query}' (could not extract text)",
                {"query": query},
            )

    def _handle_extract_text(
        self, ctx: CommandContext, browser_service
    ) -> CommandResult:
        """Handle text extraction from current page."""
        logger.debug("Extracting page text")

        success, result = self._run_async(
            self._async_get_page_text(browser_service)
        )

        if success:
            return CommandResult(
                True, "Successfully extracted page text", {"text": result}
            )
        else:
            return CommandResult(False, result)

    def _handle_extract_links(
        self, ctx: CommandContext, browser_service
    ) -> CommandResult:
        """Handle link extraction from current page."""
        logger.debug("Extracting page links")

        success, links = self._run_async(
            self._async_get_links(browser_service)
        )

        if success:
            return CommandResult(
                True,
                f"Successfully extracted {len(links)} links",
                {"links": links, "count": len(links)},
            )
        else:
            return CommandResult(False, "Failed to extract links")

    def _handle_screenshot(
        self, ctx: CommandContext, browser_service
    ) -> CommandResult:
        """Handle screenshot capture."""
        # Try to get path from params
        path = ctx.params.get("path", "") if ctx.params else ""

        # Default path if not provided
        if not path:
            path = "./screenshot.png"

        logger.debug(f"Taking screenshot to {path}")

        success, result = self._run_async(
            self._async_screenshot(browser_service, path)
        )

        if success:
            return CommandResult(
                True, f"Screenshot saved to {result}", {"path": result}
            )
        else:
            return CommandResult(False, result)
