"""用户模型 - 1张表。

本模块定义了系统的用户认证模型。
"""

from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    """用户表 - 系统用户账户。
    
    存储系统用户的基本信息和认证凭证。
    用户可以属于多个团队，通过 TeamMember 表建立关联。
    
    Attributes:
        id: 用户唯一标识符（UUID）
        email: 用户邮箱（唯一，用于登录）
        password_hash: 密码哈希值
        name: 用户姓名
        avatar_url: 头像URL
        created_at: 创建时间
        updated_at: 最后更新时间
    """
    __tablename__ = "users"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    name: str = Field(max_length=255)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
