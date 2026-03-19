from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FFF_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./fff.db"
    cors_allow_origins: str = "http://localhost:3000"


settings = Settings()

