"""Wikipedia summary tool. Owner: thdanhnguyen."""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

USER_AGENT = "AI20k-Day03-Research-Agent/1.0 (educational lab; contact: local)"
ALLOWED_LANGS = {"en", "vi"}


def _summary_url(lang: str, title: str) -> str:
    encoded = quote(title.strip().replace(" ", "_"), safe="")
    return f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"


def _extract_summary(data: dict[str, Any], fallback_title: str, lang: str) -> tuple[str, str, str]:
    title = str(data.get("title") or fallback_title)
    summary = str(data.get("extract") or data.get("description") or "").strip()
    url = (
        ((data.get("content_urls") or {}).get("desktop") or {}).get("page")
        or f"https://{lang}.wikipedia.org/wiki/{quote(title.replace(' ', '_'), safe='')}"
    )
    return title, summary, str(url)


def wikipedia_summary(topic: str = "", lang: str = "en") -> dict[str, Any]:
    """Lấy tóm tắt bách khoa (định nghĩa, background) của một khái niệm/người/tổ chức từ Wikipedia.

    API: https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title} (không cần key).
    Fallback: https://{lang}.wikipedia.org/w/api.php?action=opensearch&search=...
    Return shape: {"tool": "wikipedia_summary", "topic": ..., "lang": ..., "title": ..., "summary": ..., "url": ...}
    """
    try:
        cleaned_topic = str(topic or "").strip()
        if not cleaned_topic:
            raise ValueError("Missing or empty topic")

        cleaned_lang = str(lang or "en").strip().lower()
        if cleaned_lang not in ALLOWED_LANGS:
            cleaned_lang = "en"

        headers = {"User-Agent": USER_AGENT}
        response = requests.get(
            _summary_url(cleaned_lang, cleaned_topic),
            headers=headers,
            timeout=TIMEOUT,
        )

        if response.status_code == 404:
            search_resp = requests.get(
                f"https://{cleaned_lang}.wikipedia.org/w/api.php",
                params={
                    "action": "opensearch",
                    "search": cleaned_topic,
                    "limit": 1,
                    "namespace": 0,
                    "format": "json",
                },
                headers=headers,
                timeout=TIMEOUT,
            )
            search_resp.raise_for_status()
            search_data = search_resp.json()
            titles = search_data[1] if isinstance(search_data, list) and len(search_data) > 1 else []
            if not titles:
                raise LookupError(f"No Wikipedia article found for '{cleaned_topic}'")

            best_title = str(titles[0])
            response = requests.get(
                _summary_url(cleaned_lang, best_title),
                headers=headers,
                timeout=TIMEOUT,
            )

        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Invalid response payload from Wikipedia API")

        title, summary, url = _extract_summary(data, cleaned_topic, cleaned_lang)
        return {
            "tool": "wikipedia_summary",
            "topic": cleaned_topic,
            "lang": cleaned_lang,
            "title": title,
            "summary": summary,
            "url": url,
            "items": [
                {
                    "title": title,
                    "url": url,
                    "source": f"{cleaned_lang}.wikipedia.org",
                    "summary": summary,
                }
            ],
        }
    except Exception as exc:
        return err("wikipedia_summary", exc)
