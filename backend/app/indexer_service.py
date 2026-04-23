"""Background indexer service: enqueues packages for deep-indexing + compliance."""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from datetime import datetime

from . import db, plugins
from .indexers import index_for
from .indexers.compliance import check_compliance, save_compliance

_q: queue.Queue | None = None
_thread: threading.Thread | None = None
_seen: set[tuple[str, str]] = set()
_log_cb: Callable[[str], None] | None = None


def set_log_callback(cb: Callable[[str], None] | None) -> None:
    global _log_cb
    _log_cb = cb


def _log(msg: str) -> None:
    if _log_cb:
        try:
            _log_cb(msg)
        except Exception:
            pass
    print(msg, flush=True)


def index_one(pkg_id: int, provider: str, name: str, force: bool = False, log: bool = True) -> dict:
    """Run deep-index on a single package; persist metadata + analysis snippets."""
    if not force:
        existing = db.get_pkg_metadata(pkg_id)
        if existing:
            try:
                score = int(existing.get("compliance_score", 0) or 0)
                if score >= 90:
                    indexed_at = existing.get("indexed_at", "2000-01-01") or "2000-01-01"
                    age = (datetime.now() - datetime.fromisoformat(str(indexed_at))).total_seconds()
                    if age < 8 * 3600:
                        return check_compliance(pkg_id)
            except Exception:
                pass

    bundle = index_for(provider, name)
    if bundle.get("error"):
        if "429" not in str(bundle["error"]):
            if log:
                _log(f"⚠ [{provider}·{name[:30]}]: {str(bundle['error'])[:80]}")
        return check_compliance(pkg_id)

    fields: dict = {}
    for key in (
        "readme_text",
        "deps_json",
        "versions_json",
        "file_tree_json",
        "meta_json",
        "stars",
        "forks",
        "open_issues",
        "license_spdx",
        "homepage",
        "topics_json",
    ):
        if key in bundle and bundle[key] is not None:
            fields[key] = bundle[key]

    core = ("description", "version", "language", "size_bytes", "file_count", "published_at", "author")
    pkg = db.get_package(pkg_id) or {}
    updates: dict = {}
    for k in core:
        v = bundle.get(k)
        if not v:
            continue
        existing_val = pkg.get(k)
        if isinstance(v, str) and not (existing_val or "").strip():
            updates[k] = v
        elif not isinstance(v, str) and not existing_val:
            updates[k] = v

    if updates:
        with db.connect() as c:
            sets = ", ".join(f"{k}=?" for k in updates)
            c.execute(
                f"UPDATE packages SET {sets} WHERE id=?",
                list(updates.values()) + [pkg_id],
            )

    readme = bundle.get("readme_text", "")
    if readme:
        db.set_analysis(pkg_id, "README", readme)

    deps = bundle.get("deps_json") or {}
    if isinstance(deps, dict) and any(deps.values()):
        parts: list[str] = []
        for label, key in [
            ("Runtime", "dependencies"),
            ("Dev", "dev_deps"),
            ("Peer", "peer_deps"),
        ]:
            dd = deps.get(key) or []
            if dd:
                parts.append(f"### {label} ({len(dd)})\n")
                parts.extend(f"  • {d}" for d in dd)
                parts.append("")
        if parts:
            db.set_analysis(pkg_id, "Dependencies", "\n".join(parts))

    versions = bundle.get("versions_json") or []
    if versions:
        cur = bundle.get("version", "") or ""
        rows = [
            f"{'Version':<22} {'Date':<12} {'Size':<10} Note",
            "─" * 60,
        ]
        for v in versions[:60]:
            ver = v.get("version", "")
            date = (v.get("date", "") or "")[:10]
            size = v.get("size", 0)
            note = "← latest" if ver == cur else ("yanked" if v.get("yanked") else "")
            rows.append(f"{ver:<22} {date:<12} {size:<10} {note}")
        db.set_analysis(pkg_id, "Versions", "\n".join(rows))

    db.set_pkg_metadata(pkg_id, **fields)

    # Auto-run all cacheable analysis plugins so the full state lives in DB.
    _run_all_plugins(pkg_id)
    db.set_pkg_metadata(pkg_id, last_full_indexed_at=datetime.now().isoformat(timespec="seconds"))

    comp = check_compliance(pkg_id)
    save_compliance(pkg_id, comp)
    if log:
        score = comp.get("score", 0)
        icon = "✅" if score == 100 else ("🟡" if score >= 60 else "🔴")
        _log(f"{icon} [{provider}·{name[:30]}]  {score}/100")
    return comp


def _run_all_plugins(pkg_id: int) -> None:
    pkg = db.get_package(pkg_id)
    meta = db.get_pkg_metadata(pkg_id) or {}
    if not pkg:
        return
    for plugin in plugins.iter_plugins():
        if not plugin.cache:
            continue
        try:
            existing = db.get_analysis(pkg_id, plugin.id)
            if existing:
                continue
            out = plugin.run(pkg, meta)
            if out:
                db.set_analysis(pkg_id, plugin.id, out)
        except Exception as e:
            _log(f"[plugin {plugin.id}] {pkg.get('provider')}/{pkg.get('name')}: {e!s:.80}")


def _get_q() -> queue.Queue:
    global _q, _thread
    if _q is None:
        _q = queue.Queue(maxsize=5000)
        _thread = threading.Thread(target=_worker, daemon=True, name="meta-indexer")
        _thread.start()
    return _q


def _worker() -> None:
    q = _get_q()
    while True:
        try:
            item = q.get(timeout=10)
        except Exception:
            continue
        pkg_id, provider, name = item
        key = (provider, name)
        if key in _seen:
            q.task_done()
            continue
        _seen.add(key)
        try:
            index_one(pkg_id, provider, name, force=False, log=True)
        except Exception as e:
            _log(f"[indexer] {provider}/{name}: {e!s:.80}")
        finally:
            q.task_done()


def enqueue(pkg_id: int, provider: str, name: str) -> None:
    try:
        _get_q().put_nowait((pkg_id, provider, name))
    except Exception:
        pass
