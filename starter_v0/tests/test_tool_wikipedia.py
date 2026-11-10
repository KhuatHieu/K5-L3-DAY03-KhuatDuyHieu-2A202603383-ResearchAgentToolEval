"""Unit tests for the 'wikipedia' tool. Owner: thdanhnguyen. Need >= 3 real tests (0 skipped)."""
from __future__ import annotations

import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

wikipedia = TOOL_FUNCTIONS["wikipedia"]


def test_wikipedia_sends_expected_request_and_maps_results(fake_http) -> None:
    calls = fake_http(
        FakeResponse(
            {
                "title": "Transformer (deep learning architecture)",
                "extract": "A transformer is a deep learning architecture developed by Google.",
                "content_urls": {
                    "desktop": {
                        "page": "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)"
                    }
                },
            }
        )
    )

    result = wikipedia(topic="Transformer (deep learning architecture)", lang="en")

    assert len(calls) == 1
    assert calls[0]["method"] == "GET"
    assert (
        calls[0]["url"]
        == "https://en.wikipedia.org/api/rest_v1/page/summary/Transformer_%28deep_learning_architecture%29"
    )
    assert result["tool"] == "wikipedia_summary"
    assert result["topic"] == "Transformer (deep learning architecture)"
    assert result["lang"] == "en"
    assert result["title"] == "Transformer (deep learning architecture)"
    assert result["summary"] == "A transformer is a deep learning architecture developed by Google."
    assert result["url"] == "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)"


def test_wikipedia_falls_back_to_opensearch_on_404( monkeypatch ) -> None:
    calls = []
    responses = [
        FakeResponse(status_code=404),
        FakeResponse(["Alan Turing", ["Alan Turing"], [""], ["https://en.wikipedia.org/wiki/Alan_Turing"]]),
        FakeResponse(
            {
                "title": "Alan Turing",
                "extract": "Alan Mathison Turing was an English mathematician and computer scientist.",
                "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Alan_Turing"}},
            }
        ),
    ]

    def _fake_get(url: str, **kwargs):
        calls.append({"url": url, **kwargs})
        return responses.pop(0)

    monkeypatch.setattr(requests, "get", _fake_get)

    result = wikipedia(topic="turing machine father", lang="en")

    assert len(calls) == 3
    assert "api/rest_v1/page/summary/turing_machine_father" in calls[0]["url"]
    assert calls[1]["url"] == "https://en.wikipedia.org/w/api.php"
    assert calls[1]["params"]["action"] == "opensearch"
    assert calls[1]["params"]["search"] == "turing machine father"
    assert "api/rest_v1/page/summary/Alan_Turing" in calls[2]["url"]
    assert result["title"] == "Alan Turing"
    assert "computer scientist" in result["summary"]


def test_wikipedia_bad_input_from_model(fake_http) -> None:
    # Empty topic returns error dict without making any HTTP request
    calls = fake_http(FakeResponse({"title": "Unused", "extract": "Unused"}))
    empty_res = wikipedia(topic="   ", lang="en")
    assert "error" in empty_res
    assert empty_res["tool"] == "wikipedia_summary"
    assert calls == []

    # Invalid lang enum falls back to "en" gracefully
    calls_lang = fake_http(
        FakeResponse(
            {
                "title": "Python (programming language)",
                "extract": "Python is a high-level programming language.",
            }
        )
    )
    res_lang = wikipedia(topic="Python", lang="fr-invalid")
    assert res_lang["lang"] == "en"
    assert calls_lang[0]["url"].startswith("https://en.wikipedia.org/api/rest_v1/page/summary/")


def test_wikipedia_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=429))
    result = wikipedia(topic="Artificial intelligence", lang="en")

    assert result["tool"] == "wikipedia_summary"
    assert result["error"] == "HTTPError"
    assert "429" in result["message"]
