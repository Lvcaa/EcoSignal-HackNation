"""Configuration for community service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "sqlite+aiosqlite:///./community.db"
    challenges_path: str = "challenges.json"
    host: str = "0.0.0.0"
    port: int = 8006

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
