"""TODO(thdanhnguyen): implement hackernews.

Rules (see tools/README.md + tests/conftest.py):
- Never raise: wrap everything in try/except and return err("hn_search", exc).
- Use requests.get/requests.post (module-level) so tests can mock them with fake_http.
- Coerce model input defensively (int("5"), empty string, out-of-range values).
"""
from __future__ import annotations

from typing import Any

import requests  # noqa: F401

from tools._shared import TIMEOUT, err  # noqa: F401


def hn_search(query: str = "", sort: str = "relevance", limit: int = 5) -> dict[str, Any]:
    """Tìm story trên Hacker News theo từ khóa (thảo luận cộng đồng dev/tech).

    API: https://hn.algolia.com/api/v1/search?query=...&tags=story&hitsPerPage=N (sort=date -> /search_by_date), không cần key
    Return shape (suggested): {"tool": "hn_search", ...input echo..., "items": [...]}
    """
    try:
        raise NotImplementedError("hackernews is not implemented yet")
    except Exception as exc:
        return err("hn_search", exc)
