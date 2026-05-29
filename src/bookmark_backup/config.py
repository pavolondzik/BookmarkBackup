from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_chrome_bookmarks_path() -> Path:
    local_app = Path.home() / "AppData" / "Local"
    return (
        local_app
        / "Google"
        / "Chrome"
        / "User Data"
        / "Default"
        / "Bookmarks"
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    chrome_bookmarks_path: Path = default_chrome_bookmarks_path()


settings = Settings()
