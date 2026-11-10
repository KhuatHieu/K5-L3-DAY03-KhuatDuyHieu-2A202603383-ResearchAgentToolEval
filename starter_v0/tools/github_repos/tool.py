"""TODO(HViettt): implement github_repos.

Rules (see tools/README.md + tests/conftest.py):
- Never raise: wrap everything in try/except and return err("search_github_repos", exc).
- Use requests.get/requests.post (module-level) so tests can mock them with fake_http.
- Coerce model input defensively (int("5"), empty string, out-of-range values).
"""
from __future__ import annotations

from typing import Any

import requests  # noqa: F401

from tools._shared import TIMEOUT, err  # noqa: F401


def search_github_repos(query: str = "", sort: str = "stars", limit: int = 5) -> dict[str, Any]:
    """Tìm repository trên GitHub theo từ khóa (tên, mô tả, số sao, ngôn ngữ, link).

    API: https://api.github.com/search/repositories?q=...&sort=stars&per_page=N (không cần key, giới hạn 10 req/phút; header Accept: application/vnd.github+json)
    Return shape (suggested): {"tool": "search_github_repos", ...input echo..., "items": [...]}
    """
    try:
        raise NotImplementedError("github_repos is not implemented yet")
    except Exception as exc:
        return err("search_github_repos", exc)
