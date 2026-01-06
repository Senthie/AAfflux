"""Authentication related Pydantic schemas."""

from datetime import datetime
import re
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.exceptions import PasswordValidationException
from app.enums.custom_response_code_enum import CustomResponseCodeEnum


class RegisterRequest(BaseModel):
    """User registration request schema."""

    email: EmailStr
    password: str = Field(..., max_length=100)
    name: str = Field(..., min_length=1, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise PasswordValidationException(CustomResponseCodeEnum.PASSWORD_TOO_SHORT)
        if not re.search(r'[A-Z]', v):
            raise PasswordValidationException(CustomResponseCodeEnum.PASSWORD_MISSING_UPPERCASE)
        if not re.search(r'[a-z]', v):
            raise PasswordValidationException(CustomResponseCodeEnum.PASSWORD_MISSING_LOWERCASE)
        if not re.search(r'\d', v):
            raise PasswordValidationException(CustomResponseCodeEnum.PASSWORD_MISSING_DIGIT)
        return v


class LoginRequest(BaseModel):
    """User login request schema."""

    email: EmailStr
    password: str


class TokenPair(BaseModel):
    """Token pair response schema."""

    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
    expires_in: int  # Access token expiration in seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class UserResponse(BaseModel):
    """User response schema."""

    id: UUID
    email: str
    name: str
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class RegisterResponse(BaseModel):
    """Registration response schema."""

    user: UserResponse
    tokens: TokenPair


class LoginResponse(BaseModel):
    """Login response schema."""

    user: UserResponse
    tokens: TokenPair


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""

    token: str
    new_password: str = Field(..., max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise PasswordValidationException(CustomResponseCodeEnum.PASSWORD_TOO_SHORT)
        if not re.search(r'[A-Z]', v):
            raise PasswordValidationException(CustomResponseCodeEnum.PASSWORD_MISSING_UPPERCASE)
        if not re.search(r'[a-z]', v):
            raise PasswordValidationException(CustomResponseCodeEnum.PASSWORD_MISSING_LOWERCASE)
        if not re.search(r'\d', v):
            raise PasswordValidationException(CustomResponseCodeEnum.PASSWORD_MISSING_DIGIT)
        return v
