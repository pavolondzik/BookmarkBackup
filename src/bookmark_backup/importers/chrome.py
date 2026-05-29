import json
from datetime import UTC, datetime
from pathlib import Path

from bookmark_backup.importers.base import ImportPayload, ImportedBookmark


class ChromeImporter:
    """Read bookmarks from Chromium JSON Bookmarks file."""

    def __init__(self, path: Path, browser_name: str = "chrome") -> None:
        self.path = path
        self.browser_name = browser_name

    def load(self) -> ImportPayload:
        if not self.path.is_file():
            raise FileNotFoundError(f"Chrome bookmarks file not found: {self.path}")

        raw = json.loads(self.path.read_text(encoding="utf-8"))
        roots = raw.get("roots", {})
        results: list[ImportedBookmark] = []

        for root_name, node in roots.items():
            if root_name == "synced":  # often empty; skip duplicate tree
                continue
            self._walk(node, folder_path="", results=results)

        return ImportPayload(
            browser_name=self.browser_name,
            source_format="json",
            source_path=str(self.path),
            bookmarks=results,
        )

    def _walk(
        self,
        node: dict,
        folder_path: str,
        results: list[ImportedBookmark],
    ) -> None:
        node_type = node.get("type")
        name = node.get("name") or ""

        if node_type == "folder":
            child_path = f"{folder_path}/{name}" if folder_path else name
            for child in node.get("children") or []:
                self._walk(child, child_path, results)
            return

        if node_type != "url":
            return

        href = (node.get("url") or "").strip()
        if not href:
            return

        date_added = None
        if chrome_date := node.get("date_added"):
            date_added = _chrome_timestamp_to_datetime(chrome_date)

        results.append(
            ImportedBookmark(
                href=href,
                title=name,
                folder_path=folder_path,
                date_added=date_added,
                icon_uri=(node.get("icon_uri") or ""),
            )
        )


def _chrome_timestamp_to_datetime(value: str | int) -> datetime:
    """Chrome stores microseconds since 1601-01-01 UTC (Windows epoch)."""
    micros = int(value)
    seconds = (micros - 11_644_473_600_000_000) / 1_000_000
    return datetime.fromtimestamp(seconds, tz=UTC)
