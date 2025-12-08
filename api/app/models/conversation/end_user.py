"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-02 11:31:11
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-08 14:46:26
FilePath: : AAfflux: api: app: models: conversation: end_user.py
Description:添加了softdelete软删除字段
"""

"""终端用户模型 - 1张表。

本模块定义了终端用户（C端用户）的数据模型。
终端用户是使用已发布应用的最终用户，与租户用户（B端）不同。
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field
from app.models.base import BaseModel, TimestampMixin, WorkspaceMixin, SoftDeleteMixin
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column


class EndUser(BaseModel, WorkspaceMixin, TimestampMixin, SoftDeleteMixin, table=True):
    """终端用户表 - C端用户。

    存储使用已发布应用的终端用户信息。
    终端用户由租户的应用创建，属于特定的工作空间。

    Attributes:
    已经继承
        id: 终端用户唯一标识符（UUID）
        workspace_id: 所属工作空间ID（逻辑外键，租户隔离）
        created_at: 创建时间
        deleted_at: Optional[datetime] = Field(default=None)
        is_deleted: bool = Field(default=False)


        session_id: 会话标识符（用于匿名用户追踪）
        external_user_id: 外部系统用户ID（可选，用于集成）
        name: 用户名称
        email: 用户邮箱（可选）
        phone: 用户手机号（可选）
        avatar_url: 头像URL
        metadata: 自定义元数据（JSONB格式）
        is_anonymous: 是否匿名用户
        last_active_at: 最后活跃时间


    业务规则：
        - 终端用户属于特定工作空间，实现租户隔离
        - 支持匿名用户（通过 session_id 追踪）
        - 支持与外部系统集成（通过 external_user_id）
        - 可以存储自定义元数据用于个性化
    """

    __tablename__ = 'end_users'

    session_id: str = Field(max_length=255, index=True)
    external_user_id: Optional[str] = Field(default=None, max_length=255, index=True)
    name: str = Field(max_length=255)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    custom_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    is_anonymous: bool = Field(default=False, index=True)
    last_active_at: Optional[datetime] = None
