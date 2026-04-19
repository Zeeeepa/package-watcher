"""Run analysis plugins against a package."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import db, indexer_service, plugins

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/plugins")
def list_plugins() -> list[dict]:
    return plugins.list_plugins()


@router.get("/{pkg_id}/{plugin_id}")
def run_plugin(pkg_id: int, plugin_id: str, force: bool = False) -> dict:
    pkg = db.get_package(pkg_id)
    if not pkg:
        raise HTTPException(404, "Package not found")
    plugin = plugins.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(404, "Plugin not found")

    if not force and plugin.cache:
        cached = db.get_analysis(pkg_id, plugin.id)
        if cached:
            return {"cached": True, "result": cached}

    meta = db.get_pkg_metadata(pkg_id)
    if not meta:
        indexer_service.index_one(pkg_id, pkg["provider"], pkg["name"], force=True, log=False)
        meta = db.get_pkg_metadata(pkg_id) or {}

    try:
        result = plugin.run(pkg, meta)
    except Exception as e:
        raise HTTPException(500, f"Plugin error: {e}") from e

    if plugin.cache and result:
        db.set_analysis(pkg_id, plugin.id, result)
    return {"cached": False, "result": result}


@router.post("/{pkg_id}/reindex")
def reindex(pkg_id: int) -> dict:
    pkg = db.get_package(pkg_id)
    if not pkg:
        raise HTTPException(404, "Not found")
    comp = indexer_service.index_one(
        pkg_id, pkg["provider"], pkg["name"], force=True, log=False
    )
    return {"compliance": comp}
