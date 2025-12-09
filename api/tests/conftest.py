"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-08 09:58:13
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-09 01:29:32
FilePath: /api/tests/conftest.py
Description:Pytest configuration and fixtures.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import AsyncGenerator

import pytest

# Monkey patch JSONB to use JSON for SQLite compatibility
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings


@pytest.fixture(scope='function')
async def test_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session.

    Note: This uses the real database from .env file.
    Tables are created if they don't exist, but NOT dropped after tests.
    Each test gets its own engine and session to avoid event loop issues.
    """
    # Create async engine for this test
    engine = create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
    )

    # Ensure tables exist (idempotent operation)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()

    # Dispose engine after test
    await engine.dispose()
