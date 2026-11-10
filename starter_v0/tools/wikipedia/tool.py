"""TODO(thdanhnguyen): implement wikipedia.

Rules (see tools/README.md + tests/conftest.py):
- Never raise: wrap everything in try/except and return err("wikipedia_summary", exc).
- Use requests.get/requests.post (module-level) so tests can mock them with fake_http.
- Coerce model input defensively (int("5"), empty string, out-of-range values).
"""
from __future__ import annotations

from typing import Any

import requests  # noqa: F401

from tools._shared import TIMEOUT, err  # noqa: F401


def wikipedia_summary(topic: str = "", lang: str = "en") -> dict[str, Any]:
    """Lấy tóm tắt bách khoa (định nghĩa, background) của một khái niệm/người/tổ chức từ Wikipedia.

    API: https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title} (không cần key). Fallback: https://{lang}.wikipedia.org/w/api.php?action=opensearch&search=...
    Return shape (suggested): {"tool": "wikipedia_summary", ...input echo..., "items": [...]}
    """
    try:
        raise NotImplementedError("wikipedia is not implemented yet")
    except Exception as exc:
        return err("wikipedia_summary", exc)
