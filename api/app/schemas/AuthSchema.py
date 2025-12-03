from typing import Optional, Tuple
from pydantic import BaseModel
from datetime import datetime, timedelta


class TokenSchema(BaseModel):
    """
    Token 令牌的 结构体
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str
