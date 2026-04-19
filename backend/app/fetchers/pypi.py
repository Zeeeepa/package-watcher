"""PyPI search: registry RSS feed + JSON API (no browser required)."""

from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

from ..config import PROV_WORKERS
from ..utils import http_get
from .base import parallel_pages


def _pypi_page(query: str, pg: int) -> list[dict]:
    """PyPI search — returns results for one page.

    Uses the search JSON hack plus RSS feed fallback. No headless browser.
    """
    if pg == 1:
        try:
            req = urllib.request.Request(
                "https://pypi.org/rss/updates.xml",
                headers={"User-Agent": "PackageWatcher/1.0"},
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                root = ET.fromstring(r.read())
            q = (query or "").strip().lower()
            out: list[dict] = []
            for item in root.findall(".//item"):
                t = (item.findtext("title", "") or "").strip()
                parts = t.split()
                name = parts[0] if parts else ""
                desc = item.findtext("description", "") or ""
                if not name:
                    continue
                if not q or len(q) <= 2 or q in name.lower() or q in desc.lower():
                    out.append(
                        {
                            "name": name,
                            "description": desc,
                            "version": parts[1] if len(parts) > 1 else "",
                            "url": item.findtext("link", "") or f"https://pypi.org/project/{name}/",
                            "published_at": item.findtext("pubDate", ""),
                        }
                    )
            if out:
                return out
        except Exception:
            pass

    # JSON search: pypi.org supports `https://pypi.org/simple/` but not direct search JSON.
    # Use warehouse "project list" fallback: pypi.org/simple/<q>/  for exact names.
    q = (query or "").strip()
    if q:
        try:
            data = http_get(
                f"https://pypi.org/pypi/{urllib.parse.quote(q)}/json", timeout=20
            )
            info = data.get("info") or {}
            urls = data.get("urls") or []
            return [
                {
                    "name": info.get("name") or q,
                    "description": info.get("summary") or "",
                    "version": info.get("version") or "",
                    "url": f"https://pypi.org/project/{info.get('name') or q}/",
                    "author": info.get("author") or info.get("maintainer") or "",
                    "published_at": (urls[0].get("upload_time_iso_8601", "") if urls else ""),
                    "size_bytes": sum(u.get("size", 0) for u in urls) or None,
                    "file_count": len(urls) or None,
                    "language": "Python",
                }
            ]
        except Exception:
            return []
    return []


def fetch(query: str, max_pages: int = 1, until_dt: datetime | None = None) -> list[dict]:
    return parallel_pages(_pypi_page, query, max_pages, until_dt, PROV_WORKERS["PyPI"])
