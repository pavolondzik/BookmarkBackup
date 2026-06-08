from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Index, String, Text, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class SystemRole(StrEnum):
    ADMINISTRATOR = "Administrator"
    EDITOR = "Editor"
    VIEWER = "Viewer"

class SystemModule(StrEnum):
    BOOKMARKS = "Bookmarks"
    FOLDERS = "Folders"
    ADMINISTRATION = "Administration"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    devices: Mapped[list["Device"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    roles: Mapped[list["Role"]] = relationship(
        secondary="userroles",
        back_populates="users",
    )
    password: Mapped[str] = mapped_column(String(255), nullable=True)
    previous_password: Mapped[str] = mapped_column(String(255), nullable=True)

class UserRole(Base):
    __tablename__ = "userroles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    users: Mapped[list["User"]] = relationship(
        secondary="userroles",
        back_populates="roles",
    )
    permissions: Mapped[list["Permission"]] = relationship(
        secondary="rolepermissions",
        back_populates="roles",
    )

class Module(Base):
    __tablename__ = "modules"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e.g. "bookmarks"
    description: Mapped[str | None] = mapped_column(String(255))

    permissions: Mapped[list["Permission"]] = relationship(back_populates="module", cascade="all, delete-orphan")

class RolePermission(Base):
    __tablename__ = "rolepermissions"
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), primary_key=True)

class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), nullable=False)  
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "import", "delete"
    description: Mapped[str | None] = mapped_column(String(255))

    module: Mapped["Module"] = relationship(back_populates="permissions")
    roles: Mapped[list["Role"]] = relationship(
        secondary="rolepermissions",
        back_populates="permissions",
    )

    __table_args__ = (
        Index("ix_permissions_module_action", "module_id", "action", unique=True),
    )

class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="devices")
    browsers: Mapped[list["Browser"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
    )

class Browser(Base):
    __tablename__ = "browsers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    browser_name: Mapped[str] = mapped_column(String(50), nullable=False)   # chrome/firefox/edge
    browser_version: Mapped[str] = mapped_column(String(50), nullable=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False)
    device: Mapped["Device"] = relationship(back_populates="browsers")
    browser_exports: Mapped[list["BrowserExport"]] = relationship(
        back_populates="browser",
        cascade="all, delete-orphan",
    )

class BrowserExport(Base):
    __tablename__ = "browser_exports"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_format: Mapped[str] = mapped_column(String(20), nullable=False)  # html/json
    source_path: Mapped[str | None] = mapped_column(String(1024))
    checksum: Mapped[str | None] = mapped_column(String(128))
    browser_id: Mapped[int] = mapped_column(ForeignKey("browsers.id"), nullable=False)
    browser: Mapped["Browser"] = relationship(back_populates="browser_exports")
    folders: Mapped[list["Folder"]] = relationship(
        back_populates="browser_export",
        cascade="all, delete-orphan",
    )


class Folder(Base):
    __tablename__ = "folders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    browser_export_id: Mapped[int] = mapped_column(
        ForeignKey("browser_exports.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    browser_export: Mapped["BrowserExport"] = relationship(back_populates="folders")
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("folders.id"), nullable=True)
    parent: Mapped[Folder | None] = relationship(
        back_populates="children",
        remote_side="Folder.id",
    )
    children: Mapped[list["Folder"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        back_populates="folder",
        cascade="all, delete-orphan",
    )

class Bookmark(Base):
    __tablename__ = "bookmarks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    href: Mapped[str] = mapped_column(Text, nullable=False)
    href_normalized: Mapped[str] = mapped_column(String(2048), nullable=False)
    icon_uri: Mapped[str] = mapped_column(Text, nullable=False, default="")
    icon: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    date_added: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_modified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    folder_id: Mapped[int | None] = mapped_column(ForeignKey("folders.id"), nullable=True)
    sort_index: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    folder: Mapped[Folder | None] = relationship(back_populates="bookmarks")
    __table_args__ = (
        Index("ix_bookmarks_href_normalized", "href_normalized", unique=True),
    )
