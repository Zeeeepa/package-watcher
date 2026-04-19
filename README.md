# package-watcher

Aggregate, explore, and filter package releases across **PyPI**, **npm**, **GitHub**,
**DockerHub**, **Libraries.io**, and arbitrary **web URLs / RSS feeds** — from a
single fast UI.

- Backend: **FastAPI** (Python 3.10+), SQLite, one binary API surface.
- Frontend: **Vite + React + TypeScript**, no framework lock-in.

## Why

The original app was a ~6 600-line PyQt5 monolith that mixed fetchers, DB, and UI.
This split gives you:

- A real REST API you can drive from anywhere (not just the desktop).
- A fast web UI with filter-by-size / file-count / publish-date, sorting, and
  exploratory charts (size, file, timeline, language distribution).
- Zero-DB-setup: SQLite at `~/.package-watcher/packages.db`.

## Monorepo layout

```
backend/   FastAPI service (fetchers, DB, analysis plugins, deep-meta)
frontend/  React UI (Vite, TypeScript, Recharts)
```

## Run it

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
python -m app.main              # http://localhost:7433
```

### Frontend

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173 (proxies /api → :7433)
```

Open <http://localhost:5173>.

## Feature parity with the legacy monolith

- Providers: PyPI, npm, GitHub, DockerHub, Libraries.io, WebURL
- Parallel paged fetch with date-cutoff early termination
- Enrichment (size / file-count / language) from registry APIs
- Deep indexing: README, deps, versions, file-tree, meta
- Compliance scoring (0–100) with per-field flags
- Analysis plugins: FileTree, Dependencies, Readme, Versions, CodeStats,
  Security, Complexity, DepGraph, AI summary
- Per-monitor scheduler: interval, `by-pages` or `by-days`
- Package download (archive to `~/.package-watcher/downloads`)

## Frontend capabilities

- Sidebar list of monitors with start / pause / trigger / delete
- **Add Monitor** dialog: multi-source checkboxes, query / URL, interval
  (seconds), fetch mode (pages or days), result count
- Package card grid with rich metadata: provider, language, version, size,
  file count, compliance score, stars, downloaded flag
- Filter toolbar: full-text search, provider chips, size range (bytes),
  file-count range, publish-date range, "last-30-days" toggle, sort column
  and direction
- Detail panel with all 9 analysis tabs, Re-index, Download, live-meta
- Exploratory charts: size histogram, file histogram, 90-day publish
  timeline, top 12 languages (color-coded)

## Environment

| Var | Default | Description |
|---|---|---|
| `PW_DATA_DIR` | `~/.package-watcher` | Where DB and downloads live |
| `PW_HOST` | `0.0.0.0` | Bind host |
| `PW_PORT` | `7433` | Bind port |
| `PW_BACKEND_URL` | `http://localhost:7433` | Used by Vite proxy at dev time |

## Development

```bash
# backend
cd backend && source .venv/bin/activate
python -m ruff check app tests
python -m pytest tests

# frontend
cd frontend
npm run typecheck
npm run build
```

## License

MIT
