"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-02 08:50:10
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-09 11:09:47
FilePath: : AAfflux: api: tests: conftest.py
Description: 
"""
"""Pytest configuration and fixtures."""

import os
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from sqlmodel import SQLModel
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
    engine = create_async_engine(
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
