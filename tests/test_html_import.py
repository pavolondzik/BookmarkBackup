from pathlib import Path

from bookmark_backup.importers.html_bookmarks import HtmlBookmarksImporter


def test_html_importer_reads_nested_folders() -> None:
    fixture = Path("tests/fixtures/sample_edge_bookmarks.html")

    payload = HtmlBookmarksImporter(fixture, browser_name="edge").load()

    assert payload.browser_name == "edge"
    assert payload.source_format == "html"
    assert len(payload.bookmarks) == 2
    assert payload.bookmarks[0].folder_path == "Parent Folder/Nested Folder"
    assert payload.bookmarks[0].href == "https://example.com"
