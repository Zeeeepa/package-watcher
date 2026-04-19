"""Base class for analysis plugins."""

from __future__ import annotations


class Plugin:
    id: str = ""
    label: str = ""
    cache: bool = True

    def run(self, pkg: dict, meta: dict) -> str:
        """Given a package row (dict) and its deep metadata (dict), return plain/markdown text."""
        raise NotImplementedError
