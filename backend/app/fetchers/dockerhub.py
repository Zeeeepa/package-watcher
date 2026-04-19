"""DockerHub search via their public v2 search endpoint."""

from __future__ import annotations

import urllib.parse
from datetime import datetime

from ..config import PROV_WORKERS
from ..utils import http_get
from .base import parallel_pages


def _dockerhub_page(query: str, pg: int) -> list[dict]:
    q = (query or "").strip()
    if not q:
        return []
    url = (
        "https://hub.docker.com/v2/search/repositories/"
        f"?query={urllib.parse.quote(q)}&page_size=25&ordering=last_updated&page={pg}"
    )
    try:
        data = http_get(url, timeout=25)
    except Exception:
        return []
    out = []
    for item in data.get("results", []):
        name = item.get("repo_name") or item.get("name")
        if not name:
            continue
        out.append(
            {
                "name": name,
                "description": item.get("short_description", "") or "",
                "url": (
                    f"https://hub.docker.com/r/{name}" if "/" in name else
                    f"https://hub.docker.com/_/{name}"
                ),
                "author": item.get("repo_owner", "") or "",
                "published_at": item.get("last_updated", "") or "",
                "language": "Dockerfile",
            }
        )
    return out


def fetch(query: str, max_pages: int = 1, until_dt: datetime | None = None) -> list[dict]:
    return parallel_pages(_dockerhub_page, query, max_pages, until_dt, PROV_WORKERS["DockerHub"])
