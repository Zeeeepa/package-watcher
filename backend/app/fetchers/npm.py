"""npm search using the official registry search JSON API."""

from __future__ import annotations

import urllib.parse
from datetime import datetime

from ..config import PROV_WORKERS
from ..utils import http_get
from .base import parallel_pages

_PAGE_SIZE = 50


def _npm_page(query: str, pg: int) -> list[dict]:
    q = (query or "").strip()
    if not q:
        return []
    offset = (pg - 1) * _PAGE_SIZE
    url = (
        "https://registry.npmjs.org/-/v1/search"
        f"?text={urllib.parse.quote(q)}&size={_PAGE_SIZE}&from={offset}"
    )
    try:
        data = http_get(url, timeout=25)
    except Exception:
        return []
    out: list[dict] = []
    for obj in data.get("objects", []):
        pkg = obj.get("package", {}) or {}
        name = (pkg.get("name") or "").strip()
        if not name:
            continue
        publisher = pkg.get("publisher") or pkg.get("author") or {}
        author = (
            publisher.get("name")
            if isinstance(publisher, dict)
            else str(publisher or "")
        )
        out.append(
            {
                "name": name,
                "description": pkg.get("description", "") or "",
                "version": pkg.get("version", "") or "",
                "url": (pkg.get("links") or {}).get("npm")
                or f"https://www.npmjs.com/package/{name}",
                "author": author,
                "published_at": pkg.get("date", "") or "",
                "language": "JavaScript",
            }
        )
    return out


def fetch(query: str, max_pages: int = 1, until_dt: datetime | None = None) -> list[dict]:
    return parallel_pages(_npm_page, query, max_pages, until_dt, PROV_WORKERS["npm"])
