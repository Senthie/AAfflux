"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-08 09:58:13
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-08 12:25:05
FilePath: /api/tests/conftest.py
Description:Pytest configuration and fixtures.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import AsyncGenerator

import os
import pytest

# Monkey patch JSONB to use JSON for SQLite compatibility
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from sqlmodel import SQLModel

from app.core.config import settings
from dotenv import load_dotenv

# 加载测试环境配置
load_dotenv('.env.test')

# 从环境变量获取测试数据库 URL
TEST_DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql+asyncpg://postgres:postgres@14.12.0.102:5432/lowcode_test'
)


@pytest.fixture(scope='function')
async def test_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session.
    
    每个测试函数使用独立的数据库会话。
    注意：测试结束后需要手动清理数据，或使用唯一的测试数据。
    """
    # 创建引擎

    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    
    # 创建 session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
    
    # 清理引擎
    await engine.dispose()
