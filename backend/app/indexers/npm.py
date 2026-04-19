"""npm deep-indexer: full registry JSON + tarball tree (with jsDelivr fallback)."""

from __future__ import annotations

import urllib.parse

from ..archive import extract_tree_from_url
from ..utils import http_get


def index(name: str) -> dict:
    enc = urllib.parse.quote(name, safe="@")
    data = http_get(f"https://registry.npmjs.org/{enc}", timeout=25)
    dist_tags = data.get("dist-tags") or {}
    latest = dist_tags.get("latest", "")
    all_vers = data.get("versions") or {}
    v_obj = all_vers.get(latest) or {}
    dist = v_obj.get("dist") or {}
    tarball = dist.get("tarball", "")

    versions: list[dict] = []
    times = data.get("time") or {}
    for ver_str, meta in all_vers.items():
        d = meta.get("dist") or {}
        versions.append(
            {
                "version": ver_str,
                "date": (times.get(ver_str, "") or "")[:19],
                "size": d.get("unpackedSize", 0),
                "tarball": d.get("tarball", ""),
                "integrity": d.get("integrity", ""),
            }
        )
    versions.sort(key=lambda v: v.get("date", ""), reverse=True)

    deps = list((v_obj.get("dependencies") or {}).keys())
    dev_deps = list((v_obj.get("devDependencies") or {}).keys())
    peer = list((v_obj.get("peerDependencies") or {}).keys())

    readme = (v_obj.get("readme") or data.get("readme") or "").strip()

    tree_json = None
    if tarball:
        fn = tarball.split("/")[-1]
        tree_json = extract_tree_from_url(tarball, fn)

    if not tree_json:
        try:
            jsd_enc = urllib.parse.quote(name, safe="@/")
            jsd = http_get(
                f"https://data.jsdelivr.com/v1/packages/npm/{jsd_enc}/flat",
                timeout=20,
            )
            jsd_files = [
                {"path": f["name"], "size": f.get("size", 0), "type": "file"}
                for f in (jsd.get("files") or [])
            ]
            if jsd_files:
                tree_json = {
                    "files": jsd_files,
                    "dirs": [],
                    "_src_file": "jsDelivr",
                }
        except Exception:
            pass

    unpacked = dist.get("unpackedSize", 0)
    file_count = len(tree_json["files"]) if tree_json else 0

    author = v_obj.get("author") or {}
    if isinstance(author, dict):
        author_name = author.get("name", "")
    else:
        author_name = str(author)

    keywords = v_obj.get("keywords") or []

    return {
        "readme_text": readme,
        "deps_json": {"dependencies": deps, "dev_deps": dev_deps, "peer_deps": peer},
        "versions_json": versions,
        "file_tree_json": tree_json,
        "meta_json": {
            "keywords": keywords,
            "homepage": v_obj.get("homepage", ""),
            "repository": v_obj.get("repository") or {},
            "license": v_obj.get("license", ""),
            "engines": v_obj.get("engines") or {},
        },
        "description": (data.get("description") or v_obj.get("description", "")).strip(),
        "version": latest,
        "language": "JavaScript",
        "size_bytes": unpacked,
        "file_count": file_count,
        "published_at": (times.get(latest, "") or "")[:19],
        "author": author_name,
        "license_spdx": v_obj.get("license", "") or "",
        "homepage": v_obj.get("homepage", "") or "",
        "topics_json": keywords,
    }
