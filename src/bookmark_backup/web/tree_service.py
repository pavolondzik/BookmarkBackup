from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from bookmark_backup.db.models import Bookmark, Browser, BrowserExport, Device, Folder, User
from bookmark_backup.web.schemas import DeviceOut, ExportOut, TreeNodeOut, UserOut


def list_users(session: Session) -> list[UserOut]:
    users = session.scalars(select(User).order_by(User.email.asc())).all()
    return [UserOut(id=user.id, email=user.email) for user in users]


def list_devices(session: Session, user_id: int) -> list[DeviceOut]:
    devices = session.scalars(
        select(Device).where(Device.user_id == user_id).order_by(Device.name.asc())
    ).all()
    return [DeviceOut(id=d.id, name=d.name, user_id=d.user_id) for d in devices]


def list_exports(session: Session, device_id: int | None = None) -> list[ExportOut]:
    stmt = (
        select(BrowserExport, Browser.browser_name, Device.id)
        .join(Browser, Browser.id == BrowserExport.browser_id)
        .join(Device, Device.id == Browser.device_id)
        .order_by(BrowserExport.exported_at.desc())
    )
    if device_id is not None:
        stmt = stmt.where(Device.id == device_id)

    rows = session.execute(stmt).all()
    return [
        ExportOut(
            id=export.id,
            browser_name=browser_name,
            device_id=device_id,
            exported_at=export.exported_at.isoformat(),
            source_format=export.source_format,
            source_path=export.source_path,
        )
        for export, browser_name, device_id in rows
    ]


def get_latest_export_id(session: Session) -> int | None:
    return session.scalar(
        select(BrowserExport.id).order_by(BrowserExport.exported_at.desc()).limit(1)
    )


def build_tree(session: Session, export_id: int) -> list[TreeNodeOut]:
    folders = session.scalars(
        select(Folder)
        .where(Folder.browser_export_id == export_id)
        .options(selectinload(Folder.bookmarks))
    ).all()

    folder_ids = {folder.id for folder in folders}
    if folder_ids:
        bookmarks = session.scalars(
            select(Bookmark).where(
                Bookmark.folder_id.in_(folder_ids) | Bookmark.folder_id.is_(None)
            )
        ).all()
    else:
        bookmarks = session.scalars(select(Bookmark).where(Bookmark.folder_id.is_(None))).all()

    bookmarks_by_folder: dict[int | None, list[Bookmark]] = {}
    for bookmark in bookmarks:
        bookmarks_by_folder.setdefault(bookmark.folder_id, []).append(bookmark)

    children_by_parent: dict[int | None, list[Folder]] = {}
    for folder in folders:
        children_by_parent.setdefault(folder.parent_id, []).append(folder)

    def folder_node(folder: Folder) -> TreeNodeOut:
        child_folders = sorted(
            children_by_parent.get(folder.id, []),
            key=lambda item: item.name.lower(),
        )
        child_bookmarks = sorted(
            bookmarks_by_folder.get(folder.id, []),
            key=lambda item: (item.sort_index, item.id),
        )
        children: list[TreeNodeOut] = [
            folder_node(child) for child in child_folders
        ] + [
            TreeNodeOut(
                id=bookmark.id,
                node_type="bookmark",
                name=bookmark.title or bookmark.href,
                href=bookmark.href,
                folder_id=bookmark.folder_id,
                sort_index=bookmark.sort_index,
            )
            for bookmark in child_bookmarks
        ]
        return TreeNodeOut(
            id=folder.id,
            node_type="folder",
            name=folder.name,
            parent_id=folder.parent_id,
            children=children,
        )

    root_folders = sorted(
        children_by_parent.get(None, []),
        key=lambda item: item.name.lower(),
    )
    root_bookmarks = sorted(
        bookmarks_by_folder.get(None, []),
        key=lambda item: (item.sort_index, item.id),
    )

    nodes = [folder_node(folder) for folder in root_folders]
    nodes.extend(
        TreeNodeOut(
            id=bookmark.id,
            node_type="bookmark",
            name=bookmark.title or bookmark.href,
            href=bookmark.href,
            folder_id=None,
            sort_index=bookmark.sort_index,
        )
        for bookmark in root_bookmarks
    )
    return nodes


def is_folder_descendant(session: Session, folder_id: int, potential_ancestor_id: int) -> bool:
    current_id: int | None = potential_ancestor_id
    while current_id is not None:
        if current_id == folder_id:
            return True
        current_id = session.scalar(
            select(Folder.parent_id).where(Folder.id == current_id)
        )
    return False
