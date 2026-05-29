"""Field length limits matching the database schema."""

FOLDER_NAME_MAX = 255
BOOKMARK_TITLE_MAX = 1024
HREF_NORMALIZED_MAX = 2048
SOURCE_PATH_MAX = 1024


def clip(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len]
