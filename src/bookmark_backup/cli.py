from pathlib import Path

import typer
import uvicorn
from sqlalchemy import func, select

from bookmark_backup.config import settings
from bookmark_backup.db.models import Bookmark, Browser, BrowserExport, Folder
from bookmark_backup.db.session import SessionLocal
from bookmark_backup.importers.chrome import ChromeImporter
from bookmark_backup.importers.html_bookmarks import HtmlBookmarksImporter
from bookmark_backup.services.import_service import ImportService

app = typer.Typer(
    name="bookmark-backup",
    help="Import browser bookmarks into PostgreSQL with deduplication.",
)


@app.command("import-chrome")
def import_chrome(
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Path to Chrome Bookmarks file (default: local Chrome profile)",
    ),
) -> None:
    """Import bookmarks from Chromium JSON file into PostgreSQL."""
    bookmarks_path = path or settings.chrome_bookmarks_path
    typer.echo(f"Reading: {bookmarks_path}")

    payload = ChromeImporter(bookmarks_path, browser_name=_guess_browser_name(bookmarks_path)).load()
    typer.echo(f"Found {len(payload.bookmarks)} bookmark(s) in file")

    with SessionLocal() as session:
        result = ImportService(session).import_bookmarks(payload=payload)

    typer.echo(
        f"Done — scanned: {result.scanned}, "
        f"inserted: {result.inserted}, "
        f"skipped (duplicates): {result.skipped_duplicates}"
    )


@app.command("import-file")
def import_file(
    path: Path = typer.Option(..., "--path", "-p", help="Path to .html/.json bookmarks file"),
) -> None:
    """Import bookmarks from a file (Chrome/Edge JSON or HTML export)."""
    suffix = path.suffix.lower()
    if suffix in {".html", ".htm"}:
        payload = HtmlBookmarksImporter(path, browser_name=_guess_browser_name(path)).load()
    else:
        payload = ChromeImporter(path, browser_name=_guess_browser_name(path)).load()

    with SessionLocal() as session:
        result = ImportService(session).import_bookmarks(payload=payload)
    typer.echo(
        f"Done — scanned: {result.scanned}, "
        f"inserted: {result.inserted}, "
        f"skipped (duplicates): {result.skipped_duplicates}"
    )


@app.command("stats")
def stats() -> None:
    """Show bookmark counts in the database."""
    with SessionLocal() as session:
        total = session.scalar(select(func.count()).select_from(Bookmark)) or 0
        by_browser = session.execute(
            select(Browser.browser_name, func.count(Bookmark.id))
            .select_from(Bookmark)
            .join(Bookmark.folder, isouter=True)
            .join(BrowserExport, BrowserExport.id == Folder.browser_export_id, isouter=True)
            .join(Browser, Browser.id == BrowserExport.browser_id, isouter=True)
            .group_by(Browser.browser_name)
            .order_by(Browser.browser_name)
        ).all()

    typer.echo(f"Total bookmarks: {total}")
    for browser, count in by_browser:
        typer.echo(f"  {browser}: {count}")


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Auto-reload on code changes"),
) -> None:
    """Run the web UI (FastAPI)."""
    uvicorn.run(
        "bookmark_backup.web.app:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    app()


def _guess_browser_name(path: Path) -> str:
    lower = str(path).lower()
    if "edge" in lower:
        return "edge"
    if "firefox" in lower:
        return "firefox"
    if "chrome" in lower:
        return "chrome"
    return "unknown"
