"""Parallel page orchestrator — fans out per-page fetch calls, merges results."""

from __future__ import annotations

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from ..utils import parse_dt

_EMPTY_ABORT = 4


def parallel_pages(
    fetch_fn: Callable[[str, int], list[dict]],
    query: str,
    max_pages: int,
    until_dt: datetime | None = None,
    max_workers: int = 6,
) -> list[dict]:
    lock = threading.Lock()
    stop = threading.Event()
    seen: set[str] = set()
    results: list[tuple[datetime, dict]] = []

    def absorb(pkgs: list[dict]) -> tuple[int, bool]:
        added = 0
        oldest = datetime.max.replace(tzinfo=timezone.utc)
        with lock:
            for p in pkgs:
                n = (p.get("name") or "").strip()
                if not n or n in seen:
                    continue
                seen.add(n)
                dt = parse_dt(p.get("published_at", "")) or datetime.min.replace(
                    tzinfo=timezone.utc
                )
                results.append((dt, p))
                added += 1
                if dt < oldest:
                    oldest = dt
        cutoff = (
            until_dt
            and oldest != datetime.max.replace(tzinfo=timezone.utc)
            and oldest < until_dt
        )
        return added, bool(cutoff)

    def run(pg: int) -> tuple[int, list[dict], bool]:
        if stop.is_set():
            return pg, [], False
        try:
            return pg, fetch_fn(query, pg) or [], True
        except Exception as e:
            print(f"[fetch] p{pg}: {e!s:.80}")
            return pg, [], False

    if not until_dt:
        streak = 0
        with ThreadPoolExecutor(
            max_workers=min(max_pages, max_workers), thread_name_prefix="pw"
        ) as ex:
            futs = [ex.submit(run, p) for p in range(1, max_pages + 1)]
            for fut in as_completed(futs):
                _, pkgs, _ = fut.result()
                added, _ = absorb(pkgs)
                streak = (streak + 1) if not added else 0
                if streak >= _EMPTY_ABORT:
                    stop.set()
                    for f in futs:
                        f.cancel()
                    break
    else:
        W = min(max_workers, 5)
        pg = 1
        streak = 0
        with ThreadPoolExecutor(max_workers=W, thread_name_prefix="pw") as ex:
            while not stop.is_set():
                futs = [ex.submit(run, p) for p in range(pg, pg + W)]
                for fut in as_completed(futs):
                    if stop.is_set():
                        for f in futs:
                            f.cancel()
                        break
                    _, pkgs, _ = fut.result()
                    added, cutoff = absorb(pkgs)
                    streak = (streak + 1) if not pkgs else 0
                    if cutoff or streak >= _EMPTY_ABORT:
                        stop.set()
                        for f in futs:
                            f.cancel()
                        break
                if stop.is_set():
                    break
                pg += W

    results.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in results]
