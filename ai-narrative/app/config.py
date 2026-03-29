"""EcoSignal AI Narrative — configuration and Regolo AI client factory."""

from functools import lru_cache

from openai import OpenAI
from pydantic_settings import BaseSettings

REGOLO_BASE_URL = "https://api.regolo.ai/v1"
REGOLO_MODEL = "qwen3.5-122b"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    regolo_api_key: str = ""
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


def get_llm_client() -> OpenAI:
    """Create an OpenAI-compatible client pointing to Regolo AI."""
    settings = get_settings()
    return OpenAI(api_key=settings.regolo_api_key, base_url=REGOLO_BASE_URL)
