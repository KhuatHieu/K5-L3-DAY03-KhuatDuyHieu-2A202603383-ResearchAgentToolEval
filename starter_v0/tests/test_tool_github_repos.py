"""Unit tests for the 'github_repos' tool. Owner: HViettt. Need >= 3 real tests (0 skipped)."""
from __future__ import annotations

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

github_repos = TOOL_FUNCTIONS["github_repos"]


def test_github_repos_sends_expected_request_and_maps_results(fake_http) -> None:
    payload = {
        "items": [
            {
                "full_name": "tiangolo/fastapi",
                "html_url": "https://github.com/tiangolo/fastapi",
                "description": "FastAPI framework",
                "stargazers_count": 75000,
                "language": "Python",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        ]
    }
    calls = fake_http(FakeResponse(payload))
    result = github_repos(query="fastapi", sort="stars", limit=1)

    assert len(calls) == 1
    assert calls[0]["url"] == "https://api.github.com/search/repositories"
    assert calls[0]["params"]["q"] == "fastapi"
    assert calls[0]["params"]["sort"] == "stars"
    assert calls[0]["params"]["per_page"] == 1
    assert calls[0]["headers"]["Accept"] == "application/vnd.github+json"

    assert result["tool"] == "search_github_repos"
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["name"] == "tiangolo/fastapi"
    assert item["url"] == "https://github.com/tiangolo/fastapi"
    assert item["description"] == "FastAPI framework"
    assert item["stars"] == 75000
    assert item["language"] == "Python"
    assert item["updated_at"] == "2024-01-01T00:00:00Z"


def test_github_repos_bad_input_from_model(fake_http) -> None:
    # Query rỗng -> error dict, không gọi mạng
    res_empty = github_repos(query="")
    assert "error" in res_empty
    assert res_empty["tool"] == "search_github_repos"

    res_none = github_repos(query=None)  # type: ignore[arg-type]
    assert "error" in res_none

    # limit là chuỗi hoặc 0 -> coerce thành int hợp lệ
    calls = fake_http(FakeResponse({"items": []}))
    res_coerced = github_repos(query="agent", limit="3")  # type: ignore[arg-type]
    assert "error" not in res_coerced
    assert calls[0]["params"]["per_page"] == 3


def test_github_repos_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=429))
    result = github_repos(query="python")
    assert "error" in result
    assert result["error"] == "HTTPError"
