"""PyPI deep-indexer: full metadata + README + tarball file tree."""

from __future__ import annotations

import urllib.parse

from ..archive import extract_tree_from_url
from ..utils import http_get


def _pick_sdist_or_wheel(urls: list[dict]) -> dict | None:
    sdist = next((u for u in urls if (u.get("packagetype") or "") == "sdist"), None)
    if sdist:
        return sdist
    whl = next(
        (u for u in urls if (u.get("filename", "") or "").endswith(".whl")),
        None,
    )
    return whl


def index(name: str) -> dict:
    d = http_get(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json", timeout=25)
    info = d.get("info") or {}
    urls = d.get("urls") or []
    releases = d.get("releases") or {}

    versions: list[dict] = []
    for ver, files in releases.items():
        if not files:
            continue
        dates = [
            f.get("upload_time_iso_8601", "")
            for f in files
            if f.get("upload_time_iso_8601")
        ]
        versions.append(
            {
                "version": ver,
                "date": (min(dates) if dates else "")[:19],
                "size": sum(f.get("size", 0) for f in files),
                "file_count": len(files),
                "yanked": any(f.get("yanked") for f in files),
            }
        )
    versions.sort(key=lambda v: v["date"], reverse=True)

    readme = info.get("description") or ""
    if len(readme) > 100_000:
        readme = readme[:100_000] + "\n\n…(truncated)"

    deps: list[str] = []
    dev_deps: list[str] = []
    for dist in info.get("requires_dist") or []:
        if not dist:
            continue
        low = dist.lower()
        if "extra ==" in low or "extra == " in low or 'extra == "dev"' in low or "; extra" in low:
            dev_deps.append(dist)
        else:
            deps.append(dist)

    tree_json = None
    pick = _pick_sdist_or_wheel(urls)
    if pick and pick.get("url") and (pick.get("size", 0) or 0) < 25 * 1024 * 1024:
        tree_json = extract_tree_from_url(pick["url"], pick.get("filename"))

    kw = info.get("keywords") or ""
    keywords = [k.strip() for k in kw.replace(",", " ").split() if k.strip()]

    size_bytes = sum(u.get("size", 0) for u in urls)
    file_count = len(tree_json["files"]) if tree_json else len(urls)

    return {
        "readme_text": readme,
        "deps_json": {"dependencies": deps, "dev_deps": dev_deps, "peer_deps": []},
        "versions_json": versions,
        "file_tree_json": tree_json,
        "meta_json": {
            "summary": info.get("summary", ""),
            "license": info.get("license", ""),
            "homepage": info.get("home_page", "") or "",
            "project_urls": info.get("project_urls") or {},
            "keywords": keywords,
            "requires_python": info.get("requires_python", ""),
            "classifiers": info.get("classifiers") or [],
            "author": info.get("author", "") or info.get("maintainer", ""),
        },
        "description": info.get("summary", ""),
        "version": info.get("version", ""),
        "language": "Python",
        "size_bytes": size_bytes,
        "file_count": file_count,
        "published_at": (versions[0]["date"] if versions else ""),
        "author": info.get("author", "") or info.get("maintainer", ""),
        "license_spdx": info.get("license", "") or "",
        "homepage": info.get("home_page", "") or "",
        "topics_json": keywords,
    }
