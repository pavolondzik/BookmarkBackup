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

## Quick start

### 1. Virtual environment and install

```powershell
cd c:\projekty\BookmarkBackup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

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

Close the browser first (or copy the `Bookmarks` file elsewhere and pass `--path`), then run one of the import commands below. See [CLI reference](#cli-bookmark-backup) for all commands, options, and how the CLI compares to the web UI.

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

## CLI (`bookmark-backup`)

The CLI is a thin wrapper around the same import pipeline as the web UI: **importers** → **`ImportService`** → PostgreSQL (with URL deduplication). It does **not** browse or edit the bookmark tree; use the web UI for that.

After `pip install -e .`, the entry point is `bookmark-backup`.

### Commands

| Command | Description |
|---------|-------------|
| `bookmark-backup import-chrome` | Import from Chromium JSON (Chrome/Edge profile `Bookmarks` file) |
| `bookmark-backup import-chrome --path PATH` | Same, with explicit file path (`-p` also works) |
| `bookmark-backup import-file --path PATH` | Import one `.html`/`.htm` export or JSON bookmarks file (`-p`) |
| `bookmark-backup stats` | Print total bookmark count and counts per browser in the database |
| `bookmark-backup serve` | Start the FastAPI web app (default `http://127.0.0.1:8000`) |
| `bookmark-backup serve --reload` | Dev mode: auto-reload on code changes |
| `bookmark-backup serve --host HOST --port PORT` | Custom bind address |

### Import behavior

- **`import-chrome`**: Default path is the local Chrome profile  
  `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Bookmarks`  
  (override with `--path` or `CHROME_BOOKMARKS_PATH` in `.env`).
- **`import-file`**: `.html`/`.htm` → HTML export parser; any other extension → Chromium JSON parser.
- Browser label (`chrome`, `edge`, `firefox`, `unknown`) is guessed from the file path.
- Both commands print: **scanned**, **inserted**, **skipped (duplicates)**.
- User/device metadata use defaults (`local@bookmark-backup`, `local-device`). The web import form can override these.

**Tip:** Close the browser before importing, or copy the `Bookmarks` file elsewhere and pass `--path`, so the file is not locked.

### Examples

```powershell
bookmark-backup import-chrome
bookmark-backup import-chrome --path "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Bookmarks"
bookmark-backup import-file --path "tests\fixtures\sample_edge_bookmarks.html"
bookmark-backup stats
bookmark-backup serve
bookmark-backup serve --reload --port 8000
```

### CLI vs web UI

| Capability | CLI | Web UI |
|------------|-----|--------|
| Import bookmarks | Yes (`import-chrome`, `import-file`) | Yes (upload + path list) |
| Same dedupe / DB logic | Yes (`ImportService`) | Yes |
| Multi-file / upload import | No (one path per command) | Yes |
| Content sniffing (HTML vs JSON) | Suffix only (`.html`) | Sniffs file content + suffix |
| View / edit tree | No | Yes |
| DB migrations | No (use `alembic` separately) | No |

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
