from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "EcoSignal Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ecosignal"
    UPLOAD_DIR: str = "/app/uploads"
    CLIMATIQ_API_KEY: str | None = None
    CLIMATIQ_BASE_URL: str = "https://api.climatiq.io"
    CLIMATIQ_TIMEOUT_SECONDS: float = 10.0
    CLIMATIQ_DATA_VERSION: str = "32"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
