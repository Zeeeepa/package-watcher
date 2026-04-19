"""Deep-indexing strategies: registry-native metadata pulls for enrichment / compliance."""

from __future__ import annotations

from collections.abc import Callable

from . import dockerhub, github, librariesio, npm, pypi
from . import weburl as _weburl

_INDEXERS: dict[str, Callable[[str], dict]] = {
    "PyPI": pypi.index,
    "npm": npm.index,
    "GitHub": github.index,
    "DockerHub": dockerhub.index,
    "WebURL": _weburl.index,
    "Libraries.io": librariesio.index,
}


def index_for(provider: str, name: str) -> dict:
    fn = _INDEXERS.get(provider)
    if not fn:
        return {"error": f"No indexer for {provider}"}
    try:
        return fn(name)
    except Exception as e:
        return {"error": str(e)}
