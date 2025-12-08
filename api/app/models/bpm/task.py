"""任务模型"""

from datetime import datetime
from enum import StrEnum
from typing import Optional
from uuid import UUID

from sqlmodel import JSON, Column, Field

from app.models.base import BaseModel, TimestampMixin, WorkspaceMixin


class TaskStatus(StrEnum):
    """任务状态"""

    PENDING = 'pending'  # 待处理
    ASSIGNED = 'assigned'  # 已分配
    IN_PROGRESS = 'in_progress'  # 处理中
    COMPLETED = 'completed'  # 已完成
    REJECTED = 'rejected'  # 已拒绝
    CANCELLED = 'cancelled'  # 已取消
    TIMEOUT = 'timeout'  # 已超时
    PENDING = 'pending'  # 待处理
    ASSIGNED = 'assigned'  # 已分配
    IN_PROGRESS = 'in_progress'  # 处理中
    COMPLETED = 'completed'  # 已完成
    REJECTED = 'rejected'  # 已拒绝
    CANCELLED = 'cancelled'  # 已取消
    TIMEOUT = 'timeout'  # 已超时


class TaskType(StrEnum):
    """任务类型"""

    USER_TASK = 'user_task'  # 人工任务
    SERVICE_TASK = 'service_task'  # 服务任务
    SCRIPT_TASK = 'script_task'  # 脚本任务
    APPROVAL_TASK = 'approval_task'  # 审批任务
    USER_TASK = 'user_task'  # 人工任务
    SERVICE_TASK = 'service_task'  # 服务任务
    SCRIPT_TASK = 'script_task'  # 脚本任务
    APPROVAL_TASK = 'approval_task'  # 审批任务


class Task(BaseModel, TimestampMixin, WorkspaceMixin, table=True):
    """任务表 - 流程中的具体任务（待办事项）

    已经继承
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # 租户隔离
    workspace_id: UUID = Field(foreign_key="workspaces.id", index=True)

    # 创建信息
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    """

    __tablename__ = 'bpm_tasks'
    __tablename__ = 'bpm_tasks'

    # 关联流程实例（逻辑外键）
    process_instance_id: UUID = Field(index=True, description='流程实例ID')

    # 任务定义
    task_def_key: str = Field(max_length=100, description='任务定义键（节点ID）')
    task_name: str = Field(max_length=255, description='任务名称')
    task_type: TaskType = Field(default=TaskType.USER_TASK, description='任务类型')
    task_def_key: str = Field(max_length=100, description='任务定义键（节点ID）')
    task_name: str = Field(max_length=255, description='任务名称')
    task_type: TaskType = Field(default=TaskType.USER_TASK, description='任务类型')

    # 任务描述
    description: Optional[str] = Field(default=None, description='任务描述')
    description: Optional[str] = Field(default=None, description='任务描述')

    # 任务分配（逻辑外键）
    assignee: Optional[UUID] = Field(default=None, index=True, description='任务处理人用户ID')
    candidate_users: dict = Field(
        default_factory=dict, sa_column=Column(JSON), description='候选用户列表'
    )
    candidate_groups: dict = Field(
        default_factory=dict, sa_column=Column(JSON), description='候选组列表'
    )

    # 任务状态
    status: TaskStatus = Field(default=TaskStatus.PENDING, index=True)

    # 优先级
    priority: int = Field(default=50, description='优先级（0-100）')
    priority: int = Field(default=50, description='优先级（0-100）')

    # 时间限制
    due_date: Optional[datetime] = Field(default=None, description='截止时间')
    follow_up_date: Optional[datetime] = Field(default=None, description='跟进时间')
    due_date: Optional[datetime] = Field(default=None, description='截止时间')
    follow_up_date: Optional[datetime] = Field(default=None, description='跟进时间')

    # 表单数据
    form_key: Optional[str] = Field(default=None, description='表单键')
    form_data: Optional[dict] = Field(default=None, sa_column=Column(JSON), description='表单数据')
    form_key: Optional[str] = Field(default=None, description='表单键')
    form_data: Optional[dict] = Field(default=None, sa_column=Column(JSON), description='表单数据')

    # 任务变量
    variables: dict = Field(default_factory=dict, sa_column=Column(JSON), description='任务变量')
    variables: dict = Field(default_factory=dict, sa_column=Column(JSON), description='任务变量')

    # 执行信息
    claimed_at: Optional[datetime] = Field(default=None, description='认领时间')
    started_at: Optional[datetime] = Field(default=None, description='开始时间')
    completed_at: Optional[datetime] = Field(default=None, description='完成时间')
    duration_seconds: Optional[int] = Field(default=None, description='处理时长（秒）')
    claimed_at: Optional[datetime] = Field(default=None, description='认领时间')
    started_at: Optional[datetime] = Field(default=None, description='开始时间')
    completed_at: Optional[datetime] = Field(default=None, description='完成时间')
    duration_seconds: Optional[int] = Field(default=None, description='处理时长（秒）')

    # 结果
    result: Optional[dict] = Field(default=None, sa_column=Column(JSON), description='任务结果')
    comment: Optional[str] = Field(default=None, description='处理意见')
    result: Optional[dict] = Field(default=None, sa_column=Column(JSON), description='任务结果')
    comment: Optional[str] = Field(default=None, description='处理意见')

    class Config:
        json_schema_extra = {
            'example': {
                'task_def_key': 'manager_approval',
                'task_name': '部门主管审批',
                'task_type': 'approval_task',
                'description': '请审批工作空间创建申请',
                'assignee': 'user_uuid',
                'status': 'pending',
                'priority': 80,
                'form_data': {'workspace_name': '新工作空间', 'applicant': '张三'},
            }
        }
