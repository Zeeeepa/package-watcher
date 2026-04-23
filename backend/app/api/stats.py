"""Dashboard / exploratory aggregate endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from .. import db
from ..config import LANG_COLOR, PROV_COLOR, PROVIDERS

router = APIRouter(prefix="/api/stats", tags=["stats"])

_SIZE_BUCKETS = [
    0, 10 * 1024, 100 * 1024, 1024 * 1024, 10 * 1024 * 1024,
    100 * 1024 * 1024, 1024 * 1024 * 1024, 10 * 1024 * 1024 * 1024,
]
_FILE_BUCKETS = [0, 5, 20, 50, 100, 500, 2000, 10_000, 100_000]


@router.get("")
def dashboard() -> dict:
    return db.stats()


@router.get("/histogram/sizes")
def sizes() -> list[dict]:
    return db.histogram_sizes(_SIZE_BUCKETS)


@router.get("/histogram/files")
def files() -> list[dict]:
    return db.histogram_files(_FILE_BUCKETS)


@router.get("/timeline")
def timeline(days: int = 90) -> list[dict]:
    return db.timeline_published(days=max(1, min(days, 365)))


@router.get("/languages")
def languages(limit: int = 20) -> list[dict]:
    return db.top_languages(limit=max(1, min(limit, 100)))


@router.get("/top_starred")
def top_starred(limit: int = 20) -> list[dict]:
    return db.top_starred(limit=max(1, min(limit, 100)))


@router.get("/top_compliance")
def top_compliance(limit: int = 20) -> list[dict]:
    return db.top_compliance(limit=max(1, min(limit, 100)))


@router.get("/catalog")
def catalog(limit: int = 500, offset: int = 0, search: str = "") -> dict:
    rows = db.catalog_rows(
        limit=max(1, min(limit, 2000)),
        offset=max(0, offset),
        search=search,
    )
    return {"items": rows, "offset": offset, "limit": limit}


@router.get("/meta")
def meta() -> dict:
    return {
        "providers": PROVIDERS,
        "provider_colors": PROV_COLOR,
        "lang_colors": LANG_COLOR,
    }
