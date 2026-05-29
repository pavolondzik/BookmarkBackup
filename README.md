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

### 6. Web UI

```powershell
bookmark-backup serve
```

Open http://127.0.0.1:8000

Use the **Import bookmarks** panel to:
- upload `.html`/JSON files directly, or
- paste one path per line, for example:
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
  importers/chrome.py    # Extract
  services/dedupe.py     # Transform
  services/import_service.py
  db/models.py           # Load
  web/app.py             # Browse
  cli.py
tests/
alembic/
```

## License

MIT
