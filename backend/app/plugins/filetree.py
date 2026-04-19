"""Pretty-print a file tree."""

from __future__ import annotations

from ..utils import fmt_bytes
from .base import Plugin


class FileTreePlugin(Plugin):
    id = "filetree"
    label = "File Tree"

    def run(self, pkg: dict, meta: dict) -> str:
        tree = meta.get("file_tree_json")
        if not tree:
            return "(no file tree available)"
        files = tree.get("files") or []
        if not files:
            return "(empty)"
        paths = sorted(f["path"] for f in files)
        size_by = {f["path"]: f.get("size", 0) for f in files}
        lines = [f"Total files: {len(files)}", ""]
        for p in paths[:2000]:
            lines.append(f"  {p}  ({fmt_bytes(size_by.get(p, 0))})")
        if len(paths) > 2000:
            lines.append(f"  …(and {len(paths) - 2000} more)")
        return "\n".join(lines)
