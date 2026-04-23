"""SQLite persistence: monitors, packages, analysis cache, package metadata."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from .config import DB_PATH


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    c = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
    c.row_factory = sqlite3.Row
    try:
        yield c
    finally:
        c.close()


def init() -> None:
    with connect() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS monitors (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                provider     TEXT    NOT NULL,
                providers    TEXT,
                query        TEXT    NOT NULL,
                enabled      INTEGER DEFAULT 1,
                interval_sec INTEGER DEFAULT 300,
                fetch_mode   TEXT    DEFAULT 'pages',
                fetch_pages  INTEGER DEFAULT 1,
                fetch_days   INTEGER DEFAULT 3,
                last_ts      TEXT,
                last_new     INTEGER DEFAULT 0,
                total_saved  INTEGER DEFAULT 0,
                created_at   TEXT    DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS packages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                provider        TEXT    NOT NULL,
                monitor_id      INTEGER,
                query           TEXT,
                name            TEXT    NOT NULL,
                description     TEXT,
                url             TEXT,
                author          TEXT,
                version         TEXT,
                published_at    TEXT,
                size_bytes      INTEGER,
                file_count      INTEGER,
                language        TEXT,
                download_path   TEXT,
                download_status TEXT    DEFAULT 'none',
                fetched_at      TEXT    DEFAULT CURRENT_TIMESTAMP,
                sources_json    TEXT,
                UNIQUE(provider, name)
            );
            CREATE TABLE IF NOT EXISTS analysis_cache (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                package_id INTEGER NOT NULL,
                plugin     TEXT    NOT NULL,
                result     TEXT,
                created_at TEXT    DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(package_id, plugin)
            );
            CREATE TABLE IF NOT EXISTS package_metadata (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                package_id      INTEGER NOT NULL UNIQUE,
                file_tree_json  TEXT,
                readme_text     TEXT,
                deps_json       TEXT,
                versions_json   TEXT,
                meta_json       TEXT,
                stars           INTEGER DEFAULT 0,
                forks           INTEGER DEFAULT 0,
                open_issues     INTEGER DEFAULT 0,
                license_spdx    TEXT,
                homepage        TEXT,
                topics_json     TEXT,
                indexed_at      TEXT    DEFAULT CURRENT_TIMESTAMP,
                compliance_score INTEGER DEFAULT 0,
                compliance_flags TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_pkg_meta     ON package_metadata(package_id);
            CREATE INDEX IF NOT EXISTS idx_pkg_prov     ON packages(provider);
            CREATE INDEX IF NOT EXISTS idx_pkg_name     ON packages(name);
            CREATE INDEX IF NOT EXISTS idx_pkg_lang     ON packages(language);
            CREATE INDEX IF NOT EXISTS idx_pkg_pub      ON packages(published_at);
            CREATE INDEX IF NOT EXISTS idx_pkg_size     ON packages(size_bytes);
            CREATE INDEX IF NOT EXISTS idx_pkg_files    ON packages(file_count);
            CREATE INDEX IF NOT EXISTS idx_analysis_pkg ON analysis_cache(package_id);
            """
        )
        _migrate(c)


def _migrate(c: sqlite3.Connection) -> None:
    """Idempotent column-add migrations for upgrades from older DBs."""
    cols = {r["name"] for r in c.execute("PRAGMA table_info(packages)")}
    if "raw_json" not in cols:
        c.execute("ALTER TABLE packages ADD COLUMN raw_json TEXT")
    meta_cols = {r["name"] for r in c.execute("PRAGMA table_info(package_metadata)")}
    if "all_analyses_json" not in meta_cols:
        c.execute("ALTER TABLE package_metadata ADD COLUMN all_analyses_json TEXT")
    if "last_full_indexed_at" not in meta_cols:
        c.execute("ALTER TABLE package_metadata ADD COLUMN last_full_indexed_at TEXT")


# ── Monitors ───────────────────────────────────────────────────────────────────

def all_monitors() -> list[dict]:
    with connect() as c:
        return [dict(r) for r in c.execute("SELECT * FROM monitors ORDER BY id")]


