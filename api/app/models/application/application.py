"""应用模型 - 1张表。

本模块定义了应用管理的数据模型。
应用是对外发布的工作流实例，提供API端点供外部调用。
"""

from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class Application(SQLModel, table=True):
    """应用表 - 发布的AI应用。
    
    应用是工作流的对外发布形式，提供API端点供外部系统调用。
    每个应用关联一个工作流，并有独立的API密钥和配置。
    
    Attributes:
        id: 应用唯一标识符（UUID）
        name: 应用名称
        workspace_id: 所属工作空间ID（逻辑外键，租户隔离）
        workflow_id: 关联的工作流ID（逻辑外键）
        api_key_hash: API密钥哈希值
        endpoint: API端点路径
        is_published: 是否已发布
        config: 应用配置（JSONB格式）
        created_by: 创建者用户ID（逻辑外键）
        created_at: 创建时间
        updated_at: 最后更新时间
    """
    __tablename__ = "applications"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255)
    workspace_id: UUID = Field(index=True)  # Logical FK to workspaces (租户隔离)
    workflow_id: UUID = Field(index=True)  # Logical FK to workflows
    api_key_hash: str = Field(max_length=255)
    endpoint: str = Field(max_length=500)
    is_published: bool = Field(default=False)
    config: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    created_by: UUID = Field(index=True)  # Logical FK to users
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
