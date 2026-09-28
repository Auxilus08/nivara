from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Nivara API"
    app_env: str = "development"
    app_debug: bool = False
    database_url: str = Field(
        default="postgresql+asyncpg://nivara:nivara@localhost:5432/nivara",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins"),
    )
    map_api_key: str | None = None
    ai_api_key: str | None = None
    notification_provider: str | None = None
    notification_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
