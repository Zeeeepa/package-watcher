"""WebURL feed detection endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..fetchers.weburl import detect_feed

router = APIRouter(prefix="/api/feeds", tags=["feeds"])


@router.get("/detect")
def detect(url: str) -> dict:
    if not url:
        raise HTTPException(400, "url query required")
    return detect_feed(url)
