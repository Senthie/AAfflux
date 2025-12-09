"""
Author: Senthie seemoon2077@gmail.com
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-08 12:28:59
FilePath: /api/tests/conftest.py
FilePath: /api/tests/conftest.py
Description:Pytest configuration and fixtures.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

import os
from typing import AsyncGenerator

from dotenv import load_dotenv
import pytest

# Monkey patch JSONB to use JSON for SQLite compatibility
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 加载测试环境配置
load_dotenv('.env.test')

# 从环境变量获取测试数据库 URL
TEST_DATABASE_URL = os.getenv(
    'DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@14.12.0.102:5432/lowcode_test'
)
from dotenv import load_dotenv
from sqlmodel import SQLModel

from app.core.config import settings


@pytest.fixture(scope='function')
async def test_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session.

    Note: This uses the real database from .env file.
    Tables are created if they don't exist, but NOT dropped after tests.
    Each test gets its own engine and session to avoid event loop issues.
    """
    # 创建引擎
    engine = create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
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
