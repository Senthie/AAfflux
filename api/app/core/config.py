"""Application configuration using pydantic-settings."""

from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class InvitationSecurityConfig(BaseSettings):
    """邀请安全配置"""

    # 频率限制配置
    rate_limit_hour: int = 5  # 每小时最多5个邀请
    rate_limit_day: int = 20  # 每天最多20个邀请
    rate_limit_month: int = 100  # 每月最多100个邀请

    # 令牌安全配置
    token_length: int = 48  # 令牌长度(字节)
    token_expire_days: int = 7  # 令牌有效期(天)
    max_token_attempts: int = 3  # 令牌最大尝试次数

    # 重复邀请配置
    duplicate_check_enabled: bool = True
    duplicate_grace_period_hours: int = 1  # 重复检查宽限期

    # 审计配置
    audit_enabled: bool = True
    audit_ip_required: bool = True


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
        env_prefix='',  # No prefix for environment variables
    )

    # Application
    app_name: str = 'Low-Code Platform Backend'
    debug: bool = False
    host: str = '0.0.0.0'
    port: int = 8000
    api_v1_prefix: str = '/api/v1'

    # Security
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    secret_key: Optional[str] = Field(
        default=None, min_length=32, description='Secret key for HMAC signing'
    )

    # Invitation Security
    invitation_security: InvitationSecurityConfig = Field(default_factory=InvitationSecurityConfig)

    # Database - PostgreSQL
    database_url: str = Field(..., description='PostgreSQL connection URL')
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # MongoDB
    mongodb_url: str = Field(..., description='MongoDB connection URL')
    mongodb_database: str = 'lowcode_platform'

    # Redis
    redis_url: str = Field(..., description='Redis connection URL')
    redis_db: int = 0
    redis_max_connections: int = 10

    # Celery
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None

    # Sentry
    sentry_dsn: Optional[str] = None
    sentry_environment: str = 'development'
    sentry_traces_sample_rate: float = 0.1

    # Logging
    log_level: str = 'INFO'
    log_format: str = 'json'

    # File Upload
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    gridfs_threshold: int = 16 * 1024 * 1024  # 16MB

    # CORS
    cors_origins: list[str] = ['http://localhost:3000']
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ['*']
    cors_allow_headers: list[str] = ['*']

    # SMTP邮件配置
    smtp_server: str = 'smtp.exmail.qq.com'  # 企业微信邮箱
    smtp_port: int = 465  # SSL端口
    smtp_username: str = ''
    smtp_password: str = ''
    from_email: str = 'noreply@yourcompany.com'
    frontend_url: str = 'https://yourapp.com'

    @field_validator('celery_broker_url', mode='before')
    @classmethod
    def set_celery_broker(cls, v: Optional[str], info) -> str:
        """Set Celery broker URL from Redis URL if not provided."""
        if v is None:
            redis_url = info.data.get('redis_url')
            if redis_url:
                return redis_url
        return v or ''

    @field_validator('celery_result_backend', mode='before')
    @classmethod
    def set_celery_backend(cls, v: Optional[str], info) -> str:
        """Set Celery result backend from Redis URL if not provided."""
        if v is None:
            redis_url = info.data.get('redis_url')
            if redis_url:
                return redis_url
        return v or ''

    @field_validator('secret_key', mode='before')
    @classmethod
    def set_secret_key(cls, v: Optional[str], info) -> str:
        """Set secret key from JWT secret if not provided."""
        if v is None:
            jwt_secret = info.data.get('jwt_secret_key')
            if jwt_secret:
                return jwt_secret
        return v or 'default-secret-key-for-development-only-change-in-production'


# Global settings instance
try:
    settings = Settings()
except Exception as e:
    # Fallback for development/testing when .env might not be available
    import os

    if os.getenv('TESTING') or os.getenv('CI'):
        # Provide minimal defaults for testing
        settings = Settings(
            jwt_secret_key='test-secret-key-minimum-32-characters',
            database_url='postgresql+asyncpg://test:test@localhost/test',
            mongodb_url='mongodb://localhost:27017',
            redis_url='redis://localhost:6379',
        )
    else:
        raise e
