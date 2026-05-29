import json
import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from bookmark_backup.importers.base import ImportPayload
from bookmark_backup.importers.chrome import ChromeImporter
from bookmark_backup.importers.html_bookmarks import HtmlBookmarksImporter
from bookmark_backup.services.import_service import ImportService
from bookmark_backup.web.schemas import ImportResultOut


def persist_upload(filename: str, raw: bytes) -> Path:
    uploads_dir = Path(".uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_name = filename.replace("\\", "_").replace("/", "_")
    target = uploads_dir / f"{datetime.now(tz=UTC).strftime('%Y%m%d_%H%M%S')}_{safe_name}"
    target.write_bytes(raw)
    return target


def load_payload_from_path(path: Path) -> ImportPayload:
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


async def run_import(
    *,
    db: Session,
    files: list[UploadFile],
    paths: str,
    user_email: str,
    device_name: str,
) -> ImportResultOut:
    try:
        payloads: list[ImportPayload] = []
        for file in files:
            raw = await file.read()
            if not raw:
                continue
            path = persist_upload(file.filename or "bookmarks_upload", raw)
            payloads.append(load_payload_from_path(path))

        for line in paths.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            path = Path(os.path.expandvars(line))
            payloads.append(load_payload_from_path(path))

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

        return ImportResultOut(
            scanned=scanned_total,
            inserted=inserted_total,
            skipped_duplicates=skipped_total,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
