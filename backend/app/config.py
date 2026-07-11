from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://opportunity:password@localhost:5432/opportunity_radar"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_env: str = "development"
    cors_origins: str = "http://localhost:3000"

    scraper_user_agent: str = "OpportunityRadar/1.0"
    scraper_default_delay_ms: int = 1000
    scraper_default_timeout_seconds: int = 20
    scraper_default_max_retries: int = 3

    admin_password: str = "change-me"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
