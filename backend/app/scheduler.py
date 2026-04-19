"""Per-monitor scheduler: runs `do_fetch` on a timer, saves new packages, enqueues indexing."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from datetime import datetime

from . import db
from .fetchers import do_fetch
from .indexer_service import enqueue as enqueue_index


class Scheduler:
    def __init__(self, on_fetch: Callable[[int, int, int, str], None] | None = None) -> None:
        self._stops: dict[int, threading.Event] = {}
        self._on_fetch = on_fetch
        self._lock = threading.Lock()

    def start(self, monitor: dict) -> None:
        self.stop(int(monitor["id"]))
        ev = threading.Event()
        with self._lock:
            self._stops[int(monitor["id"])] = ev

        def _run() -> None:
            self._once(monitor)
            ticks = 0
            interval = max(10, int(monitor.get("interval_sec") or 300))
            while not ev.is_set():
                time.sleep(1)
                ticks += 1
                if ticks >= interval:
                    ticks = 0
                    m = db.get_monitor(int(monitor["id"]))
                    if not m or not m.get("enabled"):
                        break
                    self._once(m)

        threading.Thread(target=_run, daemon=True, name=f"sched-{monitor['id']}").start()

    def fire(self, monitor: dict) -> None:
        threading.Thread(
            target=self._once, args=(monitor,), daemon=True, name=f"fire-{monitor['id']}"
        ).start()

    def stop(self, mid: int) -> None:
        with self._lock:
            ev = self._stops.pop(mid, None)
        if ev:
            ev.set()

    def stop_all(self) -> None:
        with self._lock:
            events = list(self._stops.values())
            self._stops.clear()
        for ev in events:
            ev.set()

    def _once(self, monitor: dict) -> None:
        mid = int(monitor["id"])
        provider = monitor.get("provider") or ""
        providers = monitor.get("providers") or provider
        query = monitor.get("query") or ""
        mode = monitor.get("fetch_mode") or "pages"
        pages = int(monitor.get("fetch_pages") or 1)
        days = int(monitor.get("fetch_days") or 3)
        prov_list = [p.strip() for p in str(providers).split("|") if p.strip()]
        total_new = total_fetched = 0
        for prov in prov_list:
            try:
                pkgs = do_fetch(prov, query, mode, pages, days)
                total_fetched += len(pkgs)
                new = db.save_packages(prov, mid, query, pkgs, on_insert=enqueue_index)
                total_new += new
            except Exception as e:
                print(f"[scheduler] mid={mid} prov={prov}: {e!s:.120}")
        ts = datetime.now().strftime("%H:%M:%S")
        db.update_monitor_fetch(mid, total_new, ts)
        if self._on_fetch:
            try:
                self._on_fetch(mid, total_new, total_fetched, ts)
            except Exception:
                pass


_instance: Scheduler | None = None


def instance() -> Scheduler:
    global _instance
    if _instance is None:
        _instance = Scheduler()
    return _instance
