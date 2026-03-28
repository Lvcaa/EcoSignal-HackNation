"""EcoSignal env-data module — configuration schema.

Uses pydantic-settings to load values from environment variables.
No implementation logic — schema definition only.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Environment-driven configuration for the env-data service."""

    model_config = {"env_prefix": "ENV_DATA_"}

    openaq_api_key: str
    redis_url: str = "redis://redis:6379/0"
    cache_ttl_seconds: int = 3600
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"
    openaq_base_url: str = "https://api.openaq.org/v3"
    log_level: str = "INFO"
    request_timeout_seconds: int = 10
    fallback_on_timeout: bool = True
