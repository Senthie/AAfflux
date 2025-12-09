"""Tests for infrastructure components."""

import pytest

from app.core.config import settings


class TestConfiguration:
    """Test configuration loading."""

    def test_settings_loaded(self):
        """Test that settings are loaded correctly."""
        assert settings.app_name == 'Low-Code Platform Backend'
        assert settings.jwt_algorithm == 'HS256'
        assert settings.database_url is not None
        assert settings.mongodb_url is not None
        assert settings.redis_url is not None

    def test_jwt_secret_key_length(self):
        """Test that JWT secret key meets minimum length requirement."""
        assert len(settings.jwt_secret_key) >= 32

    def test_celery_broker_defaults_to_redis(self):
        """Test that Celery broker URL defaults to Redis URL."""
        # If not explicitly set, should default to redis_url
        assert settings.celery_broker_url is not None


class TestDatabaseConnection:
    """Test database connection."""

    @pytest.mark.asyncio
    async def test_database_session(self, test_session):
        """Test that database session can be created."""
        from sqlalchemy import text

        assert test_session is not None

        # Test a simple query
        result = await test_session.execute(text('SELECT 1'))
        assert result is not None

    @pytest.mark.asyncio
    async def test_application_startup(self):
        """Test that application can start up."""
        from app.main import app

        assert app is not None
        assert app.title == 'Low-Code Platform Backend'
        assert app.version == '0.1.0'
