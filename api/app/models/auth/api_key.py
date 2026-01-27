"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:47:34
FilePath: /api/app/models/auth/api_key.py
Description: Api Key数据模型

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Field

from app.models.base import BaseModel, TimestampMixin


class APIKey(BaseModel, TimestampMixin, table=True):
    """API密钥表 - 管理应用API密钥。

    存储应用的API密钥，用于外部系统调用应用API。
    支持密钥的创建、撤销和使用追踪。

    Attributes:
    已经继承
        id: 密钥记录唯一标识符（UUID）
        created_at: 创建时间

        application_id: 应用ID（逻辑外键）
        key_hash: 密钥哈希值（唯一）
        key_prefix: 密钥前缀（用于显示，如 "sk_live_abc..."）
        name: 密钥名称（用户自定义，便于识别）
        last_used_at: 最后使用时间
        is_active: 是否激活


    业务规则：
        - 密钥以哈希形式存储，原始密钥只在创建时显示一次
        - 每个应用可以有多个API密钥
        - 密钥可以随时撤销（设置 is_active = False）
        - 记录最后使用时间用于安全审计
    """

    __tablename__ = 'api_keys'

    application_id: UUID = Field(index=True)  # Logical FK to applications
    key_hash: str = Field(max_length=255, unique=True, index=True)
    key_prefix: str = Field(max_length=20)  # 如 "sk_live_abc"
    name: str = Field(max_length=255)
    last_used_at: Optional[datetime] = None
    is_active: bool = Field(default=True, index=True)
