"""GitHub search.

Uses the unauthenticated Search API for reliable JSON results.
Falls back to an HTML scrape of /search (may be rate-limited).
"""

from __future__ import annotations

import re
import urllib.parse
import urllib.request
from datetime import datetime

from ..config import PROV_WORKERS
from ..utils import http_get
from .base import parallel_pages

_SKIP = {
    "search", "explore", "trending", "topics", "collections", "marketplace",
    "login", "signup", "about", "contact", "pricing", "features",
    "enterprise", "security", "opensource", "sponsors", "settings",
    "notifications", "pulls", "issues", "site", "cdn-cgi", "assets",
    "static", "favicon", "orgs", "apps",
}

_PAGE_SIZE = 30


def _github_page(query: str, pg: int) -> list[dict]:
    q = (query or "").strip()
    if not q:
        return []
    api_url = (
        "https://api.github.com/search/repositories"
        f"?q={urllib.parse.quote(q)}&sort=updated&order=desc"
        f"&per_page={_PAGE_SIZE}&page={pg}"
    )
    try:
        data = http_get(
            api_url,
            headers={"Accept": "application/vnd.github+json"},
            timeout=25,
        )
        out: list[dict] = []
        for item in data.get("items", []):
            full = item.get("full_name") or ""
            if not full:
                continue
            out.append(
                {
                    "name": full,
                    "description": (item.get("description") or "")[:400],
                    "url": item.get("html_url") or f"https://github.com/{full}",
                    "author": (item.get("owner") or {}).get("login", ""),
                    "published_at": item.get("updated_at", "") or "",
                    "language": item.get("language") or "",
                    "size_bytes": int(item.get("size") or 0) * 1024,
                    "stars": int(item.get("stargazers_count") or 0),
                    "version": item.get("default_branch") or "",
                }
            )
        if out:
            return out
    except Exception:
        pass

    # HTML fallback (last resort)
    url = (
        f"https://github.com/search?q={urllib.parse.quote(q)}"
        f"&type=repositories&s=updated&o=desc&p={pg}"
    )
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "text/html",
            },
        )
        html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    except Exception:
        return []
    out = []
    seen: set[str] = set()
    for href in re.findall(r'href="/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)"', html):
        o, rp = href.split("/", 1)
        if o.lower() in _SKIP or rp.lower() in _SKIP:
            continue
        if href in seen:
            continue
        seen.add(href)
        out.append(
            {
                "name": href,
                "url": f"https://github.com/{href}",
                "author": o,
            }
        )
    return out


def fetch(query: str, max_pages: int = 1, until_dt: datetime | None = None) -> list[dict]:
    return parallel_pages(_github_page, query, max_pages, until_dt, PROV_WORKERS["GitHub"])
