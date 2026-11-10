"""Unit tests for the 'calculator' tool. Owner: HViettt. Need >= 3 real tests (0 skipped)."""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401
from tools import TOOL_FUNCTIONS

TODO = "TODO(HViettt): implement this test"
calculator = TOOL_FUNCTIONS["calculator"]


def test_calculator_happy_path() -> None:
    # vd: calculator(expression="(2+3)*4") -> value == 20
    pytest.skip(TODO)


def test_calculator_rejects_unsafe_expression() -> None:
    # vd: "__import__('os')" -> error dict, KHÔNG raise
    pytest.skip(TODO)


def test_calculator_bad_input_returns_error_dict() -> None:
    # vd: "", "1/0", "abc" -> error dict, KHÔNG raise
    pytest.skip(TODO)
