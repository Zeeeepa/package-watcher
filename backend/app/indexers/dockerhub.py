"""DockerHub deep-indexer: repo info + tag listing as pseudo-tree."""

from __future__ import annotations

from ..utils import http_get


def index(name: str) -> dict:
    parts = name.split("/")
    ns = parts[0] if len(parts) > 1 else "library"
    repo = parts[-1]
    info = http_get(f"https://hub.docker.com/v2/repositories/{ns}/{repo}/", timeout=20)
    tags_data = http_get(
        f"https://hub.docker.com/v2/repositories/{ns}/{repo}/tags?page_size=50",
        timeout=20,
    )
    tags = tags_data.get("results") or []
    files: list[dict] = []
    versions: list[dict] = []
    for t in tags:
        sz = sum(img.get("size", 0) for img in t.get("images") or [])
        files.append(
            {"path": f":{t.get('name', 'latest')}", "size": sz, "type": "tag"}
        )
        versions.append(
            {
                "version": t.get("name", "") or "",
                "date": (t.get("last_updated", "") or "")[:19],
                "size": sz,
            }
        )

    return {
        "readme_text": info.get("full_description", "") or "",
        "deps_json": None,
        "versions_json": versions,
        "file_tree_json": (
            {"files": files, "dirs": [], "_src_file": "DockerHub tags"}
            if files
            else None
        ),
        "meta_json": {
            "pull_count": int(info.get("pull_count") or 0),
            "star_count": int(info.get("star_count") or 0),
            "is_official": bool(info.get("is_official")),
        },
        "description": info.get("description", "") or "",
        "language": "Dockerfile",
        "size_bytes": int(info.get("full_size") or 0),
        "file_count": len(files),
        "published_at": (info.get("last_updated", "") or "")[:19],
        "author": ns,
        "stars": int(info.get("star_count") or 0),
        "homepage": "",
        "license_spdx": "",
        "topics_json": [],
    }
