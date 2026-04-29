import pytest

from ppt_agent.search import (
    SearchResult,
    TavilySearchProvider,
    PlaywrightSearchProvider,
    get_search_provider,
    _is_html_url,
    _extract_domain,
    _extract_text,
    _sync_bing_search,
    _extract_text as _orig_extract_text,
)
from ppt_agent.prompts.research import _search_results_section


class TestSearchResult:
    def test_search_result_model(self):
        r = SearchResult(title="Test", url="https://example.com", content="Hello")
        assert r.title == "Test"
        assert r.url == "https://example.com"
        assert r.content == "Hello"


class TestSearchResultsSection:
    def test_empty_results(self):
        assert _search_results_section([]) == ""

    def test_formats_results(self):
        results = [
            SearchResult(title="AI Trends", url="https://a.com", content="AI is growing fast."),
            SearchResult(title="Data Report", url="https://b.com", content="Numbers show 42%."),
        ]
        section = _search_results_section(results)
        assert "AI Trends" in section
        assert "https://a.com" in section
        assert "Data Report" in section
        assert "网络搜索结果" in section

    def test_truncates_long_content(self):
        results = [SearchResult(title="T", url="https://x.com", content="x" * 1000)]
        section = _search_results_section(results)
        # content should be truncated to 500 chars in the section
        assert "x" * 500 in section


class TestGetSearchProvider:
    def test_returns_none_when_not_configured(self, monkeypatch):
        import ppt_agent.search as mod
        monkeypatch.setattr("ppt_agent.search.settings.search_provider", "")
        monkeypatch.setattr("ppt_agent.search.settings.tavily_api_key", "")
        mod._cached_provider_key = "__reset__"  # invalidate cache
        assert get_search_provider() is None

    def test_returns_none_when_no_key(self, monkeypatch):
        import ppt_agent.search as mod
        monkeypatch.setattr("ppt_agent.search.settings.search_provider", "tavily")
        monkeypatch.setattr("ppt_agent.search.settings.tavily_api_key", "")
        mod._cached_provider_key = "__reset__"
        assert get_search_provider() is None

    def test_returns_tavily_when_configured(self, monkeypatch):
        import ppt_agent.search as mod
        monkeypatch.setattr("ppt_agent.search.settings.search_provider", "tavily")
        monkeypatch.setattr("ppt_agent.search.settings.tavily_api_key", "tvly-test")
        mod._cached_provider_key = "__reset__"
        provider = get_search_provider()
        assert isinstance(provider, TavilySearchProvider)
        assert provider._api_key == "tvly-test"

    def test_returns_playwright_when_configured(self, monkeypatch):
        import ppt_agent.search as mod
        monkeypatch.setattr("ppt_agent.search.settings.search_provider", "playwright")
        mod._cached_provider_key = "__reset__"
        provider = get_search_provider()
        assert isinstance(provider, PlaywrightSearchProvider)

    def test_caches_provider_instance(self, monkeypatch):
        import ppt_agent.search as mod
        monkeypatch.setattr("ppt_agent.search.settings.search_provider", "tavily")
        monkeypatch.setattr("ppt_agent.search.settings.tavily_api_key", "tvly-test")
        mod._cached_provider_key = "__reset__"
        p1 = get_search_provider()
        p2 = get_search_provider()
        assert p1 is p2  # same instance


class TestTavilySearchProvider:
    @pytest.mark.asyncio
    async def test_search_parses_response(self, monkeypatch):
        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "results": [
                        {"title": "Result 1", "url": "https://a.com", "content": "Content 1"},
                        {"title": "Result 2", "url": "https://b.com", "content": "Content 2"},
                    ]
                }

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None):
                self.last_url = url
                self.last_json = json
                return FakeResponse()

        fake = FakeClient()
        monkeypatch.setattr("ppt_agent.search.httpx.AsyncClient", lambda **kw: fake)

        provider = TavilySearchProvider("tvly-test")
        results = await provider.search("test query", max_results=3)

        assert len(results) == 2
        assert results[0].title == "Result 1"
        assert results[1].url == "https://b.com"
        assert fake.last_json["query"] == "test query"
        assert fake.last_json["max_results"] == 3


class TestHelpers:
    def test_is_html_url(self):
        assert _is_html_url("https://example.com/page") is True
        assert _is_html_url("https://example.com/page.html") is True
        assert _is_html_url("https://example.com/file.pdf") is False
        assert _is_html_url("https://example.com/file.xlsx") is False
        assert _is_html_url("https://example.com/video.mp4") is False

    def test_extract_domain(self):
        assert _extract_domain("https://www.example.com/path") == "www.example.com"
        assert _extract_domain("https://example.com") == "example.com"
        assert _extract_domain("https://sub.domain.com/q") == "sub.domain.com"

    def test_extract_text(self):
        html = "<html><body><article>" + "Main content. " * 50 + "</article></body></html>"
        text = _extract_text(html)
        assert "Main content" in text
        assert len(text) > 100

    def test_extract_text_empty(self):
        text = _extract_text("<html><body></body></html>")
        assert text == ""

    def test_extract_text_truncation(self):
        html = "<html><body><article>" + "Word " * 10000 + "</article></body></html>"
        text = _extract_text(html, max_chars=2000)
        assert len(text) <= 2000
