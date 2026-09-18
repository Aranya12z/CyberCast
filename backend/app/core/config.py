"""
app/core/config.py — Environment / settings loader.

Reads from a .env file (never committed) and the process environment.
Matches the keys in the root .env.example exactly.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All backend configuration.  Values come from environment variables or a
    local .env file (loaded automatically by pydantic-settings).

    Key names match .env.example exactly — do not add keys here that are not
    in .env.example without also updating that file per AGENTS.md §Shared
    Repository Infrastructure.
    """

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/cybercast_db"
    JWT_SECRET: str = "changeme-replace-in-production"
    MODEL_PATH: str = "./ml/models/latest.pkl"
    ENV: str = "development"

    # JWT settings (not in .env.example — internal defaults, safe to hardcode)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    Use as a FastAPI dependency: settings: Settings = Depends(get_settings)
    """
    return Settings()
