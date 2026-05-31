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