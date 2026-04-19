"""Shared helpers: datetime parsing, byte formatting, HTTP GET."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    parsers = [
        lambda x: datetime.fromisoformat(x.replace("Z", "+00:00")),
        lambda x: datetime.strptime(x[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc),
    ]
    for p in parsers:
        try:
            dt = p(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def rel_time(s: str | None) -> str:
    dt = parse_dt(s)
    if not dt:
        return (s or "")[:10]
    sec = int((datetime.now(timezone.utc) - dt).total_seconds())
    if sec < 60:
        return "just now"
    if sec < 3600:
        return f"{sec // 60}m ago"
    if sec < 86400:
        return f"{sec // 3600}h ago"
    if sec < 2_592_000:
        return f"{sec // 86400}d ago"
    if sec < 31_536_000:
        return f"{sec // 2_592_000}mo ago"
    return f"{sec // 31_536_000}y ago"


def fmt_bytes(n: int | float | None) -> str:
    try:
        n = int(n or 0)
    except (TypeError, ValueError):
        return "—"
    if n <= 0:
        return "—"
    if n < 1024:
        return f"{n} B"
    if n < 1 << 20:
        return f"{n / 1024:.1f} KB"
    if n < 1 << 30:
        return f"{n / (1 << 20):.1f} MB"
    return f"{n / (1 << 30):.1f} GB"


def http_get(url: str, headers: dict | None = None, timeout: int = 30) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PackageWatcher/1.0", **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def http_get_text(url: str, headers: dict | None = None, timeout: int = 30, max_bytes: int = 500_000) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PackageWatcher/1.0", **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(max_bytes).decode("utf-8", "replace")