def get_monitor(mid: int) -> dict | None:
    with connect() as c:
        r = c.execute("SELECT * FROM monitors WHERE id=?", (mid,)).fetchone()
        return dict(r) if r else None


def add_monitor(
    provider: str,
    query: str,
    interval_sec: int = 300,
    fetch_mode: str = "pages",
    fetch_pages: int = 1,
    fetch_days: int = 3,
    providers: str | None = None,
) -> int:
    with connect() as c:
        cur = c.execute(
            "INSERT INTO monitors (provider, providers, query, enabled, interval_sec,"
            " fetch_mode, fetch_pages, fetch_days) VALUES(?,?,?,1,?,?,?,?)",
            (
                provider,
                providers or provider,
                query,
                interval_sec,
                fetch_mode,
                fetch_pages,
                fetch_days,
            ),
        )
        return int(cur.lastrowid)


def delete_monitor(mid: int) -> None:
    with connect() as c:
        c.execute("DELETE FROM monitors WHERE id=?", (mid,))


def set_monitor_enabled(mid: int, enabled: bool) -> None:
    with connect() as c:
        c.execute("UPDATE monitors SET enabled=? WHERE id=?", (int(enabled), mid))


def update_monitor_fetch(mid: int, new_count: int, ts: str) -> None:
    with connect() as c:
        c.execute(
            "UPDATE monitors SET last_ts=?, last_new=?, total_saved=total_saved+? "
            "WHERE id=?",
            (ts, new_count, new_count, mid),
        )


_MONITOR_PATCH_FIELDS = {
    "enabled",
    "interval_sec",
    "fetch_mode",
    "fetch_pages",
    "fetch_days",
    "providers",
    "provider",
    "query",
}


def patch_monitor(mid: int, **fields: Any) -> None:
    assignments, values = [], []
    for k, v in fields.items():
        if k in _MONITOR_PATCH_FIELDS and v is not None:
            assignments.append(f"{k}=?")
            values.append(v)
    if not assignments:
        return
    values.append(mid)
    with connect() as c:
        c.execute(
            f"UPDATE monitors SET {','.join(assignments)} WHERE id=?",
            values,
        )


# ── Packages ──────────────────────────────────────────────────────────────────

def save_packages(
    provider: str,
    monitor_id: int | None,
    query: str,
    pkgs: Iterable[dict],
    on_insert: Any = None,
) -> int:
    pkgs = list(pkgs)
    if not pkgs:
        return 0
    now = datetime.now().isoformat(timespec="seconds")
    new = 0
    with connect() as c:
        for p in pkgs:
            name = (p.get("name") or "").strip()
            if not name:
                continue
            lib_source = p.get("_lib_source", "")
            if provider == "Libraries.io" and lib_source:
                existing = c.execute(
                    "SELECT id FROM packages WHERE provider=? AND name=?",
                    (lib_source, name),
                ).fetchone()
                if existing:
                    _add_source(c, lib_source, name, f"LIB+{lib_source}")
                    continue
                lib_existing = c.execute(
                    "SELECT id FROM packages WHERE provider='Libraries.io' AND name=?",
                    (name,),
                ).fetchone()
                if lib_existing:
                    continue
            raw_json = json.dumps(p, default=str)
            cur = c.execute(
                "INSERT OR IGNORE INTO packages "
                "(provider, monitor_id, query, name, description, url, author, version,"
                " published_at, size_bytes, file_count, language, fetched_at, sources_json, raw_json)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    provider,
                    monitor_id,
                    query,
                    name,
                    p.get("description", ""),
                    p.get("url", ""),
                    p.get("author", ""),
                    p.get("version", ""),
                    p.get("published_at", ""),
                    p.get("size_bytes"),
                    p.get("file_count"),
                    p.get("language", ""),
                    now,
                    json.dumps([f"LIB+{lib_source}"]) if lib_source else None,
                    raw_json,
                ),
            )
            if cur.rowcount:
                new += 1
                if on_insert is not None:
                    try:
                        on_insert(int(cur.lastrowid), provider, name)
                    except Exception:
                        pass
            else:
                c.execute(
                    "UPDATE packages SET "
                    " description = COALESCE(NULLIF(description,''), ?),"
                    " size_bytes  = COALESCE(size_bytes, ?),"
                    " file_count  = COALESCE(file_count, ?),"
                    " language    = COALESCE(NULLIF(language,''), ?),"
                    " version     = COALESCE(NULLIF(version,''), ?)"
                    " WHERE provider=? AND name=?",
                    (
                        p.get("description", ""),
                        p.get("size_bytes"),
                        p.get("file_count"),
                        p.get("language", ""),
                        p.get("version", ""),
                        provider,
                        name,
                    ),
                )
    return new


