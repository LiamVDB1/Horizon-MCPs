from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    HELIUS_API_KEY: str

    # Jupiter settings
    # Tier can be "lite" or "api". Defaults to lite if not provided.
    JUPITER_TIER: str = "lite"
    # Optional API key for paid tier; when provided and tier=="api", we send it via x-api-key header
    JUPITER_API_KEY: str | None = None


settings = Settings()  # reads from environment and .env


