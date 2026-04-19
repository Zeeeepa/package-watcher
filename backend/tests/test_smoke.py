"""Smoke tests: app starts, health works, DB schema initializes, filter builder behaves."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def _setup_tmp() -> None:
    d = tempfile.mkdtemp(prefix="pw-test-")
    os.environ["PW_DATA_DIR"] = d
    # Force module reload so config picks up new PW_DATA_DIR
    import importlib

    import app.config
    import app.db
    importlib.reload(app.config)
    importlib.reload(app.db)
    Path(d).mkdir(parents=True, exist_ok=True)


def test_app_boots_and_health() -> None:
    _setup_tmp()
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as client:
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True


def test_stats_and_monitors_empty() -> None:
    _setup_tmp()
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as client:
        s = client.get("/api/stats").json()
        assert s["total"] == 0
        assert s["monitors"] == 0
        m = client.get("/api/monitors").json()
        assert m == []


def test_monitor_crud() -> None:
    _setup_tmp()
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as client:
        created = client.post(
            "/api/monitors",
            json={
                "provider": "PyPI",
                "query": "requests",
                "interval_sec": 600,
                "fetch_mode": "pages",
                "fetch_pages": 1,
            },
        ).json()
        mid = created["id"]
        assert client.get(f"/api/monitors/{mid}").json()["query"] == "requests"
        patched = client.patch(
            f"/api/monitors/{mid}", json={"interval_sec": 900}
        ).json()
        assert patched["interval_sec"] == 900
        assert client.delete(f"/api/monitors/{mid}").json()["ok"] is True


def test_packages_query_filters_all_empty() -> None:
    _setup_tmp()
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as client:
        r = client.get(
            "/api/packages",
            params={
                "providers": "PyPI,npm",
                "min_size": 1000,
                "max_size": 10_000_000,
                "min_files": 1,
                "max_files": 5000,
                "search": "test",
                "sort_col": "size_bytes",
                "sort_asc": True,
                "page": 1,
                "per_page": 25,
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 0
        assert body["items"] == []
