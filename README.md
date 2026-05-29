# Bookmark Backup

Small **ETL pipeline** for browser bookmarks: import from Chromium JSON files and exported HTML, deduplicate by normalized URL, store in **PostgreSQL**, and browse/import via a simple **FastAPI** web UI.


## Architecture

```
JSON/HTML bookmark files  →  Importers  →  normalize_url()  →  PostgreSQL
                                                      ↘      ↘ Folder tree
                                                        FastAPI web UI
```

**Deduplication rules** (`normalize_url`):

- Lowercase scheme and host
- Strip `www.`
- Remove URL fragment
- Remove trailing slash (except root `/`)
- Sort query parameters
- Drop default ports (80/443)

Re-importing the same bookmarks skips rows that already exist (unique index on `href_normalized`).

## Requirements

- Python 3.11+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for local PostgreSQL)
- Chrome (optional; for live import from your profile)

## Quick start (PyCharm or terminal)

### 1. Virtual environment and install

```powershell
cd c:\projekty\BookmarkBackup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

In **PyCharm**: *File → Settings → Project → Python Interpreter* → add `.venv` interpreter.

### 2. Environment

It is required to set connection to database in file `.env`.

### 3. Start PostgreSQL

```powershell
docker compose up -d
```

### 4. Run migrations

```powershell
alembic upgrade head
```

### 5. Import bookmarks (CLI)

Close browser first (or copy the `Bookmarks` file to another path and use `--path`).

```powershell
bookmark-backup import-chrome
# or explicitly:
bookmark-backup import-chrome --path "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Bookmarks"

# import HTML export or any JSON bookmarks file:
bookmark-backup import-file --path "tests\fixtures\sample_edge_bookmarks.html"
```

### 6. Web UI (React + TypeScript)

**Development (recommended):** run API and frontend separately.

Terminal 1 — API:
```powershell
bookmark-backup serve
```

Terminal 2 — React UI:
```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 (Vite proxies `/api` to port 8000).

**Production-style (single server):**
```powershell
cd frontend
npm install
npm run build
cd ..
bookmark-backup serve
```

Open http://127.0.0.1:8000

The left sidebar shows the **folder + bookmark tree** with drag-and-drop move, rename, and delete.

Use the **Import bookmarks** panel in the details column to upload `.html`/JSON files or paste local paths (one per line), for example:
- `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Bookmarks`
- `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Bookmarks`

### 7. Tests

```powershell
pytest
```

## CLI commands

| Command | Description |
|---------|-------------|
| `bookmark-backup import-chrome` | Import from Chromium JSON profile file |
| `bookmark-backup import-file --path ...` | Import from `.html` export or JSON file |
| `bookmark-backup stats` | Count bookmarks in DB |
| `bookmark-backup serve` | Start web UI |

## Project layout

```
src/bookmark_backup/
  importers/             # JSON + HTML extract
  services/              # dedupe + import
  db/models.py
  web/app.py             # FastAPI app + static SPA
  web/api.py             # REST API for React UI
  web/import_handlers.py # multipart import for /api/import
  cli.py
frontend/                # React + TypeScript (Vite)
tests/
alembic/
```

## License

MIT
