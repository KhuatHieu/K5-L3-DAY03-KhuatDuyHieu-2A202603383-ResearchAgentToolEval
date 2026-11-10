"""TODO(HViettt): implement calculator.

Rules (see tools/README.md + tests/conftest.py):
- Never raise: wrap everything in try/except and return err("calculate", exc).
- Use requests.get/requests.post (module-level) so tests can mock them with fake_http.
- Coerce model input defensively (int("5"), empty string, out-of-range values).
"""
from __future__ import annotations

from typing import Any

import requests  # noqa: F401

from tools._shared import TIMEOUT, err  # noqa: F401


def calculate(expression: str = "") -> dict[str, Any]:
    """Tính biểu thức số học an toàn (+ - * / ** %, ngoặc, số thập phân) — KHÔNG dùng eval(); parse bằng ast.

    API: local, không gọi mạng (dùng ast.parse + whitelist node)
    Return shape (suggested): {"tool": "calculate", ...input echo..., "items": [...]}
    """
    try:
        raise NotImplementedError("calculator is not implemented yet")
    except Exception as exc:
        return err("calculate", exc)
