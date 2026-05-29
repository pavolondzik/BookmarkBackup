from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bookmark_backup.db.models import Bookmark, Browser, BrowserExport, Device, Folder, User
from bookmark_backup.importers.base import ImportPayload
from bookmark_backup.services.dedupe import normalize_url
from bookmark_backup.services.text_limits import (
    FOLDER_NAME_MAX,
    HREF_NORMALIZED_MAX,
    SOURCE_PATH_MAX,
    clip,
)


@dataclass(frozen=True, slots=True)
class ImportResult:
    scanned: int
    inserted: int
    skipped_duplicates: int


class ImportService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def import_bookmarks(
        self,
        payload: ImportPayload,
        user_email: str = "local@bookmark-backup",
        device_name: str = "local-device",
    ) -> ImportResult:
        browser = self._get_or_create_browser(
            user_email=user_email,
            device_name=device_name,
            browser_name=payload.browser_name,
        )
        source_path = payload.source_path
        if source_path:
            source_path = clip(source_path, SOURCE_PATH_MAX)

        browser_export = BrowserExport(
            browser=browser,
            exported_at=datetime.now(tz=UTC),
            source_format=payload.source_format,
            source_path=source_path,
            checksum=None,
        )
        self.session.add(browser_export)
        self.session.flush()

        folder_cache: dict[str, Folder] = {}
        sort_counters: dict[int | None, int] = defaultdict(int)
        inserted = 0
        skipped = 0
        seen_in_batch: set[str] = set()

        for item in payload.bookmarks:
            normalized = clip(normalize_url(item.href), HREF_NORMALIZED_MAX)
            if normalized in seen_in_batch:
                skipped += 1
                continue
            exists = self.session.scalar(
                select(Bookmark.id).where(Bookmark.href_normalized == normalized)
            )
            if exists:
                skipped += 1
                continue

            folder = self._get_or_create_folder(
                browser_export=browser_export,
                folder_path=item.folder_path,
                folder_cache=folder_cache,
            )
            folder_key: int | None = folder.id if folder is not None else None
            sort_index = sort_counters[folder_key]
            sort_counters[folder_key] += 1
            self.session.add(
                Bookmark(
                    href=item.href,
                    href_normalized=normalized,
                    title=item.title or item.href,
                    icon_uri=item.icon_uri,
                    icon=item.icon,
                    date_added=item.date_added,
                    folder=folder,
                    sort_index=sort_index,
                )
            )
            seen_in_batch.add(normalized)
            inserted += 1

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise ValueError(
                "Import failed: duplicate bookmark URL already exists in database."
            ) from None

        return ImportResult(
            scanned=len(payload.bookmarks),
            inserted=inserted,
            skipped_duplicates=skipped,
        )

    def _get_or_create_browser(
        self,
        user_email: str,
        device_name: str,
        browser_name: str,
    ) -> Browser:
        user = self.session.scalar(select(User).where(User.email == user_email))
        if user is None:
            user = User(email=user_email)
            self.session.add(user)
            self.session.flush()

        device = self.session.scalar(
            select(Device).where(Device.user_id == user.id, Device.name == device_name)
        )
        if device is None:
            device = Device(user=user, name=device_name)
            self.session.add(device)
            self.session.flush()

        browser = self.session.scalar(
            select(Browser).where(
                Browser.device_id == device.id, Browser.browser_name == browser_name
            )
        )
        if browser is None:
            browser = Browser(
                device=device,
                browser_name=browser_name,
                browser_version=None,
            )
            self.session.add(browser)
            self.session.flush()
        return browser

    def _get_or_create_folder(
        self,
        browser_export: BrowserExport,
        folder_path: str,
        folder_cache: dict[str, Folder],
    ) -> Folder | None:
        path = folder_path.strip().strip("/")
        if not path:
            return None

        segments = [seg.strip() for seg in path.split("/") if seg.strip()]
        parent: Folder | None = None
        running_path = ""
        for segment in segments:
            running_path = f"{running_path}/{segment}" if running_path else segment
            cached = folder_cache.get(running_path)
            if cached is not None:
                parent = cached
                continue

            folder = Folder(
                browser_export=browser_export,
                name=clip(segment, FOLDER_NAME_MAX),
                parent=parent,
            )
            self.session.add(folder)
            self.session.flush()
            folder_cache[running_path] = folder
            parent = folder

        return parent
