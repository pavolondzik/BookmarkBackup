# Bookmark Backup

Bookmark Backup is a small ETL pipeline with a FastAPI backend and web UI for importing, normalizing, and deduplicating browser bookmarks.


## Architecture

```text
JSON/HTML bookmark files
            ↓
         Importers
            ↓
      normalize_url()
            ↓
       PostgreSQL
            ↓
       Folder tree
            ↓
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
- Node.js 18+
- npm
- Docker Desktop (Windows/macOS) or Docker Engine (Linux)

## Quick start

For VS Code run/debug instructions, see [`README_VSCODE.md`](README_VSCODE.md)
Docker is optional for local containerized development; follow the steps below for a local Python/Node setup.

### App entry point

- **Web Application (FastAPI):** `src/bookmark_backup/web/app.py`
- **Command Line Interface (CLI):** `src/bookmark_backup/cli.py`

### 1. Virtual environment and install

```powershell
cd c:\BookmarkBackup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 2. Environment

Create a `.env` file in the repo root with the database URL:

```env
DATABASE_URL=postgresql+psycopg://appname:bookmark@localhost:5432/bookmark_backup
```

If you use `docker compose -f docker/docker-compose.yml up` for the full stack, the **api** service runs migrations automatically on startup. For local-only API development, run migrations yourself (step 4).

### 3. Start PostgreSQL

Database only:

```powershell
docker compose -f docker/docker-compose.yml -p bookmarkbackup up -d db
```

Or start the full containerized stack (database + API + React UI):

```powershell
docker compose -f docker/docker-compose.yml -p bookmarkbackup up -d --build
```

When using the full stack, skip steps 4 and the separate dev servers in step 6 — open http://127.0.0.1:5173 instead.

### 4. Run migrations

Required when running the API **outside** Docker (local venv or VS Code debug). Skip if the `api` container is already running — it runs `alembic upgrade head` on start.

```powershell
alembic upgrade head
```

### 5. Import bookmarks (CLI)

Close the browser first (or copy the `Bookmarks` file elsewhere and pass `--path`), then run one of the import commands below.

```powershell
bookmark-backup import-chrome
# or explicitly:
bookmark-backup import-chrome --path "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Bookmarks"

# import HTML export or any JSON bookmarks file:
bookmark-backup import-file --path "tests\fixtures\sample_edge_bookmarks.html"
```
See [README_CLI.md](README_CLI.md) for CLI usage and reference.

### 6. Web UI (React + TypeScript)

The UI is a Vite + React app in `frontend/`. When you run `bookmark-backup serve`, the API serves the compiled files from `frontend/dist/`. If that folder is missing, the server returns an error asking you to build first.

The left sidebar shows the **folder + bookmark tree** with drag-and-drop move, rename, and delete. Use the **Import bookmarks** panel in the details column to upload `.html`/JSON files or paste local paths (one per line).

#### Development (recommended)

**Docker:** `docker compose -f docker/docker-compose.yml -p bookmarkbackup up -d --build` runs API and Vite with hot reload.

**Local:** Run the API and frontend separately on the host. Changes hot-reload; no production build is required.

Terminal 1 — API:

```powershell
bookmark-backup serve
```

Terminal 2 — React UI (first time: run `npm install` in `frontend/`):

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 (Vite proxies `/api` to port 8000).

#### Production (single server)

Build once, then serve the UI from the API:

```powershell
cd frontend
npm install
npm run build
cd ..
bookmark-backup serve
```

Open http://127.0.0.1:8000

#### Build

Rebuild after you change files under `frontend/src/` and you are viewing the app at http://127.0.0.1:8000 (not the Vite dev server):

```powershell
cd frontend
npm run build
```

`npm run build` type-checks with TypeScript (`tsc -b`) and writes production assets to `frontend/dist/`.

Then:

1. **Restart** `bookmark-backup serve` if it is already running (the API does not pick up new `dist/` files on its own).
2. **Hard-refresh** the browser (e.g. Ctrl+F5) so cached JS/CSS are not reused.

### 7. Tests

```powershell
pytest
```

## License

MIT
