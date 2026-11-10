"""GitHub repository search tool.

Rules (see tools/README.md + tests/conftest.py):
- Never raise: wrap everything in try/except and return err("search_github_repos", exc).
- Use requests.get/requests.post (module-level) so tests can mock them with fake_http.
- Coerce model input defensively (int("5"), empty string, out-of-range values).
"""
from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err


def search_github_repos(query: str = "", sort: str = "stars", limit: int = 5) -> dict[str, Any]:
    """Tìm repository trên GitHub theo từ khóa (tên, mô tả, số sao, ngôn ngữ, link).

    API: https://api.github.com/search/repositories?q=...&sort=stars&per_page=N (không cần key, giới hạn 10 req/phút; header Accept: application/vnd.github+json)
    Return shape (suggested): {"tool": "search_github_repos", "query": query, "sort": sort, "items": [...]}
    """
    try:
        if not query or not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string")

        try:
            parsed_limit = int(limit)
        except (ValueError, TypeError):
            parsed_limit = 5
        if parsed_limit <= 0:
            parsed_limit = 5
        parsed_limit = min(parsed_limit, 100)

        valid_sorts = {"stars", "updated", "forks", "help-wanted-issues"}
        safe_sort = sort if sort in valid_sorts else "stars"

        headers = {
            "Accept": "application/vnd.github+json",
        }
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        params = {
            "q": query.strip(),
            "sort": safe_sort,
            "per_page": parsed_limit,
        }

        response = requests.get(
            "https://api.github.com/search/repositories",
            params=params,
            headers=headers,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        items = []
        for raw in data.get("items", []):
            items.append({
                "name": raw.get("full_name") or raw.get("name", ""),
                "url": raw.get("html_url", ""),
                "description": raw.get("description") or "",
                "stars": raw.get("stargazers_count", 0),
                "language": raw.get("language") or "",
                "updated_at": raw.get("updated_at", ""),
            })

        return {
            "tool": "search_github_repos",
            "query": query,
            "sort": safe_sort,
            "items": items,
        }
    except Exception as exc:
        return err("search_github_repos", exc)
