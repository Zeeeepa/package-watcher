"""Render the versions table."""

from __future__ import annotations

from ..utils import fmt_bytes
from .base import Plugin


class VersionsPlugin(Plugin):
    id = "versions"
    label = "Versions"

    def run(self, pkg: dict, meta: dict) -> str:
        versions = meta.get("versions_json") or []
        if not versions:
            return "(no versions recorded)"
        current = pkg.get("version") or ""
        lines = [f"{'Version':<22} {'Date':<12} {'Size':<10} Note", "─" * 60]
        for v in versions[:100]:
            ver = v.get("version", "")
            date = (v.get("date") or "")[:10]
            size = v.get("size", 0)
            note = (
                "← latest"
                if ver == current
                else ("yanked" if v.get("yanked") else "")
            )
            lines.append(
                f"{ver:<22} {date:<12} {fmt_bytes(size):<10} {note}"
            )
        return "\n".join(lines)
