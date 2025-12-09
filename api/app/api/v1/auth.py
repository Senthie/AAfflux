"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-09 16:33:45
FilePath: : AAfflux: api: app: api: v1: auth.py
Description: 认证相关API端点
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.redis import get_redis, RedisClient
from app.services.auth_service import AuthService
from app.schemas.auth_schema import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenPair,
    PasswordResetRequest,
    PasswordResetConfirm,
)

router = APIRouter(prefix='/auth', tags=['Authentication'])

# 依赖注入定义
DbSession = Annotated[AsyncSession, Depends(get_session)]
Redis = Annotated[RedisClient, Depends(get_redis)]


def get_auth_service(db: DbSession, redis: Redis) -> AuthService:
    """获取认证服务实例"""
    return AuthService(db, redis)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    '/register',
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary='用户注册',
)
async def register(
    request: RegisterRequest,
    auth_service: AuthServiceDep,
) -> RegisterResponse:
    """
    用户注册

    - **email**: 用户邮箱（唯一）
    - **password**: 密码（至少8位，包含大小写字母和数字）
    - **name**: 用户姓名
    """
    try:
        response = await auth_service.register(request)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post(
    '/login',
    response_model=LoginResponse,
    summary='用户登录',
)
async def login(
    request: LoginRequest,
    auth_service: AuthServiceDep,
) -> LoginResponse:
    """
    用户登录

    - **email**: 用户邮箱
    - **password**: 密码

    返回用户信息和访问令牌
    """
    try:
        response = await auth_service.login(request)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@router.post(
    '/refresh',
    response_model=TokenPair,
    summary='刷新访问令牌',
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthServiceDep,
) -> TokenPair:
    """
    使用刷新令牌获取新的访问令牌

    - **refresh_token**: 刷新令牌
    """
    try:
        tokens = await auth_service.refresh_token(request.refresh_token)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@router.post(
    '/logout',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='用户登出',
)
async def logout(
    access_token: str,
    refresh_token: str,
    auth_service: AuthServiceDep,
) -> None:
    """
    用户登出，撤销令牌

    - **access_token**: 访问令牌
    - **refresh_token**: 刷新令牌
    """
    await auth_service.logout(access_token, refresh_token)


@router.post(
    '/reset-password',
    status_code=status.HTTP_200_OK,
    summary='发起密码重置',
)
async def reset_password(
    request: PasswordResetRequest,
    auth_service: AuthServiceDep,
) -> dict:
    """
    发起密码重置流程

    - **email**: 用户邮箱

    系统会发送重置链接到用户邮箱（实际项目中需要实现邮件发送）
    """
    try:
        await auth_service.reset_password(request.email)
        return {
            'message': '密码重置邮件已发送，请查收',
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    '/confirm-reset-password',
    status_code=status.HTTP_200_OK,
    summary='确认密码重置',
)
async def confirm_reset_password(
    request: PasswordResetConfirm,
    auth_service: AuthServiceDep,
) -> dict:
    """
    使用重置令牌设置新密码

    - **token**: 密码重置令牌
    - **new_password**: 新密码（至少8位，包含大小写字母和数字）
    """
    try:
        await auth_service.confirm_password_reset(request.token, request.new_password)
        return {
            'message': '密码重置成功',
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
