"""Package query / detail / download endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .. import db, deep_meta, downloader

router = APIRouter(prefix="/api/packages", tags=["packages"])


def _split(val: str | None) -> list[str] | None:
    if not val:
        return None
    items = [s.strip() for s in val.split(",") if s.strip()]
    return items or None


@router.get("")
def list_packages(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    sort_col: str = Query("published_at"),
    sort_asc: bool = Query(False),
    provider: str | None = None,
    providers: str | None = Query(None, description="comma-separated"),
    languages: str | None = Query(None, description="comma-separated"),
    monitor_id: int | None = None,
    query: str | None = None,
    search: str = "",
    min_size: int | None = None,
    max_size: int | None = None,
    min_files: int | None = None,
    max_files: int | None = None,
    published_after: str | None = None,
    published_before: str | None = None,
    new_only: bool = False,
    dl_only: bool = False,
) -> dict:
    filters = dict(
        provider=provider,
        query=query,
        search=search or "",
        providers_filter=_split(providers),
        languages_filter=_split(languages),
        min_size=min_size,
        max_size=max_size,
        min_files=min_files,
        max_files=max_files,
        published_after=published_after,
        published_before=published_before,
        new_only=new_only,
        dl_only=dl_only,
        monitor_id=monitor_id,
    )
    total = db.count_packages(**filters)
    items = db.get_packages(
        page=page,
        per_page=per_page,
        sort_col=sort_col,
        sort_asc=sort_asc,
        **filters,
    )
    return {"total": total, "page": page, "per_page": per_page, "items": items}


@router.get("/{pkg_id}")
def package_detail(pkg_id: int) -> dict:
    pkg = db.get_package(pkg_id)
    if not pkg:
        raise HTTPException(404, "Not found")
    meta = db.get_pkg_metadata(pkg_id) or {}
    return {"package": pkg, "metadata": meta}


@router.get("/{pkg_id}/live")
def package_live(pkg_id: int) -> dict:
    pkg = db.get_package(pkg_id)
    if not pkg:
        raise HTTPException(404, "Not found")
    data = deep_meta.fetch_meta(pkg["provider"], pkg["name"])
    return {"package": pkg, "live": data}


@router.post("/{pkg_id}/download")
def download(pkg_id: int) -> dict:
    ok, msg = downloader.download(pkg_id)
    if not ok:
        raise HTTPException(400, msg)
    return {"ok": True, "message": msg}


class DeleteBody(BaseModel):
    ids: list[int]


@router.post("/delete")
def delete(body: DeleteBody) -> dict:
    n = db.delete_packages(body.ids)
    return {"deleted": n}