_SAFE_SORT_COLS = {
    "name",
    "description",
    "version",
    "author",
    "published_at",
    "fetched_at",
    "provider",
    "size_bytes",
    "file_count",
    "language",
    "download_status",
}


def _build_where(
    provider: str | None,
    query: str | None,
    search: str,
    providers_filter: list[str] | None,
    languages_filter: list[str] | None,
    min_size: int | None,
    max_size: int | None,
    min_files: int | None,
    max_files: int | None,
    published_after: str | None,
    published_before: str | None,
    new_only: bool,
    dl_only: bool,
    monitor_id: int | None,
) -> tuple[str, list[Any]]:
    conds: list[str] = []
    params: list[Any] = []
    if providers_filter:
        ph = ",".join("?" * len(providers_filter))
        conds.append(f"provider IN ({ph})")
        params += list(providers_filter)
    elif provider:
        conds.append("provider=?")
        params.append(provider)
    if languages_filter:
        ph = ",".join("?" * len(languages_filter))
        conds.append(f"language IN ({ph})")
        params += list(languages_filter)
    if query:
        conds.append("query=?")
        params.append(query)
    if search:
        conds.append("(LOWER(name) LIKE ? OR LOWER(description) LIKE ?)")
        s = f"%{search.lower()}%"
        params += [s, s]
    if min_size is not None:
        conds.append("size_bytes >= ?")
        params.append(min_size)
    if max_size is not None:
        conds.append("size_bytes <= ?")
        params.append(max_size)
    if min_files is not None:
        conds.append("file_count >= ?")
        params.append(min_files)
    if max_files is not None:
        conds.append("file_count <= ?")
        params.append(max_files)
    if published_after:
        conds.append("published_at >= ?")
        params.append(published_after)
    if published_before:
        conds.append("published_at <= ?")
        params.append(published_before)
    if new_only:
        conds.append("published_at >= datetime('now','-30 days')")
    if dl_only:
        conds.append("download_status='done'")
    if monitor_id is not None:
        conds.append("monitor_id=?")
        params.append(monitor_id)
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    return where, params


def count_packages(**filters: Any) -> int:
    where, params = _build_where(
        provider=filters.get("provider"),
        query=filters.get("query"),
        search=filters.get("search", ""),
        providers_filter=filters.get("providers_filter"),
        languages_filter=filters.get("languages_filter"),
        min_size=filters.get("min_size"),
        max_size=filters.get("max_size"),
        min_files=filters.get("min_files"),
        max_files=filters.get("max_files"),
        published_after=filters.get("published_after"),
        published_before=filters.get("published_before"),
        new_only=bool(filters.get("new_only", False)),
        dl_only=bool(filters.get("dl_only", False)),
        monitor_id=filters.get("monitor_id"),
    )
    with connect() as c:
        row = c.execute(f"SELECT COUNT(*) AS n FROM packages {where}", params).fetchone()
        return int(row["n"])


