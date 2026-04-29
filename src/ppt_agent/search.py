from __future__ import annotations

import asyncio
import random
import re
from collections import OrderedDict
from urllib.parse import urlparse

import httpx
import trafilatura
from pydantic import BaseModel
from typing import Protocol

from ppt_agent.config import settings


class SearchResult(BaseModel):
    title: str
    url: str
    content: str


class SearchProvider(Protocol):
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]: ...


class TavilySearchProvider:
    """Search via Tavily REST API (httpx, no extra SDK)."""

    def __init__(self, api_key: str):
        self._api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self._api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for r in data.get("results", []):
            results.append(SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
            ))
        return results


# ---------------------------------------------------------------------------
# Playwright-based browser search
# ---------------------------------------------------------------------------

_NON_HTML_EXTENSIONS = frozenset([
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp4", ".mp3", ".avi", ".mov", ".zip", ".rar", ".gz",
])

_BING_URL = "https://www.bing.com/search"

_STEALTH_JS = """
() => {
    // Remove webdriver flag
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    // Override plugins to look like a real browser
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    // Override languages
    Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
}
"""

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]


def _is_html_url(url: str) -> bool:
    """Skip non-HTML resources based on URL path extension."""
    path = urlparse(url).path.lower()
    return not any(path.endswith(ext) for ext in _NON_HTML_EXTENSIONS)


def _extract_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def _extract_text(html: str, max_chars: int = 2000) -> str:
    """Extract main text from HTML using trafilatura."""
    text = trafilatura.extract(html)
    if not text:
        return ""
    if len(text) > max_chars:
        text = text[:max_chars]
    return text


class PlaywrightSearchProvider:
    """Search via Playwright-operated browser (Bing).

    Shares a single browser instance across concurrent calls.
    Lifecycle: lazy init on first search, explicit close via aclose().
    """

    def __init__(self):
        self._browser = None
        self._playwright = None
        self._lock = asyncio.Lock()

    async def _ensure_browser(self):
        """Lazy-start browser with stealth. Protected by lock."""
        if self._browser:
            return
        async with self._lock:
            if self._browser:
                return
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )

    async def aclose(self):
        """Close browser and playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def search(self, query: str, max_results: int = 3) -> list[SearchResult]:
        """Search Bing, fetch top results, extract content."""
        await self._ensure_browser()

        # Step 1: search Bing, extract SERP entries
        entries = await self._search_bing(query, max_results)
        if not entries:
            return []

        # Deduplicate by domain
        seen_domains = set()
        unique = []
        for e in entries:
            domain = _extract_domain(e["url"])
            if domain not in seen_domains:
                seen_domains.add(domain)
                unique.append(e)
        unique = unique[:max_results]

        # Step 2: fetch pages and extract content (concurrent)
        results = []
        tasks = [self._fetch_page(e) for e in unique]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)

        for entry, outcome in zip(unique, outcomes):
            if isinstance(outcome, Exception):
                # SERP snippet as fallback
                results.append(SearchResult(
                    title=entry["title"], url=entry["url"], content=entry["snippet"],
                ))
            else:
                results.append(outcome)

        return results

    async def _search_bing(self, query: str, max_results: int) -> list[dict]:
        """Navigate to Bing, parse SERP entries."""
        context = await self._browser.new_context(
            user_agent=random.choice(_USER_AGENTS),
            locale="zh-CN",
        )
        page = await context.new_page()
        try:
            await page.add_init_script(_STEALTH_JS)
            await page.goto(
                f"{_BING_URL}?q={query}&count={max_results * 2}",
                wait_until="domcontentloaded",
                timeout=15000,
            )
            # Wait for results to render
            await page.wait_for_selector(".b_algo", timeout=5000)

            entries = []
            elements = await page.query_selector_all(".b_algo")
            for el in elements:
                link = await el.query_selector("h2 a")
                if not link:
                    continue
                title = (await link.inner_text()).strip()
                href = await link.get_attribute("href")
                if not title or not href:
                    continue
                if not _is_html_url(href):
                    continue

                snippet_el = await el.query_selector(".b_caption p, .b_lineclamp2")
                snippet = ""
                if snippet_el:
                    snippet = (await snippet_el.inner_text()).strip()

                entries.append({"title": title, "url": href, "snippet": snippet})
                if len(entries) >= max_results * 2:
                    break
            return entries
        except Exception:
            return []
        finally:
            await context.close()

    async def _fetch_page(self, entry: dict) -> SearchResult | None:
        """Fetch a page and extract main text via trafilatura."""
        context = await self._browser.new_context(
            user_agent=random.choice(_USER_AGENTS),
            locale="zh-CN",
        )
        page = await context.new_page()
        try:
            await page.add_init_script(_STEALTH_JS)
            await page.goto(
                entry["url"],
                wait_until="networkidle",
                timeout=10000,
            )
            html = await page.content()
            text = _extract_text(html)

            # If extraction failed or too short, use SERP snippet
            if len(text) < 200:
                text = entry["snippet"]

            # Small random delay to avoid looking like a bot
            await asyncio.sleep(random.uniform(0.5, 1.5))

            if not text:
                return None

            return SearchResult(title=entry["title"], url=entry["url"], content=text)
        except Exception:
            # Fallback to SERP snippet
            if entry["snippet"]:
                return SearchResult(
                    title=entry["title"], url=entry["url"], content=entry["snippet"],
                )
            return None
        finally:
            await context.close()


def get_search_provider() -> SearchProvider | None:
    """Return a search provider based on config, or None if search is disabled."""
    provider = settings.search_provider.lower()
    if provider == "tavily" and settings.tavily_api_key:
        return TavilySearchProvider(settings.tavily_api_key)
    if provider == "playwright":
        return PlaywrightSearchProvider()
    return None
