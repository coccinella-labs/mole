from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API security
    API_KEY: str = "your-secret-api-key"  # Change in production

    # Celery settings (for future async processing)
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # Class-based Config was deprecated in Pydantic V2 and is removed in V3.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
