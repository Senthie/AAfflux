"""Application configuration using pydantic-settings."""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Low-Code Platform Backend"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    api_v1_prefix: str = "/api/v1"

    # Security
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database - PostgreSQL
    database_url: str = Field(..., description="PostgreSQL connection URL")
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # MongoDB
    mongodb_url: str = Field(..., description="MongoDB connection URL")
    mongodb_database: str = "lowcode_platform"

    # Redis
    redis_url: str = Field(..., description="Redis connection URL")
    redis_db: int = 0
    redis_max_connections: int = 10

    # Celery
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None

    # Sentry
    sentry_dsn: Optional[str] = None
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # File Upload
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    gridfs_threshold: int = 16 * 1024 * 1024  # 16MB

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    @field_validator("celery_broker_url", mode="before")
    @classmethod
    def set_celery_broker(cls, v: Optional[str], info) -> str:
        """Set Celery broker URL from Redis URL if not provided."""
        if v is None:
            redis_url = info.data.get("redis_url")
            if redis_url:
                return redis_url
        return v or ""

    @field_validator("celery_result_backend", mode="before")
    @classmethod
    def set_celery_backend(cls, v: Optional[str], info) -> str:
        """Set Celery result backend from Redis URL if not provided."""
        if v is None:
            redis_url = info.data.get("redis_url")
            if redis_url:
                return redis_url
        return v or ""


# Global settings instance
settings = Settings()
