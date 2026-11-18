from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "QueryGenius API"
    app_env: str = "development"
    database_url: str = "sqlite:///./querygenius-dev.db"
    redis_url: str = "redis://redis:6379/0"
    cors_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"
    auth_secret: str = "change-me-in-local-development"
    access_token_minutes: int = 30
    refresh_token_days: int = 30
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    ai_provider: str = "gemini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
