"""FastAPI app factory + entrypoint."""

from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .api import analysis, feeds, monitors, packages, stats
from .config import API_HOST, API_PORT
from .scheduler import instance as scheduler

log = logging.getLogger("package-watcher")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    db.init()
    sched = scheduler()
    for m in db.all_monitors():
        if m.get("enabled"):
            threading.Thread(target=sched.start, args=(m,), daemon=True).start()
    try:
        yield
    finally:
        scheduler().stop_all()


def create_app() -> FastAPI:
    app = FastAPI(
        title="package-watcher",
        description="Aggregate, explore, and filter packages across registries.",
        version="1.0.0",
        lifespan=_lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(monitors.router)
    app.include_router(packages.router)
    app.include_router(analysis.router)
    app.include_router(stats.router)
    app.include_router(feeds.router)

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True, "version": app.version}

    return app


app = create_app()


def main() -> None:
    import uvicorn
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=False)


if __name__ == "__main__":
    main()
