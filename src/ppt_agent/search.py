from __future__ import annotations

import asyncio
import random
import threading
from urllib.parse import quote_plus, urlparse

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
# Playwright-based browser search (sync API + asyncio.to_thread, Windows-safe)
# ---------------------------------------------------------------------------

_NON_HTML_EXTENSIONS = frozenset([
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp4", ".mp3", ".avi", ".mov", ".zip", ".rar", ".gz",
])

_BING_URL = "https://www.bing.com/search"

_STEALTH_JS = """
() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
}
"""

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

# Per-thread browser instance (sync API, thread-safe)
_thread_local = threading.local()


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


def _get_thread_browser():
    """Get or create a sync Playwright browser for the current thread."""
    if not hasattr(_thread_local, "browser") or _thread_local.browser is None:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        _thread_local.playwright = pw
        _thread_local.browser = pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
    return _thread_local.browser


def _sync_bing_search(query: str, max_entries: int) -> list[dict]:
    """Navigate to Bing, parse SERP entries (sync, runs in thread)."""
    browser = _get_thread_browser()
    context = browser.new_context(
        user_agent=random.choice(_USER_AGENTS),
        locale="zh-CN",
    )
    page = context.new_page()
    try:
        page.add_init_script(_STEALTH_JS)
        encoded_query = quote_plus(query)
        page.goto(
            f"{_BING_URL}?q={encoded_query}&count={max_entries}",
            wait_until="domcontentloaded",
            timeout=15000,
        )
        page.wait_for_selector(".b_algo", timeout=5000)

        entries = []
        elements = page.query_selector_all(".b_algo")
        for el in elements:
            link = el.query_selector("h2 a")
            if not link:
                continue
            title = link.inner_text().strip()
            href = link.get_attribute("href")
            if not title or not href:
                continue
            if not _is_html_url(href):
                continue

            snippet_el = el.query_selector(".b_caption p, .b_lineclamp2")
            snippet = snippet_el.inner_text().strip() if snippet_el else ""

            entries.append({"title": title, "url": href, "snippet": snippet})
            if len(entries) >= max_entries:
                break
        return entries
    except Exception:
        return []
    finally:
        context.close()


def _sync_fetch_page(entry: dict) -> SearchResult | None:
    """Fetch a page and extract main text via trafilatura (sync, runs in thread)."""
    browser = _get_thread_browser()
    context = browser.new_context(
        user_agent=random.choice(_USER_AGENTS),
        locale="zh-CN",
    )
    page = context.new_page()
    try:
        page.add_init_script(_STEALTH_JS)
        page.goto(entry["url"], wait_until="networkidle", timeout=10000)
        html = page.content()
        text = _extract_text(html)

        if len(text) < 200:
            text = entry["snippet"]

        import time
        time.sleep(random.uniform(0.5, 1.5))

        if not text:
            return None
        return SearchResult(title=entry["title"], url=entry["url"], content=text)
    except Exception:
        if entry["snippet"]:
            return SearchResult(title=entry["title"], url=entry["url"], content=entry["snippet"])
        return None
    finally:
        context.close()


class PlaywrightSearchProvider:
    """Search via Playwright-operated browser (Bing).

    Uses sync API + asyncio.to_thread for Windows compatibility.
    Per-thread browser instances via threading.local.
    """

    async def search(self, query: str, max_results: int = 3) -> list[SearchResult]:
        """Search Bing, fetch top results, extract content."""
        # Step 1: search Bing (runs in thread)
        entries = await asyncio.to_thread(_sync_bing_search, query, max_results * 2)
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

        # Step 2: fetch pages concurrently (each in its own thread)
        tasks = [asyncio.to_thread(_sync_fetch_page, e) for e in unique]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for entry, outcome in zip(unique, outcomes):
            if isinstance(outcome, Exception):
                # SERP snippet as fallback
                if entry["snippet"]:
                    results.append(SearchResult(
                        title=entry["title"], url=entry["url"], content=entry["snippet"],
                    ))
            elif outcome is not None:
                results.append(outcome)

        return results


# ---------------------------------------------------------------------------
# Provider factory (cached singleton)
# ---------------------------------------------------------------------------

_cached_provider: SearchProvider | None = None
_cached_provider_key: str = ""


def get_search_provider() -> SearchProvider | None:
    """Return a cached search provider based on config, or None if disabled."""
    global _cached_provider, _cached_provider_key

    provider_key = settings.search_provider.lower()
    if provider_key != _cached_provider_key:
        _cached_provider_key = provider_key
        if provider_key == "tavily" and settings.tavily_api_key:
            _cached_provider = TavilySearchProvider(settings.tavily_api_key)
        elif provider_key == "playwright":
            _cached_provider = PlaywrightSearchProvider()
        else:
            _cached_provider = None

    return _cached_provider


def cleanup_browser_threads():
    """Close browser instances in all threads after research completes."""
    if hasattr(_thread_local, "browser") and _thread_local.browser:
        try:
            _thread_local.browser.close()
        except Exception:
            pass
        _thread_local.browser = None
    if hasattr(_thread_local, "playwright") and _thread_local.playwright:
        try:
            _thread_local.playwright.stop()
        except Exception:
            pass
        _thread_local.playwright = None
