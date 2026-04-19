"""Pretty-print the dependencies stored in deep metadata."""

from __future__ import annotations

from .base import Plugin


class DependencyPlugin(Plugin):
    id = "dependencies"
    label = "Dependencies"

    def run(self, pkg: dict, meta: dict) -> str:
        deps = meta.get("deps_json") or {}
        if not any(deps.values()):
            return "(no dependency info recorded)"
        parts: list[str] = []
        for label, key in [
            ("Runtime", "dependencies"),
            ("Dev", "dev_deps"),
            ("Peer", "peer_deps"),
        ]:
            items = deps.get(key) or []
            if items:
                parts.append(f"### {label} ({len(items)})\n")
                parts.extend(f"  • {d}" for d in items)
                parts.append("")
        return "\n".join(parts)
