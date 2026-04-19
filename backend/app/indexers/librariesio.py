"""Libraries.io items are cross-listed; delegate to the canonical provider's indexer."""

from __future__ import annotations

from . import github, npm, pypi


def index(name: str) -> dict:
    if "/" in name:
        return github.index(name)
    for try_fn, prov in [(pypi.index, "PyPI"), (npm.index, "npm")]:
        try:
            result = try_fn(name)
            if not result.get("error"):
                result["_resolved_provider"] = prov
                return result
        except Exception:
            continue
    return {"error": f"Could not resolve Libraries.io package: {name}"}
