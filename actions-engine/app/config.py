"""Configuration for actions-engine service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "sqlite+aiosqlite:///./actions.db"
    catalogue_path: str = "catalogue.json"
    host: str = "0.0.0.0"
    port: int = 8005

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
