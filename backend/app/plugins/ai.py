"""Heuristic AI-style summary produced locally from metadata; no external LLM required."""

from __future__ import annotations

import re

from ..utils import fmt_bytes
from .base import Plugin


def _short(text: str, n: int = 2) -> str:
    if not text:
        return ""
    plain = re.sub(r"<[^>]+>", "", text)
    sents = re.split(r"(?<=[.!?])\s+", plain)
    return " ".join(sents[:n]).strip()


class AIPlugin(Plugin):
    id = "ai"
    label = "AI Summary"

    def run(self, pkg: dict, meta: dict) -> str:
        lines: list[str] = []
        name = pkg.get("name") or "package"
        provider = pkg.get("provider") or ""
        lang = pkg.get("language") or ""
        description = pkg.get("description") or meta.get("meta_json", {}).get("summary") or ""
        if description:
            lines.append(f"**What it is:** {_short(description)}")
        if lang:
            lines.append(f"**Language:** {lang}")
        if pkg.get("version"):
            lines.append(f"**Latest version:** {pkg['version']}")
        if pkg.get("published_at"):
            lines.append(f"**Last published:** {pkg['published_at']}")
        size = pkg.get("size_bytes") or 0
        if size:
            lines.append(f"**Size:** {fmt_bytes(size)}")
        if pkg.get("file_count"):
            lines.append(f"**Files:** {pkg['file_count']}")

        deps = (meta.get("deps_json") or {}).get("dependencies") or []
        lines.append(f"**Direct deps:** {len(deps)}")

        readme = meta.get("readme_text") or ""
        if readme:
            summary = _short(readme, 3)
            if summary:
                lines.append("")
                lines.append("**README gist:**")
                lines.append(summary)

        if provider == "GitHub":
            stars = meta.get("stars") or pkg.get("stars") or 0
            if stars:
                lines.append(f"**Stars:** {stars}")

        lines.append("")
        lines.append(
            f"_(Auto-summary for `{provider} / {name}` built from local metadata only — no external LLM used.)_"
        )
        return "\n".join(lines)
