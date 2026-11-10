"""Unit tests for the 'wikipedia' tool. Owner: thdanhnguyen. Need >= 3 real tests (0 skipped)."""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401
from tools import TOOL_FUNCTIONS

TODO = "TODO(thdanhnguyen): implement this test"
wikipedia = TOOL_FUNCTIONS["wikipedia"]


def test_wikipedia_sends_expected_request_and_maps_results(fake_http) -> None:
    # calls = fake_http(FakeResponse({...payload giống API thật...}))
    # assert calls[0]["url"] / params, và assert shape của result
    pytest.skip(TODO)


def test_wikipedia_bad_input_from_model() -> None:
    # vd: query="" , limit="5" (chuỗi), limit=0, enum sai
    pytest.skip(TODO)


def test_wikipedia_http_error_returns_error_dict(fake_http) -> None:
    # fake_http(FakeResponse(status_code=429)) -> result["error"], KHÔNG raise
    pytest.skip(TODO)
