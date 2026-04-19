"""ASCII dep-graph: package → direct runtime deps."""

from __future__ import annotations

from .base import Plugin


class DepGraphPlugin(Plugin):
    id = "depgraph"
    label = "Dep Graph"

    def run(self, pkg: dict, meta: dict) -> str:
        deps = (meta.get("deps_json") or {}).get("dependencies") or []
        if not deps:
            return "(no runtime dependencies)"
        name = pkg.get("name") or "package"
        lines = [f"{name}"]
        for i, d in enumerate(deps):
            branch = "└─" if i == len(deps) - 1 else "├─"
            lines.append(f"  {branch} {d}")
        return "\n".join(lines)
