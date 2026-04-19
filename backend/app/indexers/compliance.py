"""Compliance scoring — computes a 0-100 score based on metadata completeness."""

from __future__ import annotations

from typing import Any

from .. import db


def check_compliance(pkg_id: int) -> dict:
    meta = db.get_pkg_metadata(pkg_id) or {}
    pkg = db.get_package(pkg_id) or {}
    score = 0
    missing: list[str] = []

    def has(val: Any) -> bool:
        if val is None:
            return False
        if isinstance(val, (list, dict, str)) and not val:
            return False
        return True

    checks = [
        (has(pkg.get("description")), 10, "description"),
        (has(pkg.get("version")), 5, "version"),
        (has(pkg.get("author")), 5, "author"),
        (has(pkg.get("published_at")), 5, "published_at"),
        (bool(pkg.get("size_bytes")), 10, "size_bytes"),
        (bool(pkg.get("file_count")), 10, "file_count"),
        (has(pkg.get("language")), 5, "language"),
        (has(meta.get("readme_text")), 15, "readme"),
        (has(meta.get("deps_json")), 10, "deps"),
        (has(meta.get("versions_json")), 10, "versions"),
        (has(meta.get("file_tree_json")), 10, "file_tree"),
        (has(meta.get("meta_json")), 5, "meta"),
    ]
    flags: dict[str, bool] = {}
    for ok, weight, label in checks:
        flags[label] = bool(ok)
        if ok:
            score += weight
        else:
            missing.append(label)
    return {
        "score": min(score, 100),
        "missing": missing,
        "flags": flags,
    }


def save_compliance(pkg_id: int, comp: dict) -> None:
    db.save_compliance(pkg_id, int(comp.get("score", 0)), comp.get("flags") or {})
