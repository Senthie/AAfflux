"""认证相关模型 - 2张表。

本模块定义了认证相关的数据模型：
1. RefreshToken - 刷新令牌表
2. PasswordReset - 密码重置表

这些表支持用户认证、令牌管理和密码重置功能。
"""

from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from sqlmodel import SQLModel, Field


class RefreshToken(SQLModel, table=True):
    """刷新令牌表 - 管理用户刷新令牌。
    
    存储用户的刷新令牌，用于获取新的访问令牌。
    支持令牌撤销和过期管理。
    
    Attributes:
        id: 令牌记录唯一标识符（UUID）
        user_id: 用户ID（逻辑外键）
        token_hash: 令牌哈希值（唯一）
        expires_at: 过期时间
        revoked: 是否已撤销
        created_at: 创建时间
    
    业务规则：
        - 每个用户可以有多个有效的刷新令牌（支持多设备登录）
        - 令牌过期或撤销后不能再使用
        - 登出时撤销对应的刷新令牌
    """
    __tablename__ = "refresh_tokens"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True)  # Logical FK to users
    token_hash: str = Field(max_length=255, unique=True, index=True)
    expires_at: datetime
    revoked: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class PasswordReset(SQLModel, table=True):
    """密码重置表 - 管理密码重置请求。
    
    存储密码重置请求的令牌，用于验证用户身份。
    令牌有时效性，使用后失效。
    
    Attributes:
        id: 重置记录唯一标识符（UUID）
        user_id: 用户ID（逻辑外键）
        token: 重置令牌（唯一）
        expires_at: 过期时间
        used: 是否已使用
        created_at: 创建时间
    
    业务规则：
        - 令牌通过邮件发送给用户
        - 令牌有效期通常为1小时
        - 使用后立即标记为已使用
        - 过期的令牌不能使用
    """
    __tablename__ = "password_resets"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True)  # Logical FK to users
    token: str = Field(max_length=255, unique=True, index=True)
    expires_at: datetime
    used: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
