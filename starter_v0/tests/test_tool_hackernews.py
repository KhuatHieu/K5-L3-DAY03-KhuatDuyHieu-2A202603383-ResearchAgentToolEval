"""Unit tests for the 'hackernews' tool. Owner: thdanhnguyen. Need >= 3 real tests (0 skipped)."""
from __future__ import annotations

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

hackernews = TOOL_FUNCTIONS["hackernews"]


def test_hackernews_sends_expected_request_and_maps_results(fake_http) -> None:
    calls = fake_http(
        FakeResponse(
            {
                "hits": [
                    {
                        "objectID": "40001234",
                        "title": "Show HN: Fast LLM Eval Harness in Python",
                        "url": "https://example.com/llm-eval",
                        "points": 256,
                        "num_comments": 84,
                        "created_at": "2026-06-01T12:00:00Z",
                    },
                    {
                        "objectID": "40005678",
                        "title": "Ask HN: How do you test agent tool routing?",
                        "url": None,
                        "points": 95,
                        "num_comments": 42,
                        "created_at": "2026-06-02T08:30:00Z",
                    },
                ]
            }
        )
    )

    result = hackernews(query="LLM eval", sort="relevance", limit=3)

    assert len(calls) == 1
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls[0]["params"] == {"query": "LLM eval", "tags": "story", "hitsPerPage": 3}

    assert result["tool"] == "hn_search"
    assert result["query"] == "LLM eval"
    assert result["sort"] == "relevance"
    assert result["limit"] == 3
    assert len(result["items"]) == 2
    assert result["items"][0] == {
        "title": "Show HN: Fast LLM Eval Harness in Python",
        "url": "https://example.com/llm-eval",
        "points": 256,
        "num_comments": 84,
        "created_at": "2026-06-01T12:00:00Z",
        "hn_url": "https://news.ycombinator.com/item?id=40001234",
    }
    # When story has no external URL (Ask HN), url falls back to hn_url
    assert result["items"][1]["url"] == "https://news.ycombinator.com/item?id=40005678"
    assert result["items"][1]["hn_url"] == "https://news.ycombinator.com/item?id=40005678"


def test_hackernews_bad_input_from_model(fake_http) -> None:
    # 1. Empty query returns error dict without making any HTTP request
    calls_empty = fake_http(FakeResponse({"hits": []}))
    res_empty = hackernews(query="   ")
    assert "error" in res_empty
    assert res_empty["tool"] == "hn_search"
    assert calls_empty == []

    # 2. String limit ("7") and sort="date" route to /search_by_date with coerced integer limit
    calls_date = fake_http(FakeResponse({"hits": []}))
    res_date = hackernews(query="Rust", sort="date", limit="7")  # type: ignore[arg-type]
    assert calls_date[0]["url"] == "https://hn.algolia.com/api/v1/search_by_date"
    assert calls_date[0]["params"]["hitsPerPage"] == 7
    assert res_date["limit"] == 7
    assert res_date["sort"] == "date"

    # 3. Non-positive limit (0 or negative) and invalid sort enum fall back to defaults (limit=5, sort="relevance")
    calls_bad = fake_http(FakeResponse({"hits": []}))
    res_bad = hackernews(query="AI", sort="popular_invalid", limit=0)
    assert calls_bad[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls_bad[0]["params"]["hitsPerPage"] == 5
    assert res_bad["limit"] == 5
    assert res_bad["sort"] == "relevance"


def test_hackernews_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=429))
    result = hackernews(query="OpenAI")

    assert result["tool"] == "hn_search"
    assert result["error"] == "HTTPError"
    assert "429" in result["message"]
