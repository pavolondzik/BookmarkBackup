from typing import Literal

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None


class DeviceOut(BaseModel):
    id: int
    name: str
    user_id: int


class TreeNodeOut(BaseModel):
    id: int
    node_type: Literal["folder", "bookmark"]
    name: str
    href: str | None = None
    parent_id: int | None = None
    folder_id: int | None = None
    sort_index: int | None = None
    children: list["TreeNodeOut"] = Field(default_factory=list)


class ExportOut(BaseModel):
    id: int
    browser_name: str
    device_id: int
    exported_at: str
    source_format: str
    source_path: str | None


class FolderUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None


class BookmarkOut(BaseModel):
    id: int
    title: str
    href: str
    icon_uri: str
    icon: str | None = None
    folder_id: int | None = None


class BookmarkUpdate(BaseModel):
    title: str | None = None
    folder_id: int | None = None
    sort_index: int | None = None


class ImportResultOut(BaseModel):
    scanned: int
    inserted: int
    skipped_duplicates: int
