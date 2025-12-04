"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-04 06:14:57
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-04 07:34:26
FilePath: /api/app/models/application/prompt_template.py
Description:提示词模板模型 - 2张表。
            本模块定义了提示词模板相关的数据模型：
            1. PromptTemplate - 提示词模板表
            2. PromptTemplateVersion - 提示词模板版本表

支持模板的版本管理和变量替换功能。
Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from uuid import UUID

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field

from app.models.base import AuditMixin, BaseModel, TimestampMixin, WorkspaceMixin


class PromptTemplate(BaseModel, TimestampMixin, AuditMixin, WorkspaceMixin, table=True):
    """提示词模板表 - 可复用的提示词配置。

    存储提示词模板的当前版本和元信息。
    支持变量占位符（{{variable_name}}格式）。

    Attributes:
    已经继承
        id: 模板唯一标识符（UUID）
        created_by: 创建者用户ID（逻辑外键）
        created_at: 创建时间
        updated_at: 最后更新时间
        workspace_id: 所属工作空间ID（逻辑外键，租户隔离）

        content: 模板内容
        variables: 变量列表（JSONB格式）
        version: 当前版本号
        name: 模板名称

    """

    __tablename__ = 'prompt_templates'
    name: str = Field(max_length=255)
    content: str
    variables: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    version: int = Field(default=1)


class PromptTemplateVersion(BaseModel, TimestampMixin, table=True):
    """提示词模板版本表 - 模板的历史版本。

    保存提示词模板的所有历史版本，支持版本回滚。
    每次更新模板时创建新版本记录。

    Attributes:
    已经继承
        id: 版本记录唯一标识符（UUID）
        created_at: 创建时间

        template_id: 所属模板ID（逻辑外键）
        version: 版本号
        content: 该版本的模板内容

    """

    __tablename__ = 'prompt_template_versions'
    template_id: UUID = Field(index=True)  # Logical FK to prompt_templates
    version: int
    content: str
