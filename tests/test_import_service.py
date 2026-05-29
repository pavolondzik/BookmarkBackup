from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from bookmark_backup.db.models import Base, Bookmark
from bookmark_backup.importers.base import ImportPayload, ImportedBookmark
from bookmark_backup.services.import_service import ImportService


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_import_skips_duplicate_urls_in_same_batch() -> None:
    payload = ImportPayload(
        browser_name="chrome",
        source_format="html",
        source_path="test.html",
        bookmarks=[
            ImportedBookmark(
                href="https://example.com",
                title="First",
                folder_path="Folder A",
            ),
            ImportedBookmark(
                href="https://example.com#section",
                title="Duplicate",
                folder_path="Folder B",
            ),
        ],
    )

    session = _session()
    result = ImportService(session).import_bookmarks(payload)

    assert result.scanned == 2
    assert result.inserted == 1
    assert result.skipped_duplicates == 1
    count = session.scalar(select(func.count()).select_from(Bookmark))
    assert count == 1


def test_import_skips_url_already_in_database() -> None:
    session = _session()
    service = ImportService(session)

    first = ImportPayload(
        browser_name="chrome",
        source_format="json",
        source_path="first.json",
        bookmarks=[
            ImportedBookmark(
                href="https://bitcoin.org/en",
                title="Bitcoin",
                folder_path="",
            ),
        ],
    )
    service.import_bookmarks(first)

    second = ImportPayload(
        browser_name="chrome",
        source_format="json",
        source_path="second.json",
        bookmarks=[
            ImportedBookmark(
                href="https://bitcoin.org/en#top",
                title="Bitcoin again",
                folder_path="",
            ),
        ],
    )
    result = service.import_bookmarks(second)

    assert result.inserted == 0
    assert result.skipped_duplicates == 1
    count = session.scalar(select(func.count()).select_from(Bookmark))
    assert count == 1