def get_packages(
    page: int = 1,
    per_page: int = 50,
    sort_col: str = "published_at",
    sort_asc: bool = False,
    **filters: Any,
) -> list[dict]:
    if sort_col not in _SAFE_SORT_COLS:
        sort_col = "published_at"
    where, params = _build_where(
        provider=filters.get("provider"),
        query=filters.get("query"),
        search=filters.get("search", ""),
        providers_filter=filters.get("providers_filter"),
        languages_filter=filters.get("languages_filter"),
        min_size=filters.get("min_size"),
        max_size=filters.get("max_size"),
        min_files=filters.get("min_files"),
        max_files=filters.get("max_files"),
        published_after=filters.get("published_after"),
        published_before=filters.get("published_before"),
        new_only=bool(filters.get("new_only", False)),
        dl_only=bool(filters.get("dl_only", False)),
        monitor_id=filters.get("monitor_id"),
    )
    order = f"ORDER BY {sort_col} IS NULL, {sort_col} {'ASC' if sort_asc else 'DESC'}"
    sql = (
        "SELECT p.id, p.name, p.description, p.version, p.author, p.published_at,"
        " p.fetched_at, p.provider, p.size_bytes, p.file_count, p.language,"
        " p.download_status, p.url, p.sources_json,"
        " COALESCE(m.compliance_score, 0) AS compliance_score,"
        " COALESCE(m.stars, 0) AS stars,"
        " (CASE WHEN p.published_at >= datetime('now','-30 days') THEN 1 ELSE 0 END) AS is_new "
        " FROM packages p"
        " LEFT JOIN package_metadata m ON m.package_id = p.id"
        f" {where} {order} LIMIT ? OFFSET ?"
    )
    with connect() as c:
        rows = c.execute(sql, params + [per_page, (page - 1) * per_page]).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            srcs = d.pop("sources_json", None)
            try:
                d["sources"] = json.loads(srcs) if srcs else []
            except Exception:
                d["sources"] = []
            out.append(d)
        return out


def get_package(pkg_id: int) -> dict | None:
    with connect() as c:
        r = c.execute("SELECT * FROM packages WHERE id=?", (pkg_id,)).fetchone()
        if not r:
            return None
        d = dict(r)
        for key in ("raw_json", "sources_json"):
            if d.get(key) and isinstance(d[key], str):
                try:
                    d[key] = json.loads(d[key])
                except Exception:
                    pass
        return d


def get_package_full(pkg_id: int) -> dict | None:
    """Package + metadata + all cached analyses in one blob."""
    pkg = get_package(pkg_id)
    if not pkg:
        return None
    meta = get_pkg_metadata(pkg_id) or {}
    with connect() as c:
        rows = c.execute(
            "SELECT plugin, result, created_at FROM analysis_cache WHERE package_id=?",
            (pkg_id,),
        ).fetchall()
    analyses = {r["plugin"]: {"result": r["result"], "created_at": r["created_at"]} for r in rows}
    return {"package": pkg, "metadata": meta, "analyses": analyses}


def delete_packages(ids: list[int]) -> int:
    if not ids:
        return 0
    with connect() as c:
        ph = ",".join("?" * len(ids))
        return int(
            c.execute(f"DELETE FROM packages WHERE id IN ({ph})", ids).rowcount
        )


def update_download(pkg_id: int, status: str, path: str | None = None) -> None:
    with connect() as c:
        c.execute(
            "UPDATE packages SET download_status=?, download_path=? WHERE id=?",
            (status, path, pkg_id),
        )


def update_enrichment(
    pkg_id: int,
    size_bytes: int | None = None,
    file_count: int | None = None,
    language: str | None = None,
) -> None:
    with connect() as c:
        c.execute(
            "UPDATE packages SET size_bytes=?, file_count=?, language=? WHERE id=?",
            (size_bytes, file_count, language, pkg_id),
        )


def total_packages() -> int:
    with connect() as c:
        return int(
            c.execute("SELECT COUNT(*) AS n FROM packages").fetchone()["n"]
        )


def stats() -> dict:
    with connect() as c:
        total = int(c.execute("SELECT COUNT(*) AS n FROM packages").fetchone()["n"])
        by_prov = {
            r["provider"]: r["c"]
            for r in c.execute(
                "SELECT provider, COUNT(*) AS c FROM packages GROUP BY provider"
            )
        }
        mon_row = c.execute(
            "SELECT COUNT(*) AS n, SUM(enabled) AS a FROM monitors"
        ).fetchone()
        dl = int(
            c.execute(
                "SELECT COUNT(*) AS n FROM packages WHERE download_status='done'"
            ).fetchone()["n"]
        )
        comp_avg_row = c.execute(
            "SELECT AVG(COALESCE(compliance_score,0)) AS a FROM package_metadata"
        ).fetchone()
    return {
        "total": total,
        "by_provider": by_prov,
        "monitors": int(mon_row["n"] or 0),
        "active_monitors": int(mon_row["a"] or 0),
        "downloaded": dl,
        "avg_compliance": round(float(comp_avg_row["a"] or 0), 1),
    }


