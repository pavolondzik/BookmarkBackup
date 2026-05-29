from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from bookmark_backup.db.models import Bookmark, Folder
from bookmark_backup.db.session import get_db
from bookmark_backup.services.bookmark_order import reindex_folder, reorder_bookmark
from bookmark_backup.web.schemas import (
    BookmarkOut,
    BookmarkUpdate,
    DeviceOut,
    ExportOut,
    FolderUpdate,
    TreeNodeOut,
    UserOut,
)
from bookmark_backup.web.tree_service import (
    build_tree,
    get_latest_export_id,
    is_folder_descendant,
    list_devices,
    list_exports,
    list_users,
)

router = APIRouter(prefix="/api")


@router.get("/users", response_model=list[UserOut])
def api_list_users(db: Session = Depends(get_db)) -> list[UserOut]:
    return list_users(db)


@router.get("/devices", response_model=list[DeviceOut])
def api_list_devices(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
) -> list[DeviceOut]:
    return list_devices(db, user_id=user_id)


@router.get("/exports", response_model=list[ExportOut])
def api_list_exports(
    device_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> list[ExportOut]:
    return list_exports(db, device_id=device_id)


@router.get("/tree", response_model=list[TreeNodeOut])
def api_get_tree(
    export_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> list[TreeNodeOut]:
    resolved_export_id = export_id or get_latest_export_id(db)
    if resolved_export_id is None:
        return []
    return build_tree(db, resolved_export_id)


@router.patch("/folders/{folder_id}", response_model=TreeNodeOut)
def api_update_folder(
    folder_id: int,
    body: FolderUpdate,
    db: Session = Depends(get_db),
) -> TreeNodeOut:
    folder = db.get(Folder, folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")

    if body.name is not None:
        folder.name = body.name.strip() or folder.name

    if "parent_id" in body.model_fields_set:
        parent_id = body.parent_id
        if parent_id == folder_id:
            raise HTTPException(status_code=400, detail="Folder cannot be its own parent")
        if parent_id is None:
            folder.parent_id = None
        else:
            parent = db.get(Folder, parent_id)
            if parent is None:
                raise HTTPException(status_code=404, detail="Parent folder not found")
            if parent.browser_export_id != folder.browser_export_id:
                raise HTTPException(status_code=400, detail="Parent must belong to same export")
            if is_folder_descendant(db, folder_id, parent_id):
                raise HTTPException(status_code=400, detail="Cannot move folder into its descendant")
            folder.parent_id = parent_id

    db.commit()
    db.refresh(folder)
    return TreeNodeOut(
        id=folder.id,
        node_type="folder",
        name=folder.name,
        parent_id=folder.parent_id,
        children=[],
    )


@router.delete("/folders/{folder_id}", status_code=204)
def api_delete_folder(folder_id: int, db: Session = Depends(get_db)) -> None:
    folder = db.get(Folder, folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    db.delete(folder)
    db.commit()


@router.get("/bookmarks/{bookmark_id}", response_model=BookmarkOut)
def api_get_bookmark(bookmark_id: int, db: Session = Depends(get_db)) -> BookmarkOut:
    bookmark = db.get(Bookmark, bookmark_id)
    if bookmark is None:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return BookmarkOut(
        id=bookmark.id,
        title=bookmark.title,
        href=bookmark.href,
        icon_uri=bookmark.icon_uri,
        icon=bookmark.icon,
        folder_id=bookmark.folder_id,
    )


@router.patch("/bookmarks/{bookmark_id}")
def api_update_bookmark(
    bookmark_id: int,
    body: BookmarkUpdate,
    db: Session = Depends(get_db),
) -> dict[str, str | int | None]:
    bookmark = db.get(Bookmark, bookmark_id)
    if bookmark is None:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    if body.title is not None:
        bookmark.title = body.title.strip()

    old_folder_id = bookmark.folder_id

    if "folder_id" in body.model_fields_set:
        folder_id = body.folder_id
        if folder_id is None:
            bookmark.folder_id = None
        else:
            folder = db.get(Folder, folder_id)
            if folder is None:
                raise HTTPException(status_code=404, detail="Folder not found")
            bookmark.folder_id = folder_id

    if "folder_id" in body.model_fields_set or "sort_index" in body.model_fields_set:
        sort_index = body.sort_index if "sort_index" in body.model_fields_set else None
        reorder_bookmark(
            db,
            bookmark,
            old_folder_id=old_folder_id,
            sort_index=sort_index,
        )

    db.commit()
    return {
        "id": bookmark.id,
        "title": bookmark.title,
        "folder_id": bookmark.folder_id,
        "sort_index": bookmark.sort_index,
    }


@router.delete("/bookmarks/{bookmark_id}", status_code=204)
def api_delete_bookmark(bookmark_id: int, db: Session = Depends(get_db)) -> None:
    bookmark = db.get(Bookmark, bookmark_id)
    if bookmark is None:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    folder_id = bookmark.folder_id
    db.delete(bookmark)
    db.flush()
    reindex_folder(db, folder_id)
    db.commit()
