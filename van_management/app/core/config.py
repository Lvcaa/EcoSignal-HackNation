from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "EcoSignal Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ecosignal"
    UPLOAD_DIR: str = "/app/uploads"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
