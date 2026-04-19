"""Libraries.io cross-registry search."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime

from ..config import PROV_WORKERS
from .base import parallel_pages

_PROV_MAP = {
    "pypi": "PyPI",
    "npm": "npm",
    "github": "GitHub",
    "rubygems": "Libraries.io",
    "cargo": "Libraries.io",
    "nuget": "Libraries.io",
    "packagist": "Libraries.io",
}


def _librariesio_page(query: str, pg: int) -> list[dict]:
    q = (query or "").strip()
    if not q:
        return []
    api_url = (
        "https://libraries.io/api/search"
        f"?q={urllib.parse.quote(q)}&page={pg}&per_page=30&sort=created_at"
    )
    try:
        req = urllib.request.Request(
            api_url,
            headers={
                "User-Agent": "PackageWatcher/1.0",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status != 200:
                return []
            data = json.loads(r.read())
    except Exception:
        return []
    out: list[dict] = []
    for item in data:
        name = item.get("name")
        platform = (item.get("platform", "") or "").lower()
        repo = item.get("repository_url", "") or item.get("homepage", "") or ""
        if not name:
            continue
        canon = _PROV_MAP.get(platform, "Libraries.io")
        published = (item.get("latest_release_published_at") or "")[:19]
        out.append(
            {
                "name": name,
                "description": (item.get("description") or "")[:400],
                "url": repo
                or f"https://libraries.io/{platform}/{urllib.parse.quote(name)}",
                "author": item.get("maintainer") or "",
                "published_at": published,
                "version": item.get("latest_release_number") or "",
                "language": item.get("language") or "",
                "_lib_source": canon,
                "_lib_platform": platform,
            }
        )
    return out


def fetch(query: str, max_pages: int = 1, until_dt: datetime | None = None) -> list[dict]:
    return parallel_pages(_librariesio_page, query, max_pages, until_dt, PROV_WORKERS["Libraries.io"])
