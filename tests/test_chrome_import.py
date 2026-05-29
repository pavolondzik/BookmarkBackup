import json
from pathlib import Path

from bookmark_backup.importers.chrome import ChromeImporter


def test_chrome_importer_reads_nested_folders(tmp_path: Path) -> None:
    data = {
        "roots": {
            "bookmark_bar": {
                "type": "folder",
                "name": "Bookmarks bar",
                "children": [
                    {
                        "type": "folder",
                        "name": "Work",
                        "children": [
                            {
                                "type": "url",
                                "name": "Example",
                                "url": "https://example.com",
                                "date_added": "13311638400000000",
                            }
                        ],
                    },
                    {
                        "type": "url",
                        "name": "GitHub",
                        "url": "https://github.com",
                    },
                ],
            }
        }
    }
    path = tmp_path / "Bookmarks"
    path.write_text(json.dumps(data), encoding="utf-8")

    payload = ChromeImporter(path, browser_name="chrome").load()
    items = payload.bookmarks

    assert len(items) == 2
    urls = {i.href for i in items}
    assert "https://example.com" in urls
    assert "https://github.com" in urls

    example = next(i for i in items if i.href == "https://example.com")
    assert example.folder_path == "Bookmarks bar/Work"
    assert payload.browser_name == "chrome"
    assert payload.source_format == "json"
    assert example.date_added is not None
