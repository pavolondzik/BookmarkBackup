from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from bookmark_backup.db.models import Base, Bookmark, Browser, BrowserExport, Device, Folder, User
from bookmark_backup.importers.base import ImportPayload, ImportedBookmark
from bookmark_backup.services.bookmark_order import reorder_bookmark
from bookmark_backup.services.import_service import ImportService


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _bookmark(session, *, folder_id: int | None, sort_index: int, href: str) -> Bookmark:
    bookmark = Bookmark(
        href=href,
        href_normalized=href,
        title=href,
        folder_id=folder_id,
        sort_index=sort_index,
    )
    session.add(bookmark)
    session.flush()
    return bookmark


def test_import_assigns_sequential_sort_index_per_folder() -> None:
    payload = ImportPayload(
        browser_name="chrome",
        source_format="html",
        source_path="test.html",
        bookmarks=[
            ImportedBookmark(href="https://a.example", title="A", folder_path="Work"),
            ImportedBookmark(href="https://b.example", title="B", folder_path="Work"),
            ImportedBookmark(href="https://c.example", title="C", folder_path=""),
        ],
    )
    session = _session()
    ImportService(session).import_bookmarks(payload)

    bookmarks = session.scalars(select(Bookmark).order_by(Bookmark.id)).all()
    in_folder = [bookmark for bookmark in bookmarks if bookmark.folder_id is not None]
    root = [bookmark for bookmark in bookmarks if bookmark.folder_id is None]

    assert [bookmark.sort_index for bookmark in in_folder] == [0, 1]
    assert root[0].sort_index == 0


def test_reorder_moves_bookmark_to_insert_index() -> None:
    session = _session()
    user = User(email="u@example.com")
    session.add(user)
    session.flush()
    device = Device(user=user, name="d")
    session.add(device)
    session.flush()
    browser = Browser(device=device, browser_name="chrome", browser_version=None)
    session.add(browser)
    session.flush()
    export = BrowserExport(
        browser=browser,
        exported_at=datetime.now(tz=UTC),
        source_format="json",
        source_path=None,
    )
    session.add(export)
    session.flush()
    folder = Folder(browser_export=export, name="F")
    session.add(folder)
    session.flush()

    a = _bookmark(session, folder_id=folder.id, sort_index=0, href="https://a")
    b = _bookmark(session, folder_id=folder.id, sort_index=1, href="https://b")
    c = _bookmark(session, folder_id=folder.id, sort_index=2, href="https://c")

    reorder_bookmark(session, c, old_folder_id=folder.id, sort_index=0)
    session.commit()

    ordered = session.scalars(
        select(Bookmark)
        .where(Bookmark.folder_id == folder.id)
        .order_by(Bookmark.sort_index)
    ).all()
    assert [item.id for item in ordered] == [c.id, a.id, b.id]
    assert [item.sort_index for item in ordered] == [0, 1, 2]
