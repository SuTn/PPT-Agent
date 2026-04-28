import pytest

from ppt_agent.search import SearchResult, TavilySearchProvider, get_search_provider
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
        monkeypatch.setattr("ppt_agent.search.settings.search_provider", "")
        monkeypatch.setattr("ppt_agent.search.settings.tavily_api_key", "")
        assert get_search_provider() is None

    def test_returns_none_when_no_key(self, monkeypatch):
        monkeypatch.setattr("ppt_agent.search.settings.search_provider", "tavily")
        monkeypatch.setattr("ppt_agent.search.settings.tavily_api_key", "")
        assert get_search_provider() is None

    def test_returns_tavily_when_configured(self, monkeypatch):
        monkeypatch.setattr("ppt_agent.search.settings.search_provider", "tavily")
        monkeypatch.setattr("ppt_agent.search.settings.tavily_api_key", "tvly-test")
        provider = get_search_provider()
        assert isinstance(provider, TavilySearchProvider)
        assert provider._api_key == "tvly-test"


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
