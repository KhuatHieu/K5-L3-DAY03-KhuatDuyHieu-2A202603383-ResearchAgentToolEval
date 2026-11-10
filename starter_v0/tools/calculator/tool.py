"""Calculator tool implemented with AST-based safe evaluation.

Rules (see tools/README.md + tests/conftest.py):
- Never raise: wrap everything in try/except and return err("calculate", exc).
- Coerce model input defensively (int("5"), empty string, out-of-range values).
"""
from __future__ import annotations

import ast
import operator
from typing import Any

from tools._shared import err

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_node(node: ast.AST) -> int | float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value!r}")
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            operand = _eval_node(node.operand)
            return SAFE_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            if op_type is ast.Pow:
                if abs(right) > 1000 or (abs(left) > 1000 and right > 100):
                    raise ValueError("Exponent or base too large")
            return SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
    raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def calculate(expression: str = "") -> dict[str, Any]:
    """Tính biểu thức số học an toàn (+ - * / ** %, ngoặc, số thập phân) — KHÔNG dùng eval(); parse bằng ast."""
    try:
        if not expression or not isinstance(expression, str) or not expression.strip():
            raise ValueError("Expression must be a non-empty string")
        tree = ast.parse(expression.strip(), mode="eval")
        val = _eval_node(tree)
        return {"tool": "calculate", "expression": expression, "value": val}
    except Exception as exc:
        return err("calculate", exc)
