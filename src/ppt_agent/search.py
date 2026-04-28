from __future__ import annotations

from typing import Protocol

import httpx
from pydantic import BaseModel

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


def get_search_provider() -> SearchProvider | None:
    """Return a search provider based on config, or None if search is disabled."""
    provider = settings.search_provider.lower()
    if provider == "tavily" and settings.tavily_api_key:
        return TavilySearchProvider(settings.tavily_api_key)
    return None
