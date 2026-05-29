import json
import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from bookmark_backup import __version__
from bookmark_backup.db.models import Bookmark
from bookmark_backup.db.session import get_db
from bookmark_backup.importers.base import ImportPayload
from bookmark_backup.importers.chrome import ChromeImporter
from bookmark_backup.importers.html_bookmarks import HtmlBookmarksImporter
from bookmark_backup.services.import_service import ImportService
from bookmark_backup.web.api import router as api_router

TEMPLATES_DIR = Path(__file__).parent / "templates"
FRONTEND_DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app = FastAPI(
    title="Bookmark Backup",
    description="Unified bookmark storage with deduplication",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/")
def root():
    index = FRONTEND_DIST / "index.html"
    if index.is_file():
        return FileResponse(index)
    return RedirectResponse(url="/legacy")


@app.get("/legacy", response_class=HTMLResponse)
def legacy_index(
    request: Request,
    q: str | None = Query(None, description="Search title or URL"),
    imported: str | None = Query(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    stmt = select(Bookmark).order_by(Bookmark.title.asc())
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(Bookmark.title.ilike(pattern), Bookmark.href.ilike(pattern))
        )

    bookmarks = db.scalars(stmt.limit(500)).all()
    total = db.scalar(select(func.count()).select_from(Bookmark)) or 0

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "bookmarks": bookmarks,
            "total": total,
            "shown": len(bookmarks),
            "query": q or "",
            "imported": imported,
        },
    )


@app.post("/import")
async def import_bookmarks(
    files: list[UploadFile] = File(default=[]),
    paths: str = Form(default=""),
    user_email: str = Form(default="local@bookmark-backup"),
    device_name: str = Form(default="local-device"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    try:
        payloads: list[ImportPayload] = []
        for file in files:
            raw = await file.read()
            if not raw:
                continue
            path = _persist_upload(file.filename or "bookmarks_upload", raw)
            payloads.append(_load_payload_from_path(path))

        for line in paths.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            path = Path(os.path.expandvars(line))
            payloads.append(_load_payload_from_path(path))

        if not payloads:
            raise HTTPException(
                status_code=400,
                detail="No import files or paths provided.",
            )

        service = ImportService(db)
        inserted_total = 0
        scanned_total = 0
        skipped_total = 0
        for payload in payloads:
            result = service.import_bookmarks(
                payload=payload,
                user_email=user_email,
                device_name=device_name,
            )
            inserted_total += result.inserted
            scanned_total += result.scanned
            skipped_total += result.skipped_duplicates
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    message = f"Imported {inserted_total}/{scanned_total}, skipped {skipped_total}"
    if (FRONTEND_DIST / "index.html").is_file():
        return RedirectResponse(url=f"/?imported={message}", status_code=303)
    return RedirectResponse(url=f"/legacy?imported={message}", status_code=303)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _persist_upload(filename: str, raw: bytes) -> Path:
    uploads_dir = Path(".uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_name = filename.replace("\\", "_").replace("/", "_")
    target = uploads_dir / f"{datetime.now(tz=UTC).strftime('%Y%m%d_%H%M%S')}_{safe_name}"
    target.write_bytes(raw)
    return target


def _load_payload_from_path(path: Path) -> ImportPayload:
    if not path.is_file():
        raise FileNotFoundError(f"Import file not found: {path}")

    text_start = path.read_text(encoding="utf-8", errors="ignore")[:2048]
    if "<!DOCTYPE NETSCAPE-Bookmark-file-1>" in text_start:
        return HtmlBookmarksImporter(path, browser_name=_guess_browser_name(path)).load()

    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(parsed, dict) and "roots" in parsed:
            return ChromeImporter(path, browser_name=_guess_browser_name(path)).load()
    except json.JSONDecodeError:
        pass

    if path.suffix.lower() in {".html", ".htm"}:
        return HtmlBookmarksImporter(path, browser_name=_guess_browser_name(path)).load()
    return ChromeImporter(path, browser_name=_guess_browser_name(path)).load()


def _guess_browser_name(path: Path) -> str:
    lower = str(path).lower()
    if "edge" in lower:
        return "edge"
    if "firefox" in lower:
        return "firefox"
    if "chrome" in lower:
        return "chrome"
    return "unknown"
