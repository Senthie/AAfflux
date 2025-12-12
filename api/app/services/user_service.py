"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-05 17:49:22
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-12 11:09:37
FilePath: : AAfflux: api: app: services: user_service.py
Description:用户管理服务
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import UploadFile, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


from app.models.auth.user import User
from app.schemas.user import UserUpdateRequest

from app.utils.password import get_password_hash, verify_password


class UserService:
    """用户管理服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """根据ID获取用户"""
        result = await self.session.execute(
            select(User).where(User.id == user_id, User.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await self.session.execute(
            select(User).where(User.email == email, User.is_deleted.is_(False))
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
        if not verify_password(old_password, user.password_hash):
            return False

        # 设置新密码
        user.password_hash = get_password_hash(new_password)
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

        # 重置文件指针
        await file.seek(0)

        # 使用文件服务上传头像
        from app.services.file_server import FileService

        file_service = FileService(self.session)

        # 创建一个默认工作空间ID（或从用户获取）
        workspace_id = UUID('00000000-0000-0000-0000-000000000000')  # 系统默认工作空间

        file_reference = await file_service.upload_file(
            file=file,
            workspace_id=workspace_id,
            uploaded_by=user.id,
        )

        # 生成头像访问URL
        avatar_url = f'/api/v1/files/{file_reference.file_id}/view'

        user.avatar_url = avatar_url
        user.updated_at = datetime.utcnow()

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return avatar_url

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
        # 需要在 UserService 中添加

    async def delete_user(self, user_id: UUID) -> bool:
        """软删除用户"""
        # 这里调用 get_user_by_id 已经隐含了 "is_deleted == False" 的判断
        # 所以如果用户已经被删除了，这里 user 会是 None，直接返回 False
        user = await self.get_user_by_id(user_id)
        if user:
            # 假设 User 模型中有 soft_delete 方法 (设置 is_deleted=True, deleted_at=now)
            user.soft_delete()

            # 标记修改并提交
            self.session.add(user)  # 建议显式 add 一下，虽然某些 ORM 配置下不需要
            await self.session.commit()
            return True
        return False
