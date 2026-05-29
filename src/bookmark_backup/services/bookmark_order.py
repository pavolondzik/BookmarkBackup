"""Reorder bookmarks within a folder using sort_index."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from bookmark_backup.db.models import Bookmark


def _folder_filter(folder_id: int | None):
    if folder_id is None:
        return Bookmark.folder_id.is_(None)
    return Bookmark.folder_id == folder_id


def _siblings_in_folder(
    session: Session,
    folder_id: int | None,
    *,
    exclude_id: int | None = None,
) -> list[Bookmark]:
    stmt = select(Bookmark).where(_folder_filter(folder_id)).order_by(
        Bookmark.sort_index.asc(),
        Bookmark.id.asc(),
    )
    if exclude_id is not None:
        stmt = stmt.where(Bookmark.id != exclude_id)
    return list(session.scalars(stmt).all())


def reindex_folder(session: Session, folder_id: int | None) -> None:
    for index, bookmark in enumerate(_siblings_in_folder(session, folder_id)):
        bookmark.sort_index = index


def reorder_bookmark(
    session: Session,
    bookmark: Bookmark,
    *,
    old_folder_id: int | None,
    sort_index: int | None = None,
) -> None:
    """Place bookmark at sort_index in its current folder; None appends to end."""
    target_folder_id = bookmark.folder_id
    siblings = _siblings_in_folder(session, target_folder_id, exclude_id=bookmark.id)

    if sort_index is None:
        insert_at = len(siblings)
    else:
        insert_at = max(0, min(sort_index, len(siblings)))

    ordered = siblings[:insert_at] + [bookmark] + siblings[insert_at:]
    for index, item in enumerate(ordered):
        item.sort_index = index

    if old_folder_id != target_folder_id:
        reindex_folder(session, old_folder_id)


def next_sort_index(session: Session, folder_id: int | None) -> int:
    siblings = _siblings_in_folder(session, folder_id)
    if not siblings:
        return 0
    return max(bookmark.sort_index for bookmark in siblings) + 1
