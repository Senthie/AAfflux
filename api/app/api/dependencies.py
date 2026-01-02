"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-22 12:17:15
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-22 14:30:23
FilePath: : AAfflux: api: app: api: dependencies.py
Description: API依赖注入模块
"""

from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session as _get_session
from app.middleware.auth import get_current_user as _get_current_user
from app.models.auth.user import UserEntity


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话依赖"""
    async for session in _get_session():
        yield session


async def get_current_user(request: Request) -> UserEntity:
    """获取当前用户依赖"""
    return await _get_current_user(request)


# 为了向后兼容，提供同步版本的依赖（如果需要）
def get_session_sync():
    """同步版本的数据库会话依赖（待实现）"""
    pass


def get_current_user_sync():
    """同步版本的当前用户依赖（待实现）"""
    pass