# ── Histograms / exploratory aggregates ───────────────────────────────────────

def histogram_sizes(buckets: list[int]) -> list[dict]:
    out = []
    with connect() as c:
        for i in range(len(buckets) - 1):
            lo, hi = buckets[i], buckets[i + 1]
            n = c.execute(
                "SELECT COUNT(*) AS n FROM packages "
                "WHERE size_bytes >= ? AND size_bytes < ?",
                (lo, hi),
            ).fetchone()["n"]
            out.append({"lo": lo, "hi": hi, "count": int(n)})
    return out


def histogram_files(buckets: list[int]) -> list[dict]:
    out = []
    with connect() as c:
        for i in range(len(buckets) - 1):
            lo, hi = buckets[i], buckets[i + 1]
            n = c.execute(
                "SELECT COUNT(*) AS n FROM packages "
                "WHERE file_count >= ? AND file_count < ?",
                (lo, hi),
            ).fetchone()["n"]
            out.append({"lo": lo, "hi": hi, "count": int(n)})
    return out


def timeline_published(days: int = 90) -> list[dict]:
    with connect() as c:
        rows = c.execute(
            "SELECT substr(published_at,1,10) AS d, COUNT(*) AS n "
            "FROM packages "
            "WHERE published_at >= date('now', ?) "
            "GROUP BY substr(published_at,1,10) "
            "ORDER BY d",
            (f"-{days} days",),
        ).fetchall()
    return [{"date": r["d"], "count": int(r["n"])} for r in rows if r["d"]]


