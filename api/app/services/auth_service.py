"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-02 08:55:33
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-08 12:02:18
FilePath: : AAfflux: api: app: services: auth_service.py
Description: Authentication service for user registration, login, and token management,补充添加了is_delete,完善业务逻辑

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select

from app.models.auth import User
from app.schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    TokenPair,
    RegisterResponse,
    LoginResponse,
    UserResponse,
)
from app.utils.password import get_password_hash, verify_password
from app.utils.token import (
    generate_access_token,
    generate_refresh_token,
    verify_token,
    TokenType,
)
from app.core.config import settings
from app.core.redis import RedisClient


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, db: Session, redis: RedisClient):
        """
        Initialize AuthService.

        Args:
            db: Database session
            redis: Redis client for token management
        """
        self.db = db
        self.redis = redis

    async def register(self, request: RegisterRequest) -> RegisterResponse:
        """
        Register a new user.

        Args:
            request: Registration request data

        Returns:
            RegisterResponse with user data and tokens

        Raises:
            ValueError: If email already exists
        """
        # Check if user already exists
        statement = select(User).where(
            User.email == request.email,
            User.is_deleted.is_(False),  # 原始使用 ‘==’ 不符合ruff规则 改为is
        )
        existing_user = self.db.exec(statement).first()

        if existing_user:
            raise ValueError('Email already registered')

        # Create new user
        password_hash = get_password_hash(request.password)
        user = User(
            email=request.email,
            password_hash=password_hash,
            name=request.name,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Generate tokens
        tokens = await self._generate_token_pair(user.id)

        return RegisterResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    async def login(self, request: LoginRequest) -> LoginResponse:
        """
        Authenticate user and generate tokens.

        Args:
            request: Login request data

        Returns:
            LoginResponse with user data and tokens

        Raises:
            ValueError: If credentials are invalid
        """
        # Find user by email
        statement = select(User).where(User.email == request.email, User.is_deleted.is_(False))
        user = self.db.exec(statement).first()

        if not user:
            raise ValueError('Invalid email or password')

        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise ValueError('Invalid email or password')

        # Generate tokens
        tokens = await self._generate_token_pair(user.id)

        return LoginResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New token pair

        Raises:
            ValueError: If refresh token is invalid or revoked
        """
        # Verify refresh token
        payload = verify_token(refresh_token, token_type=TokenType.REFRESH)

        if not payload:
            raise ValueError('Invalid or expired refresh token')

        user_id = UUID(payload['user_id'])

        # Check if token is revoked
        revoked_key = f'revoked_token:{refresh_token}'
        if await self.redis.exists(revoked_key):
            raise ValueError('Token has been revoked')

        # Verify user still exists
        user = self.db.get(User, user_id)
        if not user or user.is_deleted:
            raise ValueError('User not found')

        # Generate new token pair
        tokens = await self._generate_token_pair(user_id)

        return tokens

    async def logout(self, access_token: str, refresh_token: str) -> None:
        """
        Logout user by revoking tokens.

        Args:
            access_token: Access token to revoke
            refresh_token: Refresh token to revoke
        """
        # Revoke both tokens by storing them in Redis with expiration
        access_payload = verify_token(access_token, token_type=TokenType.ACCESS)
        refresh_payload = verify_token(refresh_token, token_type=TokenType.REFRESH)

        # Calculate remaining TTL for tokens
        if access_payload:
            access_exp = access_payload.get('exp')
            if access_exp:
                access_ttl = max(0, access_exp - int(datetime.utcnow().timestamp()))
                await self.redis.set(
                    f'revoked_token:{access_token}',
                    '1',
                    expire=access_ttl,
                )

        if refresh_payload:
            refresh_exp = refresh_payload.get('exp')
            if refresh_exp:
                refresh_ttl = max(0, refresh_exp - int(datetime.utcnow().timestamp()))
                await self.redis.set(
                    f'revoked_token:{refresh_token}',
                    '1',
                    expire=refresh_ttl,
                )

    async def reset_password(self, email: str) -> None:
        """
        Initiate password reset process.

        Args:
            email: User email address

        Raises:
            ValueError: If user not found
        """
        # Find user by email
        statement = select(User).where(User.email == email, User.is_deleted.is_(False))
        user = self.db.exec(statement).first()

        if not user:
            raise ValueError('User not found')

        # Generate password reset token (valid for 1 hour)
        reset_token = generate_access_token(
            user.id, additional_claims={'purpose': 'password_reset'}
        )

        # Store reset token in Redis with 1 hour expiration
        await self.redis.set(
            f'password_reset:{user.id}',
            reset_token,
            expire=3600,  # 1 hour
        )

        # TODO: Send email with reset link
        # For now, we just store the token
        # In production, you would send an email with a link like:
        # https://yourapp.com/reset-password?token={reset_token}

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        """
        Confirm password reset with token.

        Args:
            token: Password reset token
            new_password: New password

        Raises:
            ValueError: If token is invalid or expired
        """
        # Verify reset token
        payload = verify_token(token)

        if not payload or payload.get('purpose') != 'password_reset':
            raise ValueError('Invalid or expired reset token')

        user_id = UUID(payload['user_id'])

        # Verify token is still in Redis
        stored_token = await self.redis.get(f'password_reset:{user_id}')
        if not stored_token or stored_token != token:
            raise ValueError('Invalid or expired reset token')

        # Get user
        user = self.db.get(User, user_id)
        if not user or user.is_deleted:
            raise ValueError('User not found')

        # Update password
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()

        self.db.add(user)
        self.db.commit()

        # Delete reset token
        await self.redis.delete(f'password_reset:{user_id}')

    async def verify_access_token(self, token: str) -> Optional[User]:
        """
        Verify access token and return user.

        Args:
            token: Access token to verify

        Returns:
            User if token is valid, None otherwise
        """
        # Check if token is revoked
        revoked_key = f'revoked_token:{token}'
        if await self.redis.exists(revoked_key):
            return None

        # Verify token
        payload = verify_token(token, token_type=TokenType.ACCESS)

        if not payload:
            return None

        user_id = UUID(payload['user_id'])

        # Get user from database
        user = self.db.get(User, user_id)
        if user and user.is_deleted:
            return None
        return user

    async def _generate_token_pair(self, user_id: UUID) -> TokenPair:
        """
        Generate access and refresh token pair.

        Args:
            user_id: User UUID

        Returns:
            TokenPair with access and refresh tokens
        """
        access_token = generate_access_token(user_id)
        refresh_token = generate_refresh_token(user_id)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type='bearer',
            expires_in=settings.access_token_expire_minutes * 60,
        )
