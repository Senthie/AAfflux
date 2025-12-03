"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-02 08:55:33
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-03 07:29:19
FilePath: /api/app/services/auth_service.py
Description:

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Optional
from redis import Redis
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.AuthSchema import TokenSchema
from app.core.config import Settings
from app.core.security import TokenManager, PasswordManager
from app.core.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
)


class AuthService:

    def __init__(
        self,
        db_session: AsyncSession,
        token_manager: TokenManager,
        password_manager: PasswordManager,
        redis_client: Redis,
        config: Settings,
    ):
        self.db = db_session
        self.token_manager = token_manager
        self.password_manager = password_manager
        self.redis = redis_client
        self.config = config

    def _validate_email(self, email: str) -> None:
        """
        验证邮箱是否正确

        :param  str email 邮箱地址
        """
        pass

    def _validate_password(self, password: str):
        """
        验证密码是否正确

        :param str password: 密码数据
        """
        pass

    async def register(self, email: str, password: str, name: str) -> User:
        """
        用户注册逻辑

        :param str email: 邮箱
        :param str password: 未经过加密的密码
        :param str name: 用户名
        """
        # 1. 验证输入
        self._validate_email(email)
        self._validate_password(password)

        # 2. 检测用户是否存在
        existing_user = await self._get_user_by_email(email)
        if existing_user:
            raise UserAlreadyExistsError("用户已存在")

        # 3. 创建用户
        password_hash = self.password_manager.hash_password(password)
        user = await self._create_user(email, password_hash, name)

        return user

    async def login(
        self, email: str, password_has: str, invite_token: str | None = None
    ) -> TokenSchema:
        # 1. 从数据库查询相关的数据
        verification_user = await self._get_user_by_email(email)

        # 2. 验证用户是否存在
        if not verification_user:
            raise InvalidCredentialsError("用户名或密码错误")

        # 3. 验证密码
        if not self.password_manager.verify_password(password_has, verification_user.password_hash):
            raise InvalidCredentialsError("用户名或密码错误")

        # 4. 生成令牌对
        access_token = self.token_manager.create_accesss_token(verification_user.id)
        refresh_token = self.token_manager.create_refresh_token(verification_user.id)

        # 5. 存储刷新令牌
        await self._store_refresh_token(verification_user.id, refresh_token)

        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_token(self, refresh_token: str) -> TokenSchema:
        """刷新访问令牌"""

        # 1. 验证令牌
        payload = self.token_manager.verify_refresh_token(refresh_token)
        user_id = payload.get("sub")

        # 2. 检查令牌是否在黑名单
        if await self._is_token_blacklisted(refresh_token):
            raise InvalidTokenError("令牌已经失效")

        # 3. 验证用户是否存在
        user = await self._get_user_by_id(user_id)
        if not user:
            raise InvalidTokenError("用户不存在")

        # 4. 生成新的令牌对
        new_access_token = self.token_manager.create_accesss_token(user.id)
        new_refresh_token = self.token_manager.create_refresh_token(user.id)

        # 5. 撤销旧的刷新令牌，存储新的
        await self._blacklist_token(refresh_token)
        await self._store_refresh_token(user.id, new_refresh_token)

        return TokenSchema(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=self.config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """登出，撤销令牌"""
        # 1. 将访问令牌加入黑名单
        await self._blacklist_token(access_token)

        # 2. 如果提供了刷新令牌，也加入黑名单
        if refresh_token:
            await self._blacklist_token(refresh_token)

        # 3. 清理用户的所有刷新令牌
        payload = self.token_manager.verify_access_token(access_token, verify_expiry=False)
        user_id = payload.get("sub")
        await self._revoke_all_refresh_tokens(user_id)

    async def reset_password(self, email: str) -> None:
        """发送密码重置邮件"""
        pass

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        pass

    async def _get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        pass

    async def _create_user(self, email: str, password_hash: str, name: str) -> User:
        """创建新用户"""
        pass

    async def _store_refresh_token(self, user_id: int, refresh_token: str) -> None:
        """存储刷新令牌到Redis"""
        pass

    async def _is_token_blacklisted(self, token: str) -> bool:
        """检查令牌是否在黑名单中"""
        pass

    async def _blacklist_token(self, token: str) -> None:
        """将令牌加入黑名单"""
        pass

    async def _revoke_all_refresh_tokens(self, user_id: int) -> None:
        """撤销用户的所有刷新令牌"""
        pass
