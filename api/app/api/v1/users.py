"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-05 17:50:01
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-08 17:58:37
FilePath: : AAfflux: api: app: api: v1: users.py
Description: 用户管理，增删改查
"""

from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, HTTPException, File, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.middleware.auth import get_current_user
from app.services.user_service import UserService
from app.schemas.user import (
    UserProfileResponse,
    UserUpdateRequest,
    PasswordChangeRequest,
    PasswordChangeResponse,
    AvatarUploadResponse,
    UserDeleteResponse,
)

from app.models.auth.user import User

router = APIRouter(PREFIX='/users', tags=['User Management'])

# 依赖注入定义
DbSession = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get('/me', response_model=UserProfileResponse, summary='获取当前用户信息')
async def get_current_user_info(current_user: CurrentUser) -> UserProfileResponse:
    """获取当前登陆用户的详细信息"""
    return UserProfileResponse.model_validate(current_user)


@router.put('/me', response_model=UserProfileResponse, summary='更新用户资料')
async def update_user_profile(
    user_update: UserUpdateRequest, current_user: CurrentUser, session: DbSession
) -> UserProfileResponse:
    """更新用户资料（用户名、邮箱等）"""
    service = UserService(session)
    updated_user = await service.update_user(user=current_user, update_data=user_update)
    return UserProfileResponse.model_validate(updated_user)


@router.post(
    '/me/password',
    response_model=PasswordChangeResponse,
    summary='修改密码',
)
async def change_password(
    password_data: PasswordChangeRequest, current_user: CurrentUser, session: DbSession
) -> PasswordChangeResponse:
    """修改当前用户密码"""
    service = UserService(session)
    success = await service.change_password(
        user=current_user,
        old_password=password_data.old_password,
        new_password=password_data.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='旧密码不正确',
        )
    return PasswordChangeResponse(
        success=True,
        message='密码修改成功',
    )


@router.post(
    '/me/avatar',
    response_model=AvatarUploadResponse,
    summary='上传头像/更新头像',
)
async def upload_avatar(
    current_user: CurrentUser,
    session: DbSession,
    file: UploadFile = File(..., description='头像文件'),
) -> AvatarUploadResponse:
    """上传/更新头像"""
    service = UserService(session)
    avatar_url = await service.update_avatar(user=current_user, file=file)

    return AvatarUploadResponse(
        avatar_url=avatar_url,
        message='头像上传成功',
    )


@router.delete(
    '/me',
    response_model=UserDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary='删除账户',
)
async def delete_account(current_user: CurrentUser, session: DbSession) -> UserDeleteResponse:
    """删除账号（软删除）"""
    service = UserService(session)
    success = await service.soft_delete_user(user=current_user)

    return UserDeleteResponse(
        success=success,
        message='账号已删除',
        user_id=current_user.id,
    )
