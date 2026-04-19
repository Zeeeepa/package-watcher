"""Analysis plugins: run computations on a package and return (label, text) pairs."""

from __future__ import annotations

from . import ai, codestats, complexity, depgraph, depscanner, filetree, readme, security, versions
from .base import Plugin

_REGISTRY: list[Plugin] = [
    filetree.FileTreePlugin(),
    depscanner.DependencyPlugin(),
    readme.ReadmePlugin(),
    versions.VersionsPlugin(),
    codestats.CodeStatsPlugin(),
    security.SecurityPlugin(),
    complexity.ComplexityPlugin(),
    depgraph.DepGraphPlugin(),
    ai.AIPlugin(),
]


def list_plugins() -> list[dict]:
    return [{"id": p.id, "label": p.label, "cache": p.cache} for p in _REGISTRY]


def get_plugin(pid: str) -> Plugin | None:
    for p in _REGISTRY:
        if p.id == pid:
            return p
    return None
