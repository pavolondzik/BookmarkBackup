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

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — runs the **containerized** database, API, and React dev server (see [Docker](#docker-containerized-stack))
- **For local (non-Docker) development and CLI:** Python 3.11+, Node.js 18+ and npm

## Docker (containerized stack)

PostgreSQL, FastAPI, and the React UI run as Docker Compose services under the project name **`bookmarkbackup`**. Container names look like `bookmarkbackup-db-1`, `bookmarkbackup-api-1`, and `bookmarkbackup-web-1`.

| Service | Container | Host URL |
|---------|-----------|----------|
| `db` | Postgres 16 | `localhost:5430` (maps to 5432 in the container) |
| `api` | FastAPI + Alembic on startup | http://127.0.0.1:8000 |
| `web` | Vite dev server (hot reload) | http://127.0.0.1:5173 |

The API container sets `DATABASE_URL` to reach Postgres on the internal hostname `db`. The web container proxies `/api` and `/health` to `http://api:8000`. Source mounts enable hot reload for `src/` and `frontend/` without rebuilding images on every edit.

**Start the full stack:**

```powershell
docker compose up -d --build
```

**Useful commands:**

```powershell
docker compose ps
docker compose logs -f api web
docker compose up -d --build api web   # API + UI only (if db is already running)
docker compose down
```

Open http://127.0.0.1:5173 for the UI. Check the API at http://127.0.0.1:8000/health.

**CLI and imports on the host:** `bookmark-backup` still runs on your machine (not in a container). Point `.env` at the published DB port:

```env
DATABASE_URL=postgresql+psycopg://pavol:bookmark@localhost:5430/bookmark_backup
```

Docker files: [`docker-compose.yml`](docker-compose.yml), root [`Dockerfile`](Dockerfile), [`frontend/Dockerfile`](frontend/Dockerfile).

## Quick start

Choose **Docker** (above) for the easiest full stack, or follow the steps below for a local Python/Node setup.

### 1. Virtual environment and install

```powershell
cd c:\projekty\BookmarkBackup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 2. Environment

Create a `.env` file in the repo root with the database URL. Use port **5430** when Postgres runs via Docker Compose (see [Docker](#docker-containerized-stack)):

```env
DATABASE_URL=postgresql+psycopg://pavol:bookmark@localhost:5430/bookmark_backup
```

If you use `docker compose up` for the full stack, the **api** service runs migrations automatically on startup. For local-only API development, run migrations yourself (step 4).

### 3. Start PostgreSQL

Database only:

```powershell
docker compose up -d db
```

Or start the full containerized stack (database + API + React UI):

```powershell
docker compose up -d --build
```

When using the full stack, skip steps 4 and the separate dev servers in step 6 — open http://127.0.0.1:5173 instead.

### 4. Run migrations

Required when running the API **outside** Docker (local venv or VS Code debug). Skip if the `api` container is already running — it runs `alembic upgrade head` on start.

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

The UI is a Vite + React app in `frontend/`. When you run `bookmark-backup serve`, the API serves the compiled files from `frontend/dist/`. If that folder is missing, the server returns an error asking you to build first.

The left sidebar shows the **folder + bookmark tree** with drag-and-drop move, rename, and delete. Use the **Import bookmarks** panel in the details column to upload `.html`/JSON files or paste local paths (one per line), for example:

- `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Bookmarks`
- `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Bookmarks`

#### Development (recommended)

**Docker:** `docker compose up -d --build` runs API and Vite with hot reload (see [Docker](#docker-containerized-stack)).

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

**VS Code / Cursor:** open the repo root, install the [recommended extensions](.vscode/extensions.json) if prompted, then use **Run and Debug** → **Full stack (API + React)** (see [.vscode/launch.json](.vscode/launch.json)). The API configuration loads `.env` and runs uvicorn with `--reload`.

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

Other frontend scripts:

| Command | Description |
|---------|-------------|
| `npm run dev` | Dev server at http://127.0.0.1:5173 (proxies `/api` to port 8000) |
| `npm run preview` | Serve the production build locally for a quick check |
| `npm run format` | Format `src/**/*.{ts,tsx,css}` with Prettier |
| `npm run format:check` | Verify formatting (useful in CI) |

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
docker-compose.yml     # bookmarkbackup project: db, api, web
Dockerfile             # FastAPI image
frontend/Dockerfile    # Vite dev image
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
