"""Hacker News search tool via Algolia API. Owner: thdanhnguyen."""
from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

ALGOLIA_BASE = "https://hn.algolia.com/api/v1"
ALLOWED_SORTS = {"relevance", "date"}


def _coerce_limit(limit: Any, default: int = 5) -> int:
    try:
        val = int(limit)
    except (TypeError, ValueError):
        return default
    if val <= 0:
        return default
    return min(val, 50)


def _hn_item(hit: dict[str, Any]) -> dict[str, Any]:
    object_id = str(hit.get("objectID") or "").strip()
    hn_url = f"https://news.ycombinator.com/item?id={object_id}" if object_id else ""
    url = hit.get("url") or hn_url
    title = str(hit.get("title") or hit.get("story_title") or "").strip()
    points = hit.get("points")
    num_comments = hit.get("num_comments")
    created_at = hit.get("created_at")
    return {
        "title": title,
        "url": url,
        "points": int(points) if isinstance(points, (int, float)) else 0,
        "num_comments": int(num_comments) if isinstance(num_comments, (int, float)) else 0,
        "created_at": created_at,
        "hn_url": hn_url,
    }


def hn_search(query: str = "", sort: str = "relevance", limit: int = 5) -> dict[str, Any]:
    """Tìm story trên Hacker News theo từ khóa (thảo luận cộng đồng dev/tech).

    API: https://hn.algolia.com/api/v1/search?query=...&tags=story&hitsPerPage=N (sort=date -> /search_by_date), không cần key
    Return shape: {"tool": "hn_search", "query": ..., "sort": ..., "limit": ..., "items": [...]}
    """
    try:
        cleaned_query = str(query or "").strip()
        if not cleaned_query:
            raise ValueError("Missing or empty query")

        cleaned_sort = str(sort or "relevance").strip().lower()
        if cleaned_sort not in ALLOWED_SORTS:
            cleaned_sort = "relevance"

        coerced_limit = _coerce_limit(limit, default=5)
        endpoint = f"{ALGOLIA_BASE}/search_by_date" if cleaned_sort == "date" else f"{ALGOLIA_BASE}/search"

        response = requests.get(
            endpoint,
            params={
                "query": cleaned_query,
                "tags": "story",
                "hitsPerPage": coerced_limit,
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Invalid response payload from Hacker News Algolia API")

        raw_hits = data.get("hits") or []
        items = [_hn_item(hit) for hit in raw_hits if isinstance(hit, dict)][:coerced_limit]

        return {
            "tool": "hn_search",
            "query": cleaned_query,
            "sort": cleaned_sort,
            "limit": coerced_limit,
            "items": items,
        }
    except Exception as exc:
        return err("hn_search", exc)
