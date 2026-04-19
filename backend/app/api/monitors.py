"""Monitor CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import db
from ..scheduler import instance as scheduler

router = APIRouter(prefix="/api/monitors", tags=["monitors"])


class MonitorIn(BaseModel):
    provider: str
    query: str
    interval_sec: int = 300
    fetch_mode: str = "pages"
    fetch_pages: int = 1
    fetch_days: int = 3
    providers: str | None = None


class MonitorPatch(BaseModel):
    enabled: bool | None = None
    interval_sec: int | None = None
    fetch_mode: str | None = None
    fetch_pages: int | None = None
    fetch_days: int | None = None
    providers: str | None = None
    provider: str | None = None
    query: str | None = None


@router.get("")
def list_monitors() -> list[dict]:
    return db.all_monitors()


@router.post("")
def create_monitor(body: MonitorIn) -> dict:
    mid = db.add_monitor(
        provider=body.provider,
        query=body.query,
        interval_sec=body.interval_sec,
        fetch_mode=body.fetch_mode,
        fetch_pages=body.fetch_pages,
        fetch_days=body.fetch_days,
        providers=body.providers or body.provider,
    )
    m = db.get_monitor(mid)
    if m and m.get("enabled"):
        scheduler().start(m)
    return m or {"id": mid}


@router.get("/{mid}")
def get_monitor(mid: int) -> dict:
    m = db.get_monitor(mid)
    if not m:
        raise HTTPException(404, "Not found")
    return m


@router.patch("/{mid}")
def patch_monitor(mid: int, body: MonitorPatch) -> dict:
    existing = db.get_monitor(mid)
    if not existing:
        raise HTTPException(404, "Not found")
    db.patch_monitor(mid, **body.model_dump(exclude_unset=True))
    m = db.get_monitor(mid) or existing
    sched = scheduler()
    sched.stop(mid)
    if m.get("enabled"):
        sched.start(m)
    return m


@router.delete("/{mid}")
def delete_monitor(mid: int) -> dict:
    scheduler().stop(mid)
    db.delete_monitor(mid)
    return {"ok": True}


@router.post("/{mid}/trigger")
def trigger(mid: int) -> dict:
    m = db.get_monitor(mid)
    if not m:
        raise HTTPException(404, "Not found")
    scheduler().fire(m)
    return {"ok": True}


@router.post("/{mid}/enable")
def enable(mid: int, body: dict | None = None) -> dict:
    enabled = bool((body or {}).get("enabled", True))
    db.set_monitor_enabled(mid, enabled)
    m = db.get_monitor(mid)
    if not m:
        raise HTTPException(404, "Not found")
    sched = scheduler()
    sched.stop(mid)
    if enabled:
        sched.start(m)
    return m