def top_starred(limit: int = 20) -> list[dict]:
    with connect() as c:
        rows = c.execute(
            "SELECT p.id, p.provider, p.name, p.language, p.version,"
            " COALESCE(m.stars, 0) AS stars, COALESCE(m.compliance_score, 0) AS score"
            " FROM packages p LEFT JOIN package_metadata m ON m.package_id = p.id"
            " ORDER BY stars DESC, score DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def top_compliance(limit: int = 20) -> list[dict]:
    with connect() as c:
        rows = c.execute(
            "SELECT p.id, p.provider, p.name, p.language, p.version,"
            " COALESCE(m.stars, 0) AS stars, COALESCE(m.compliance_score, 0) AS score"
            " FROM packages p INNER JOIN package_metadata m ON m.package_id = p.id"
            " WHERE m.compliance_score > 0"
            " ORDER BY score DESC, stars DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def catalog_rows(limit: int = 500, offset: int = 0, search: str = "") -> list[dict]:
    conds = []
    params: list[Any] = []
    if search:
        conds.append("(LOWER(p.name) LIKE ? OR LOWER(p.description) LIKE ?)")
        s = f"%{search.lower()}%"
        params += [s, s]
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    sql = (
        "SELECT p.id, p.provider, p.name, p.description, p.version, p.language,"
        " p.published_at, p.fetched_at, p.size_bytes, p.file_count, p.url,"
        " p.download_status,"
        " COALESCE(m.stars, 0) AS stars, COALESCE(m.forks, 0) AS forks,"
        " COALESCE(m.compliance_score, 0) AS compliance_score,"
        " m.license_spdx, m.homepage, m.last_full_indexed_at"
        " FROM packages p LEFT JOIN package_metadata m ON m.package_id = p.id"
        f" {where} ORDER BY p.fetched_at DESC LIMIT ? OFFSET ?"
    )
    params += [limit, offset]
    with connect() as c:
        rows = c.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def top_languages(limit: int = 20) -> list[dict]:
    with connect() as c:
        rows = c.execute(
            "SELECT COALESCE(NULLIF(language,''),'Unknown') AS language, "
            " COUNT(*) AS n "
            "FROM packages GROUP BY language ORDER BY n DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [{"language": r["language"], "count": int(r["n"])} for r in rows]


# ── Analysis cache ───────────────────────────────────────────────────────────

def get_analysis(pkg_id: int, plugin: str) -> str | None:
    with connect() as c:
        r = c.execute(
            "SELECT result FROM analysis_cache WHERE package_id=? AND plugin=?",
            (pkg_id, plugin),
        ).fetchone()
        return r["result"] if r else None


def set_analysis(pkg_id: int, plugin: str, result: str) -> None:
    with connect() as c:
        c.execute(
            "INSERT OR REPLACE INTO analysis_cache (package_id, plugin, result) "
            "VALUES(?, ?, ?)",
            (pkg_id, plugin, result),
        )


# ── Package metadata ─────────────────────────────────────────────────────────

def get_pkg_metadata(pkg_id: int) -> dict | None:
    with connect() as c:
        r = c.execute(
            "SELECT * FROM package_metadata WHERE package_id=?", (pkg_id,)
        ).fetchone()
        if not r:
            return None
        d = dict(r)
        for key in ("deps_json", "versions_json", "meta_json", "topics_json", "file_tree_json"):
            if d.get(key) and isinstance(d[key], str):
                try:
                    d[key] = json.loads(d[key])
                except Exception:
                    pass
        return d


def set_pkg_metadata(pkg_id: int, **fields: Any) -> None:
    serialized: dict[str, Any] = {}
    for k, v in fields.items():
        if v is None:
            continue
        if k in {"deps_json", "versions_json", "meta_json", "file_tree_json", "topics_json"} \
                and not isinstance(v, str):
            serialized[k] = json.dumps(v, default=str)
        else:
            serialized[k] = v
    if not serialized:
        return
    cols = ", ".join(serialized.keys())
    placeholders = ", ".join("?" * len(serialized))
    on_conflict = ", ".join(f"{k}=excluded.{k}" for k in serialized)
    with connect() as c:
        c.execute(
            f"INSERT INTO package_metadata (package_id, {cols}, indexed_at) "
            f"VALUES(?, {placeholders}, datetime('now')) "
            f"ON CONFLICT(package_id) DO UPDATE SET {on_conflict}, indexed_at=datetime('now')",
            [pkg_id] + list(serialized.values()),
        )


def _add_source(c: sqlite3.Connection, provider: str, name: str, tag: str) -> None:
    r = c.execute(
        "SELECT sources_json FROM packages WHERE provider=? AND name=?",
        (provider, name),
    ).fetchone()
    sources: list[str] = []
    if r and r["sources_json"]:
        try:
            sources = json.loads(r["sources_json"])
        except Exception:
            sources = []
    if tag not in sources:
        sources.append(tag)
        c.execute(
            "UPDATE packages SET sources_json=? WHERE provider=? AND name=?",
            (json.dumps(sources), provider, name),
        )


def save_compliance(pkg_id: int, score: int, flags: dict) -> None:
    with connect() as c:
        c.execute(
            "INSERT INTO package_metadata (package_id, compliance_score, compliance_flags, indexed_at)"
            " VALUES(?, ?, ?, datetime('now'))"
            " ON CONFLICT(package_id) DO UPDATE SET"
            "   compliance_score = excluded.compliance_score,"
            "   compliance_flags = excluded.compliance_flags,"
            "   indexed_at       = excluded.indexed_at",
            (pkg_id, score, json.dumps(flags)),
        )


def packages_needing_enrichment(incomplete_only: bool = True) -> list[dict]:
    with connect() as c:
        if incomplete_only:
            rows = c.execute(
                "SELECT p.id, p.provider, p.name, COALESCE(m.compliance_score, 0) AS score"
                " FROM packages p"
                " LEFT JOIN package_metadata m ON m.package_id = p.id"
                " WHERE m.package_id IS NULL"
                "    OR COALESCE(m.compliance_score, 0) < 60"
                " ORDER BY p.published_at DESC"
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT p.id, p.provider, p.name, COALESCE(m.compliance_score, 0) AS score"
                " FROM packages p"
                " LEFT JOIN package_metadata m ON m.package_id = p.id"
                " WHERE COALESCE(m.compliance_score, 0) < 100"
                " ORDER BY p.published_at DESC"
            ).fetchall()
    return [dict(r) for r in rows]
