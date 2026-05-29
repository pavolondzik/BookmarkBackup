from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path

from bookmark_backup.importers.base import ImportPayload, ImportedBookmark


class HtmlBookmarksImporter:
    """Read Netscape bookmark export HTML from Chrome/Edge/Firefox."""

    def __init__(self, path: Path, browser_name: str = "unknown") -> None:
        self.path = path
        self.browser_name = browser_name

    def load(self) -> ImportPayload:
        if not self.path.is_file():
            raise FileNotFoundError(f"Bookmarks HTML file not found: {self.path}")

        parser = _BookmarksHtmlParser()
        parser.feed(self.path.read_text(encoding="utf-8"))
        return ImportPayload(
            browser_name=self.browser_name,
            source_format="html",
            source_path=str(self.path),
            bookmarks=parser.bookmarks,
        )


class _BookmarksHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.folder_stack: list[str] = []
        self.pending_folder_name = False
        self.pending_link: dict[str, str] | None = None
        self.bookmarks: list[ImportedBookmark] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "h3":
            self.pending_folder_name = True
            return
        if tag.lower() == "a":
            self.pending_link = attrs_map

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "dl" and self.folder_stack:
            self.folder_stack.pop()

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return

        if self.pending_folder_name:
            self.folder_stack.append(text)
            self.pending_folder_name = False
            return

        if self.pending_link is None:
            return

        href = self.pending_link.get("href", "").strip()
        if not href:
            self.pending_link = None
            return

        folder_path = "/".join(self.folder_stack)
        add_date = self._parse_unix_ts(self.pending_link.get("add_date", ""))
        icon = self.pending_link.get("icon") or None
        icon_uri = self.pending_link.get("icon_uri", "")
        self.bookmarks.append(
            ImportedBookmark(
                href=href,
                title=text,
                folder_path=folder_path,
                date_added=add_date,
                icon_uri=icon_uri,
                icon=icon,
            )
        )
        self.pending_link = None

    @staticmethod
    def _parse_unix_ts(value: str) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromtimestamp(int(value), tz=UTC)
        except ValueError:
            return None
