"""用户模型 - 1张表。

本模块定义了系统的用户认证模型。
"""

from typing import Optional
from sqlmodel import Field
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin


class User(BaseModel, TimestampMixin, SoftDeleteMixin, table=True):
    """用户表 - 系统用户账户。

    存储系统用户的基本信息和认证凭证。
    用户可以属于多个团队，通过 TeamMember 表建立关联。
    实现了软删除的字段设计

    Attributes:
        已经使用继承不需要重新写
        id: 用户唯一标识符（UUID）
        created_at: 创建时间
        updated_at: 最后更新时间
        deleted_at: Optional[datetime] = Field(default=None)
        is_deleted: bool = Field(default=False)

        name: 用户姓名
        email: 用户邮箱（唯一，用于登录）
        password_hash: 密码哈希值
        avatar_url: 头像URL
    """

    __tablename__ = 'users'
    name: str = Field(max_length=255)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
