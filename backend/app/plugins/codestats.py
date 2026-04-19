"""Basic code stats: file extension breakdown."""

from __future__ import annotations

import os
from collections import Counter

from ..utils import fmt_bytes
from .base import Plugin


class CodeStatsPlugin(Plugin):
    id = "codestats"
    label = "Code Stats"

    def run(self, pkg: dict, meta: dict) -> str:
        tree = meta.get("file_tree_json") or {}
        files = tree.get("files") or []
        if not files:
            return "(no file tree available)"
        by_ext = Counter()
        size_by_ext: dict[str, int] = {}
        total = 0
        for f in files:
            p = f.get("path", "")
            sz = int(f.get("size", 0) or 0)
            ext = (os.path.splitext(p)[1] or "(no ext)").lower()
            by_ext[ext] += 1
            size_by_ext[ext] = size_by_ext.get(ext, 0) + sz
            total += sz
        rows = [
            f"{'Ext':<12} {'Files':>7} {'Size':>12}",
            "─" * 36,
        ]
        for ext, cnt in by_ext.most_common(40):
            rows.append(
                f"{ext:<12} {cnt:>7} {fmt_bytes(size_by_ext.get(ext, 0)):>12}"
            )
        rows.append("─" * 36)
        rows.append(f"{'Total':<12} {len(files):>7} {fmt_bytes(total):>12}")
        return "\n".join(rows)
