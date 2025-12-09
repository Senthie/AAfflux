"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-05 17:49:22
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-09 15:49:34
FilePath: : AAfflux: api: app: services: user_service.py
Description:用户管理服务
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import UploadFile, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from passlib.context import CryptContext

from app.models.auth.user import User
from app.schemas.user import UserUpdateRequest


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class UserService:
    """用户管理服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """根据ID获取用户"""
        result = await self.session.execute(
            select(User).where(User.id == user_id, User.is_deleted is False)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await self.session.execute(
            select(User).where(User.email == email, User.is_deleted is False)
        )
        return result.scalar_one_or_none()

    async def update_user(self, user: User, update_data: UserUpdateRequest) -> User:
        """更新用户资料"""
        # 检查邮箱是否已被其他用户使用
        if update_data.email and update_data.email != user.email:
            existing_user = await self.get_user_by_email(update_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='该邮箱已被使用',
                )

        # 更新字段
        if update_data.name is not None:
            user.name = update_data.name
        if update_data.email is not None:
            user.email = update_data.email

        user.updated_at = datetime.utcnow()

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def change_password(self, user: User, old_password: str, new_password: str) -> bool:
        """修改密码"""
        # 验证旧密码
        if not pwd_context.verify(old_password, user.password_hash):
            return False

        # 设置新密码
        user.password_hash = pwd_context.hash(new_password)
        user.updated_at = datetime.utcnow()

        self.session.add(user)
        await self.session.commit()
        return True

    async def update_avatar(self, user: User, file: UploadFile) -> str:
        """更新用户头像"""
        # 验证文件类型
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='只支持图片文件',
            )

        # 验证文件大小 (5MB)
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='文件大小不能超过5MB',
            )

        # TODO: 实际项目中应该上传到对象存储服务（如S3、OSS等）
        # 这里简化处理，返回一个模拟的URL
        avatar_url = f'https://example.com/avatars/{user.id}.jpg'

        user.avatar_url = avatar_url
        user.updated_at = datetime.utcnow()

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return avatar_url

    async def soft_delete_user(self, user: User) -> bool:
        """软删除用户"""
        user.soft_delete()
        user.updated_at = datetime.utcnow()

        self.session.add(user)
        await self.session.commit()
        return True

    async def restore_user(self, user_id: UUID) -> Optional[User]:
        """恢复已删除的用户"""
        result = await self.session.execute(
            select(User).where(User.id == user_id, User.is_deleted is True)
        )
        user = result.scalar_one_or_none()

        if user:
            user.restore()
            user.updated_at = datetime.utcnow()
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

        return user
