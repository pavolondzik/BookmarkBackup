import pytest

from bookmark_backup.services.dedupe import normalize_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://WWW.Example.com/path/", "https://example.com/path"),
        ("https://example.com/path?b=2&a=1", "https://example.com/path?a=1&b=2"),
        ("https://example.com:443/x", "https://example.com/x"),
        ("http://example.com:80/x", "http://example.com/x"),
        ("https://example.com/page#section", "https://example.com/page"),
    ],
)
def test_normalize_url(raw: str, expected: str) -> None:
    assert normalize_url(raw) == expected


def test_normalize_url_preserves_non_http() -> None:
    url = "chrome://settings"
    assert normalize_url(url) == url
