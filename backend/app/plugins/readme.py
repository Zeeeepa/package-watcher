"""Return the stored README text."""

from __future__ import annotations

from .base import Plugin


class ReadmePlugin(Plugin):
    id = "readme"
    label = "README"

    def run(self, pkg: dict, meta: dict) -> str:
        return (meta.get("readme_text") or "(no README available)").strip()
