from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    devices: Mapped[list["Device"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
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
    title: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    date_added: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_modified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    folder_id: Mapped[int | None] = mapped_column(ForeignKey("folders.id"), nullable=True)
    folder: Mapped[Folder | None] = relationship(back_populates="bookmarks")
    __table_args__ = (
        Index("ix_bookmarks_href_normalized", "href_normalized", unique=True),
    )
