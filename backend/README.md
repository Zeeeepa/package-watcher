# package-watcher · backend

FastAPI service for aggregating and exploring packages across PyPI / npm / GitHub / DockerHub / Libraries.io / WebURL.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m app.main
```

API is served at http://0.0.0.0:7433. The SQLite database lives at `$PW_DATA_DIR/packages.db` (default `~/.package-watcher/packages.db`).

## Endpoints (short summary)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Health probe |
| GET | `/api/stats` | Dashboard totals |
| GET | `/api/stats/meta` | Provider/language colour maps |
| GET | `/api/stats/histogram/sizes` | Size-distribution histogram |
| GET | `/api/stats/histogram/files` | File-count histogram |
| GET | `/api/stats/timeline?days=90` | Daily publish counts |
| GET | `/api/stats/languages?limit=20` | Top languages |
| GET/POST | `/api/monitors` | List / create monitors |
| GET/PATCH/DELETE | `/api/monitors/{id}` | Read / update / delete a monitor |
| POST | `/api/monitors/{id}/trigger` | Fire a monitor once immediately |
| POST | `/api/monitors/{id}/enable` | Enable/disable |
| GET | `/api/packages` | Query packages (filters + sort + pagination) |
| GET | `/api/packages/{id}` | Stored metadata for a package |
| GET | `/api/packages/{id}/live` | Live registry fetch |
| POST | `/api/packages/{id}/download` | Download archive |
| POST | `/api/packages/delete` | Bulk delete |
| GET | `/api/analysis/plugins` | List available analysis plugins |
| GET | `/api/analysis/{pkg_id}/{plugin_id}` | Run plugin (cached) |
| POST | `/api/analysis/{pkg_id}/reindex` | Force re-indexing |
| GET | `/api/feeds/detect?url=…` | Detect a WebURL feed |

### Query parameters for `/api/packages`

- `page`, `per_page` (≤ 500, default 50)
- `sort_col` (whitelisted), `sort_asc`
- `providers` / `languages` — comma-separated filter
- `search` — case-insensitive name/description match
- `min_size` / `max_size` — bytes
- `min_files` / `max_files`
- `published_after` / `published_before` — ISO-8601
- `new_only` (last 30 days) / `dl_only` (already downloaded)
- `monitor_id` — filter to a monitor
