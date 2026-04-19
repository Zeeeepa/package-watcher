"""Rough complexity proxy: size, file count, directory depth."""

from __future__ import annotations

from ..utils import fmt_bytes
from .base import Plugin


class ComplexityPlugin(Plugin):
    id = "complexity"
    label = "Complexity"

    def run(self, pkg: dict, meta: dict) -> str:
        tree = meta.get("file_tree_json") or {}
        files = tree.get("files") or []
        if not files:
            return "(no file tree available)"
        total = sum(f.get("size", 0) for f in files)
        depth = max((f.get("path", "").count("/") for f in files), default=0)
        big = sorted(files, key=lambda f: f.get("size", 0), reverse=True)[:10]
        lines = [
            f"Files:      {len(files)}",
            f"Total size: {fmt_bytes(total)}",
            f"Max depth:  {depth}",
            "",
            "Top 10 largest files:",
        ]
        for f in big:
            lines.append(f"  • {f.get('path'):<60} {fmt_bytes(f.get('size', 0))}")
        return "\n".join(lines)
