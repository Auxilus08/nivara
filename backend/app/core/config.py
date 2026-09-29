from functools import lru_cache
import json
from typing import Annotated

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Nivara API"
    app_env: str = "development"
    app_debug: bool = False
    database_url: str = Field(
        default="postgresql+asyncpg://nivara:nivara@localhost:5432/nivara",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default=["http://localhost:3000"],
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins"),
    )
    map_api_key: str | None = None
    routing_provider: str = Field(default="openrouteservice")
    routing_api_key: str | None = Field(default=None)
    route_corridor_radius_meters: float = Field(default=100.0, ge=25.0, le=1000.0)
    deviation_corridor_threshold_meters: float = Field(default=500.0, ge=25.0, le=5000.0)
    ai_api_key: str | None = None
    notification_provider: str | None = None
    notification_api_key: str | None = None
    demo_mode: bool = Field(default=False, validation_alias=AliasChoices("NIVARA_DEMO_MODE", "DEMO_MODE", "demo_mode"))

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        """Accept JSON from .env files and comma-separated shell values.

        Sourcing a JSON-style env value in Bash removes its inner quotes, so
        `['http://localhost:3000']` must remain usable as well as valid JSON.
        """
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if not isinstance(value, str):
            return ["http://localhost:3000"]
        raw = value.strip()
        try:
            decoded = json.loads(raw)
            if isinstance(decoded, list):
                return [str(item).strip() for item in decoded if str(item).strip()]
        except json.JSONDecodeError:
            pass
        raw = raw.strip("[]")
        return [item.strip().strip("\"'") for item in raw.split(",") if item.strip().strip("\"'")]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
