"""表单模型"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Column, JSON
from app.models.base import BaseModel, TimestampMixin, WorkspaceMixin, AuditMixin


class FormDefinition(BaseModel, TimestampMixin, AuditMixin, WorkspaceMixin, table=True):
    """表单定义表

    已经继承
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # 租户隔离
    workspace_id: Optional[UUID] = Field(default=None, foreign_key="workspaces.id", index=True)

    # 创建信息
    created_by: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    """

    __tablename__ = 'bpm_form_definitions'

    # 表单标识
    key: str = Field(max_length=100, unique=True, index=True, description='表单唯一标识')
    name: str = Field(max_length=255, description='表单名称')
    description: Optional[str] = Field(default=None, description='表单描述')

    # 表单 Schema（JSON Schema）
    form_schema: dict = Field(sa_column=Column(JSON), description='表单结构定义')

    # UI Schema（表单渲染配置）
    ui_schema: Optional[dict] = Field(default=None, sa_column=Column(JSON), description='UI配置')

    # 版本
    version: int = Field(default=1, description='版本号')

    # 状态
    is_active: bool = Field(default=True, description='是否激活')


class FormData(SQLModel, table=True):
    """表单数据表"""

    __tablename__ = 'bpm_form_data'

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # 关联（逻辑外键）
    process_instance_id: UUID = Field(index=True, description='流程实例ID')
    task_id: Optional[UUID] = Field(default=None, index=True, description='任务ID')
    form_definition_id: UUID = Field(description='表单定义ID')

    # 表单数据
    data: dict = Field(sa_column=Column(JSON), description='表单数据')

    # 提交信息（逻辑外键）
    submitted_by: UUID = Field(description='提交人用户ID')
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    # 租户隔离（逻辑外键）
    workspace_id: UUID = Field(index=True, description='工作空间ID')
