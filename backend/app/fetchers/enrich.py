"""Post-fetch enrichment: fill in size_bytes / file_count / language from registry APIs."""

from __future__ import annotations

import re
import urllib.parse
import urllib.request
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from ..utils import http_get


def _enrich_pypi(p: dict) -> None:
    if p.get("size_bytes"):
        return
    try:
        d = http_get(f"https://pypi.org/pypi/{urllib.parse.quote(p['name'])}/json", timeout=20)
        urls = d.get("urls", [])
        p["size_bytes"] = sum(u.get("size", 0) for u in urls) or None
        p["file_count"] = len(urls) or None
        p["language"] = "Python"
    except Exception:
        pass


def _enrich_npm(p: dict) -> None:
    if p.get("size_bytes"):
        return
    try:
        d = http_get(
            f"https://registry.npmjs.org/{urllib.parse.quote(p['name'], safe='')}/latest",
            timeout=20,
        )
        dist = d.get("dist", {})
        p["size_bytes"] = dist.get("unpackedSize")
        p["file_count"] = dist.get("fileCount")
        p["language"] = "JavaScript"
    except Exception:
        pass


def _enrich_github(p: dict) -> None:
    if p.get("language") or "/" not in p.get("name", ""):
        return
    try:
        req = urllib.request.Request(
            f"https://github.com/{p['name']}",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", "replace")
        m = re.search(
            r'class="[^"]*color-fg-default[^"]*text-bold[^"]*"[^>]*>([A-Za-z+#]+)</span>',
            html,
        )
        if m:
            p["language"] = m.group(1).strip()
    except Exception:
        pass


def _enrich_docker(p: dict) -> None:
    if p.get("size_bytes"):
        return
    name = p.get("name", "")
    if not name:
        return
    try:
        ns, repo = name.split("/", 1) if "/" in name else ("library", name)
        d = http_get(f"https://hub.docker.com/v2/repositories/{ns}/{repo}/", timeout=20)
        p["size_bytes"] = d.get("full_size")
    except Exception:
        pass


_ENRICH_MAP: dict[str, Callable[[dict], None]] = {
    "PyPI": _enrich_pypi,
    "npm": _enrich_npm,
    "GitHub": _enrich_github,
    "DockerHub": _enrich_docker,
}


def enrich(provider: str, pkgs: list[dict]) -> list[dict]:
    fn = _ENRICH_MAP.get(provider)
    if not fn:
        return pkgs
    targets = [p for p in pkgs[:100] if not p.get("size_bytes")]
    if not targets:
        return pkgs
    with ThreadPoolExecutor(max_workers=12, thread_name_prefix="enrich") as ex:
        list(ex.map(fn, targets))
    return pkgs
