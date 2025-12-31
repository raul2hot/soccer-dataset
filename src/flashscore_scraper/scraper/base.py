"""Base scraper classes with tls_client and Playwright support."""

import asyncio
import logging
import random
from typing import Optional, Any
from abc import ABC

try:
    from playwright.async_api import async_playwright, Page, BrowserContext

    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("⚠️  Playwright not installed. Install with: playwright install chromium")

try:
    import tls_client
    from bs4 import BeautifulSoup

    HAS_TLS_CLIENT = True
except ImportError:
    HAS_TLS_CLIENT = False
    print("⚠️  tls_client or beautifulsoup4 not installed")

from ..constants import USER_AGENTS, TLS_CLIENT_HEADERS, DEFAULT_TIMEOUT
from ..utils.retry import with_retry


class TLSClientScraper(ABC):
    """
    Base scraper using tls_client for direct HTTP requests.

    Better for:
    - Simple page fetches
    - API-like endpoints
    - Bypassing Cloudflare
    - Lower resource usage
    """

    def __init__(
        self,
        proxy_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize TLS client scraper.

        Args:
            proxy_url: Proxy URL (e.g., http://user:pass@host:port)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        if not HAS_TLS_CLIENT:
            raise ImportError("tls_client is required. Install with: pip install tls-client")

        self.proxy_url = proxy_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(self.__class__.__name__)

        # Create TLS session
        self.session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_extension_order=True,
        )

        # Set headers
        self.session.headers.update(TLS_CLIENT_HEADERS)
        self.session.headers["User-Agent"] = random.choice(USER_AGENTS)

        # Set proxy if provided
        if self.proxy_url:
            self.session.proxies = {
                "http": self.proxy_url,
                "https": self.proxy_url,
            }
            self.logger.info(f"Using proxy: {self.proxy_url.split('@')[-1]}")

    @with_retry(max_attempts=3)
    async def fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from URL.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string

        Raises:
            Exception: If request fails after retries
        """
        self.logger.debug(f"Fetching: {url}")

        # Run sync request in executor to not block async loop
        # Note: tls_client doesn't support timeout parameter directly
        # We use asyncio.wait_for to handle timeout at the async level
        loop = asyncio.get_event_loop()

        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: self.session.get(url)),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request to {url} timed out after {self.timeout}s")

        if response.status_code not in [200, 301, 302]:
            raise Exception(f"HTTP {response.status_code} for {url}")

        return response.text

    async def fetch_soup(self, url: str) -> "BeautifulSoup":
        """
        Fetch URL and return BeautifulSoup object.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object
        """
        html = await self.fetch_html(url)
        return BeautifulSoup(html, "lxml")

    async def random_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """
        Add random delay to avoid rate limiting.

        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)

    async def close(self):
        """Close session."""
        # tls_client sessions don't need explicit closing
        pass


class BaseScraper(ABC):
    """
    Base scraper using Playwright for browser automation.

    Better for:
    - JavaScript-heavy pages
    - Dynamic content loading
    - Button clicks and interactions
    - Screenshot debugging
    """

    def __init__(
        self,
        headless: bool = True,
        proxy_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
    ):
        """
        Initialize Playwright scraper.

        Args:
            headless: Run browser in headless mode
            proxy_url: Proxy URL
            timeout: Timeout in milliseconds
            max_retries: Maximum retry attempts
        """
        if not HAS_PLAYWRIGHT:
            raise ImportError(
                "Playwright is required. Install with: "
                "pip install playwright && playwright install chromium"
            )

        self.headless = headless
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(self.__class__.__name__)

    async def create_context(self) -> tuple:
        """
        Create browser and context.

        Returns:
            Tuple of (playwright, browser, context)
        """
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=self.headless)

        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": random.choice(USER_AGENTS),
        }

        # Add proxy if configured
        if self.proxy_url:
            context_options["proxy"] = {"server": self.proxy_url}
            self.logger.info(f"Using proxy: {self.proxy_url.split('@')[-1]}")

        context = await browser.new_context(**context_options)
        return playwright, browser, context

    @with_retry(max_attempts=3)
    async def safe_goto(self, page: Page, url: str, wait_until: str = "domcontentloaded"):
        """
        Navigate to URL with retry logic.

        Args:
            page: Playwright page
            url: URL to navigate to
            wait_until: Wait condition (domcontentloaded, load, networkidle)
        """
        self.logger.debug(f"Navigating to: {url}")
        await page.goto(url, wait_until=wait_until, timeout=self.timeout)

    async def safe_click(self, page: Page, selector: str, timeout: int = 5000) -> bool:
        """
        Click element if exists.

        Args:
            page: Playwright page
            selector: CSS selector
            timeout: Timeout in milliseconds

        Returns:
            True if clicked, False if element not found
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            await page.click(selector)
            return True
        except Exception as e:
            self.logger.debug(f"Click failed for {selector}: {e}")
            return False

    async def safe_get_text(self, page: Page, selector: str, timeout: int = 5000) -> Optional[str]:
        """
        Get text content safely.

        Args:
            page: Playwright page
            selector: CSS selector
            timeout: Timeout in milliseconds

        Returns:
            Text content or None if not found
        """
        try:
            element = await page.wait_for_selector(selector, timeout=timeout)
            if element:
                text = await element.text_content()
                return text.strip() if text else None
        except Exception as e:
            self.logger.debug(f"Text extraction failed for {selector}: {e}")
        return None

    async def scroll_and_load_all(
        self,
        page: Page,
        load_more_selector: str,
        item_selector: str,
        max_clicks: int = 50,
        max_empty_cycles: int = 3,
    ) -> int:
        """
        Repeatedly click 'load more' until all items are loaded.

        Args:
            page: Playwright page
            load_more_selector: CSS selector for load more button
            item_selector: CSS selector for items to count
            max_clicks: Maximum number of clicks
            max_empty_cycles: Stop after N consecutive cycles with no new items

        Returns:
            Total count of items loaded
        """
        empty_cycles = 0
        clicks = 0

        while clicks < max_clicks:
            count_before = len(await page.query_selector_all(item_selector))

            # Try to find and click load more button
            load_more = await page.query_selector(load_more_selector)
            if not load_more:
                self.logger.debug("Load more button not found")
                break

            try:
                await load_more.click()
                await page.wait_for_timeout(800)
                clicks += 1
            except Exception as e:
                self.logger.debug(f"Load more click failed: {e}")
                break

            count_after = len(await page.query_selector_all(item_selector))

            if count_after == count_before:
                empty_cycles += 1
                self.logger.debug(
                    f"No new items loaded ({empty_cycles}/{max_empty_cycles})"
                )
                if empty_cycles >= max_empty_cycles:
                    break
            else:
                empty_cycles = 0
                self.logger.debug(f"Loaded {count_after - count_before} new items")

        total = len(await page.query_selector_all(item_selector))
        return total

    async def random_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """
        Add random delay.

        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
