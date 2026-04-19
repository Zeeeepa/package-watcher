"""Provider fetchers (search / list packages from registries)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from . import dockerhub, github, librariesio, npm, pypi, weburl
from .enrich import enrich

_FETCHERS: dict[str, Callable] = {
    "PyPI": pypi.fetch,
    "npm": npm.fetch,
    "GitHub": github.fetch,
    "DockerHub": dockerhub.fetch,
    "Libraries.io": librariesio.fetch,
    "WebURL": weburl.fetch,
}


def do_fetch(
    provider: str,
    query: str,
    mode: str = "pages",
    pages: int = 1,
    days: int = 3,
) -> list[dict]:
    fn = _FETCHERS.get(provider)
    if not fn:
        return []
    until = (
        datetime.now(timezone.utc) - timedelta(days=days) if mode == "days" else None
    )
    max_pages = pages if mode == "pages" else 999
    results = fn(query, max_pages, until)
    if provider != "WebURL":
        results = enrich(provider, results)
    return results
