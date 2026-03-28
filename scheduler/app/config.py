"""EcoSignal Scheduler — configuration schema."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Environment-driven configuration for the scheduler service."""

    model_config = {"env_prefix": ""}

    env_data_service_url: str = "http://env-data:8003"
    ai_narrative_service_url: str = "http://ai-narrative:8004"
    user_profile_service_url: str = "http://user-profile:8001"
    redis_url: str = "redis://redis:6379/0"
    log_level: str = "INFO"
    job_timezone: str = "Europe/Rome"
    prefetch_zip_limit: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
