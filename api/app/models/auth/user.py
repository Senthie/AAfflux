"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-04 06:26:55
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-04 07:36:10
FilePath: /api/app/models/auth/user.py
Description:
    用户模型 - 1张表。
    本模块定义了系统的用户认证模型。

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Optional

from sqlmodel import Field

from app.models.base import BaseModel, TimestampMixin


class User(BaseModel, TimestampMixin, table=True):
    """用户表 - 系统用户账户。

    存储系统用户的基本信息和认证凭证。
    用户可以属于多个团队，通过 TeamMember 表建立关联。

    Attributes:
        已经使用继承不需要重新写
        id: 用户唯一标识符（UUID）
        created_at: 创建时间
        updated_at: 最后更新时间

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
