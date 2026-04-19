"""WebURL feed / article extractor — query IS the URL."""

from __future__ import annotations

import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from ..utils import parse_dt


def _hostname(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.replace("www.", "")
    except Exception:
        return url[:30]


def _via_feed(url: str) -> list[dict]:
    try:
        import feedparser as fp
    except ImportError:
        return []

    def _entries(feed, source_url):
        host = _hostname(source_url)
        out = []
        for e in feed.entries:
            title = (e.get("title") or e.get("link") or "").strip()
            link = e.get("link") or e.get("id") or ""
            pub = ""
            for attr in ("published", "updated", "created"):
                raw = e.get(attr, "")
                if raw:
                    dt = parse_dt(raw)
                    if dt:
                        pub = dt.isoformat()
                        break
            summary = ""
            for attr in ("summary", "content"):
                val = e.get(attr, "")
                if isinstance(val, list) and val:
                    val = val[0].get("value", "")
                if val:
                    summary = re.sub(r"<[^>]+>", "", val).strip()[:400]
                    break
            author = e.get("author", "") or host
            out.append(
                {
                    "name": title[:200],
                    "description": summary,
                    "url": link,
                    "author": author,
                    "published_at": pub,
                    "version": "",
                    "language": feed.get("feed", {}).get("language", "") or "",
                }
            )
        return out

    feed = fp.parse(url)
    if feed.entries:
        return _entries(feed, url)
    for suffix in ("/feed", "/rss", "/atom", "/feed.xml", "/rss.xml", "/atom.xml", "?format=rss"):
        try:
            candidate = url.rstrip("/") + suffix
            feed2 = fp.parse(candidate)
            if feed2.entries:
                return _entries(feed2, url)
        except Exception:
            continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PackageWatcher/1.0"})
        html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "replace")
        m = re.search(
            r'<link[^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]+href=["\']([^"\']+)["\']',
            html, re.I,
        )
        if m:
            href = m.group(1)
            feed_url = href if href.startswith("http") else urllib.parse.urljoin(url, href)
            feed3 = fp.parse(feed_url)
            if feed3.entries:
                return _entries(feed3, url)
    except Exception:
        pass
    return []


def _via_trafilatura(url: str, max_items: int = 50) -> list[dict]:
    try:
        import trafilatura
    except ImportError:
        return []
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return []
        links = trafilatura.extract_metadata(downloaded)
        host = _hostname(url)
        out: list[dict] = []
        if links and links.url:
            out.append(
                {
                    "name": (links.title or host)[:200],
                    "description": (links.description or "")[:400],
                    "url": links.url,
                    "author": links.author or host,
                    "published_at": (links.date or "")[:19],
                    "version": "",
                    "language": getattr(links, "language", "") or "",
                }
            )
        return out[:max_items]
    except Exception:
        return []


def fetch(url: str, max_pages: int = 1, until_dt: datetime | None = None) -> list[dict]:
    items = _via_feed(url) or _via_trafilatura(url)
    if until_dt and items:
        items = [
            i
            for i in items
            if not i.get("published_at")
            or (parse_dt(i["published_at"]) or datetime.min.replace(tzinfo=timezone.utc)) >= until_dt
        ]
    seen: set[str] = set()
    deduped: list[dict] = []
    for i in items:
        k = i.get("url", "")
        if k and k not in seen:
            seen.add(k)
            deduped.append(i)
    return deduped[:200]


def detect_feed(url: str) -> dict:
    try:
        import feedparser as fp
    except ImportError:
        return {"type": "unknown", "feed_url": "", "sample": [], "count": 0}
    try:
        feed = fp.parse(url)
        if feed.entries:
            titles = [e.get("title", "") for e in feed.entries[:5]]
            return {
                "type": "feed",
                "feed_url": url,
                "sample": titles,
                "count": len(feed.entries),
            }
    except Exception:
        pass
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PackageWatcher/1.0"})
        html = urllib.request.urlopen(req, timeout=12).read(200_000).decode("utf-8", "replace")
        m = re.search(
            r'<link[^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]+href=["\']([^"\']+)["\']',
            html, re.I,
        )
        if m:
            href = m.group(1)
            feed_url = href if href.startswith("http") else urllib.parse.urljoin(url, href)
            feed2 = fp.parse(feed_url)
            titles = [e.get("title", "") for e in feed2.entries[:5]]
            return {
                "type": "feed",
                "feed_url": feed_url,
                "sample": titles,
                "count": len(feed2.entries),
            }
        links = re.findall(r'href=["\']([^"\'#?]{10,})["\']', html)
        return {"type": "html", "feed_url": "", "sample": links[:5], "count": len(links)}
    except Exception as e:
        return {
            "type": "unknown",
            "feed_url": "",
            "sample": [],
            "count": 0,
            "error": str(e),
        }
