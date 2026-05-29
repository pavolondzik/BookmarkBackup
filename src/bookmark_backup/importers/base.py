from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ImportedBookmark:
    href: str
    title: str
    folder_path: str
    date_added: datetime | None = None
    icon_uri: str = ""
    icon: str | None = None


@dataclass(frozen=True, slots=True)
class ImportPayload:
    browser_name: str
    source_format: str
    source_path: str | None
    bookmarks: list[ImportedBookmark]
