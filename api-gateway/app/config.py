from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str = "change-me-to-a-random-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    user_profile_service_url: str = "http://user-profile:8000"
    footprint_service_url: str = "http://footprint-engine:8000"
    env_data_service_url: str = "http://env-data:8000"
    ai_narrative_service_url: str = "http://ai-narrative:8000"
    actions_service_url: str = "http://actions-engine:8000"
    community_service_url: str = "http://community:8000"

    redis_url: str = "redis://redis:6379/0"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
