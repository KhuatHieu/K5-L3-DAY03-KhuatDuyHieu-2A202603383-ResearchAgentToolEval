"""Unit tests for the 'calculator' tool. Owner: HViettt. Need >= 3 real tests (0 skipped)."""
from __future__ import annotations

from tools import TOOL_FUNCTIONS

calculator = TOOL_FUNCTIONS["calculator"]


def test_calculator_happy_path() -> None:
    res = calculator(expression="(2+3)*4")
    assert res["tool"] == "calculate"
    assert res["value"] == 20
    assert res["expression"] == "(2+3)*4"

    res_float = calculator(expression="10 / 4 + 2**3")
    assert res_float["value"] == 10.5


def test_calculator_rejects_unsafe_expression() -> None:
    res = calculator(expression="__import__('os').system('dir')")
    assert "error" in res
    assert res["tool"] == "calculate"

    res_call = calculator(expression="abs(-5)")
    assert "error" in res_call

    res_attr = calculator(expression="[].__class__")
    assert "error" in res_attr


def test_calculator_bad_input_returns_error_dict() -> None:
    assert "error" in calculator(expression="")
    res_div = calculator(expression="1 / 0")
    assert "error" in res_div
    assert res_div["error"] == "ZeroDivisionError"

    assert "error" in calculator(expression="abc + 5")
    assert "error" in calculator(expression=None)  # type: ignore[arg-type]
