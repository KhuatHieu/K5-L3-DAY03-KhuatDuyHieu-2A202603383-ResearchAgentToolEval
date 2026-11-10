"""TODO(student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

clarify_tool = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send_tool = TOOL_FUNCTIONS["send"]
lookup_tool = TOOL_FUNCTIONS["lookup"]
fetch_tool = TOOL_FUNCTIONS["fetch"]
timeline_tool = TOOL_FUNCTIONS["timeline"]
social_search_tool = TOOL_FUNCTIONS["social_search"]
policy_tool = TOOL_FUNCTIONS["policy"]
calculator_tool = TOOL_FUNCTIONS["calculator"]
github_repos_tool = TOOL_FUNCTIONS["github_repos"]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    res = clarify_tool(question="Bạn muốn chọn phương án nào?", response_type="choice", options=["Phương án 1", "Phương án 2"])
    assert res["options"] == ["Phương án 1", "Phương án 2"]
    assert res["awaiting_user"] is True
    assert res["response_type"] == "choice"
    assert res["question"] == "Bạn muốn chọn phương án nào?"


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "Item 1", "section": "A"},
        {"title": "Item 2", "section": "B"},
        {"title": "Item 3", "section": "A"},
    ]
    res = format_tool(items=items, template="sections")
    assert res["markdown"].count("## A") == 1
    assert res["markdown"].count("## B") == 1
    assert res["item_count"] == 3


def test_format_thread_numbers_items() -> None:
    items = [
        {"title": "First post"},
        {"title": "Second post"},
        {"title": "Third post"},
    ]
    res = format_tool(items=items, template="thread")
    lines = [p for p in res["markdown"].split("\n\n") if p.strip()]
    assert len(lines) == 3
    assert lines[0].startswith("1/ ")
    assert lines[1].startswith("2/ ")
    assert lines[2].startswith("3/ ")


def test_format_empty_items_does_not_crash() -> None:
    res_none = format_tool(items=None)
    assert res_none["item_count"] == 0
    assert res_none["markdown"] == ""

    res_empty = format_tool(items=[])
    assert res_empty["item_count"] == 0
    assert res_empty["markdown"] == ""


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake_bot_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")
    calls = fake_http(FakeResponse({"ok": True}))

    res = send_tool(text="Bản tin công nghệ", confirmed=True)

    assert len(calls) == 1
    assert "fake_bot_token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "123456789"
    assert calls[0]["json"]["text"] == "Bản tin công nghệ"
    assert res["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    res = send_tool(text="Bản tin", confirmed=True)

    assert "error" in res
    assert res["error"] == "RuntimeError"
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "mock_key")
    calls = fake_http(FakeResponse({"results": []}))

    res = lookup_tool(query="LangChain", timeframe=None)

    assert len(calls) == 1
    assert "time_range" not in calls[0]["json"]
    assert res["timeframe"] is None


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "mock_key")
    fake_http(FakeResponse({
        "data": {
            "markdown": "# Tiêu đề\nNội dung chi tiết",
            "metadata": {"title": "T", "sourceURL": "https://example.com/research"},
        }
    }))

    res = fetch_tool(url="https://example.com/research")

    assert res["tool"] == "read_url"
    assert len(res["items"]) == 1
    item = res["items"][0]
    assert item["title"] == "T"
    assert item["url"] == "https://example.com/research"
    assert item["source"] == "example.com"
    assert item["summary"] == "# Tiêu đề\nNội dung chi tiết"


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "mock_key")
    long_markdown = "A" * 6000
    fake_http(FakeResponse({
        "data": {
            "markdown": long_markdown,
            "metadata": {"title": "Long page"},
        }
    }))

    res = fetch_tool(url="https://example.com/long")
    assert len(res["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "mock_key")
    raw_timeline = [
        {"tweet_id": None, "text": "invalid tweet without id"},
        *[{"tweet_id": f"t_{i}", "screen_name": "sama", "text": f"Tweet #{i}"} for i in range(6)],
    ]
    fake_http(FakeResponse({"timeline": raw_timeline}))

    res = timeline_tool(screenname="sama", limit=3)

    assert len(res["items"]) == 3
    for i, item in enumerate(res["items"]):
        assert item["url"] == f"https://x.com/sama/status/t_{i}"
        assert item["source"] == "@sama"


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "mock_key")
    calls = fake_http(FakeResponse({"timeline": []}))

    social_search_tool(query="DeepSeek", search_type="Top")

    assert len(calls) == 1
    assert calls[0]["params"]["query"] == "DeepSeek"
    assert calls[0]["params"]["search_type"] == "Top"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    res = policy_tool(query="")
    assert res["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    res = policy_tool(query="privacy data personal", policy_area="data_privacy")
    assert len(res["results"]) > 0
    for hit in res["results"]:
        assert hit["policy_area"] == "data_privacy"


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    res = policy_tool(query="citation policy probe", policy_area="source_citation")
    injection_hits = [hit for hit in res["results"] if hit["section"] == "Injection probe"]
    assert len(injection_hits) > 0
    probe = injection_hits[0]
    assert any("ignore the citation policy" in line for line in probe["untrusted_text"])
    assert "ignore the citation policy" not in probe["facts"]


# ---------------- YOUR NEW TOOL(S) ----------------

def test_my_new_tool_happy_path() -> None:
    res = calculator_tool(expression="(12 + 8) * 3 / 2")
    assert res["tool"] == "calculate"
    assert res["value"] == 30.0
    assert res["expression"] == "(12 + 8) * 3 / 2"


def test_my_new_tool_bad_input_from_model() -> None:
    res_div0 = calculator_tool(expression="50 / 0")
    assert "error" in res_div0
    assert res_div0["error"] == "ZeroDivisionError"

    res_empty = calculator_tool(expression="")
    assert "error" in res_empty


def test_my_new_tool_failure_returns_error_dict() -> None:
    res_unsafe = calculator_tool(expression="__import__('os').system('ls')")
    assert "error" in res_unsafe
    assert res_unsafe["tool"] == "calculate"

    res_invalid_syntax = calculator_tool(expression="2 +* 3")
    assert "error" in res_invalid_syntax
    assert res_invalid_syntax["tool"] == "calculate"
