"""BPM 流程模型 - 流程定义和流程实例"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from sqlmodel import Field, Column, JSON
from app.models.base import BaseModel, TimestampMixin, WorkspaceMixin, AuditMixin, SoftDeleteMixin


class ProcessDefinition(
    BaseModel, WorkspaceMixin, TimestampMixin, AuditMixin, SoftDeleteMixin, table=True
):
    """流程定义表 - 定义可重用的流程模板

    已经继承
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # 租户隔离
    workspace_id: Optional[UUID] = Field(default=None, foreign_key="workspaces.id", index=True)
    # 创建信息
    created_by: UUID = Field(foreign_key="users.id", description="创建者")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)
    is_deleted: bool = Field(default=False)
    """

    __tablename__ = 'bpm_process_definitions'
    __tablename__ = 'bpm_process_definitions'

    # 流程标识
    key: str = Field(
        index=True, max_length=100, description='流程唯一标识（如：workspace_approval）'

    )
    name: str = Field(max_length=255, description='流程名称')
    description: Optional[str] = Field(default=None, description='流程描述')
    category: Optional[str] = Field(default=None, max_length=50, description='流程分类')
    name: str = Field(max_length=255, description='流程名称')
    description: Optional[str] = Field(default=None, description='流程描述')
    category: Optional[str] = Field(default=None, max_length=50, description='流程分类')

    # 版本控制
    version: int = Field(default=1, description='流程版本号')
    is_latest: bool = Field(default=True, description='是否最新版本')
    version: int = Field(default=1, description='流程版本号')
    is_latest: bool = Field(default=True, description='是否最新版本')

    # 流程定义
    bpmn_xml: Optional[str] = Field(default=None, description='BPMN 2.0 XML 定义')
    bpmn_xml: Optional[str] = Field(default=None, description='BPMN 2.0 XML 定义')
    process_config: dict = Field(
        default_factory=dict, sa_column=Column(JSON), description='流程配置（JSON）'

    )

    # 节点定义
    nodes: dict = Field(default_factory=dict, sa_column=Column(JSON), description='流程节点列表')
    nodes: dict = Field(default_factory=dict, sa_column=Column(JSON), description='流程节点列表')

    # 表单配置
    form_schema: Optional[dict] = Field(
        default=None, sa_column=Column(JSON), description='表单 Schema'

    )

    # 状态
    is_active: bool = Field(default=True, description='是否激活')

    # 统计
    instance_count: int = Field(default=0, description='实例数量')
    instance_count: int = Field(default=0, description='实例数量')

    class Config:
        json_schema_extra = {
            'example': {
                'key': 'workspace_approval',
                'name': '工作空间创建审批',
                'description': '用户申请创建工作空间的审批流程',
                'category': 'tenant_management',
                'version': 1,
                'nodes': [
                    {'id': 'start', 'type': 'start', 'name': '开始'},
                    {
                        'id': 'manager_approval',
                        'type': 'user_task',
                        'name': '部门主管审批',
                        'assignee': 'manager',
                    },

                    {'id': 'end', 'type': 'end', 'name': '结束'},
                ],
            }
        }



class ProcessStatus(str, Enum):
    """流程状态"""

    PENDING = 'pending'  # 待启动
    RUNNING = 'running'  # 运行中
    WAITING = 'waiting'  # 等待中（等待审批）
    SUSPENDED = 'suspended'  # 已暂停
    COMPLETED = 'completed'  # 已完成
    REJECTED = 'rejected'  # 已拒绝
    CANCELLED = 'cancelled'  # 已取消
    FAILED = 'failed'  # 失败
    PENDING = 'pending'  # 待启动
    RUNNING = 'running'  # 运行中
    WAITING = 'waiting'  # 等待中（等待审批）
    SUSPENDED = 'suspended'  # 已暂停
    COMPLETED = 'completed'  # 已完成
    REJECTED = 'rejected'  # 已拒绝
    CANCELLED = 'cancelled'  # 已取消
    FAILED = 'failed'  # 失败


class ProcessInstance(BaseModel, WorkspaceMixin, TimestampMixin, table=True):
    """流程实例表 - 流程定义的具体执行实例

    已经继承
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # 租户隔离
    workspace_id: UUID = Field(foreign_key="workspaces.id", index=True)
    # 创建信息
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    """

    __tablename__ = 'bpm_process_instances'
    __tablename__ = 'bpm_process_instances'

    # 关联流程定义（逻辑外键）
    process_definition_id: UUID = Field(index=True, description='流程定义ID')
    process_key: str = Field(max_length=100, index=True, description='流程标识（冗余）')
    process_version: int = Field(description='流程版本（快照）')

    # 业务关联
    business_key: Optional[str] = Field(
        default=None, max_length=255, index=True, description='业务键（如：application_id）'

    )
    business_type: Optional[str] = Field(default=None, max_length=50, description='业务类型')
    business_type: Optional[str] = Field(default=None, max_length=50, description='业务类型')

    # 关联 Workflow（如果从 Workflow 触发）
    workflow_run_id: Optional[UUID] = Field(
        default=None, index=True, description='关联的工作流执行ID'

    )
    workflow_node_id: Optional[str] = Field(default=None, description='触发的工作流节点ID')
    workflow_node_id: Optional[str] = Field(default=None, description='触发的工作流节点ID')

    # 流程状态
    status: ProcessStatus = Field(default=ProcessStatus.PENDING, index=True)

    # 流程变量
    variables: dict = Field(default_factory=dict, sa_column=Column(JSON), description='流程变量')
    variables: dict = Field(default_factory=dict, sa_column=Column(JSON), description='流程变量')

    # 当前节点
    current_node_id: Optional[str] = Field(default=None, description='当前执行节点ID')
    current_task_id: Optional[UUID] = Field(default=None, description='当前任务ID')
    current_node_id: Optional[str] = Field(default=None, description='当前执行节点ID')
    current_task_id: Optional[UUID] = Field(default=None, description='当前任务ID')

    # 执行信息
    started_at: Optional[datetime] = Field(default=None, description='启动时间')
    completed_at: Optional[datetime] = Field(default=None, description='完成时间')
    duration_seconds: Optional[int] = Field(default=None, description='执行时长（秒）')
    started_at: Optional[datetime] = Field(default=None, description='启动时间')
    completed_at: Optional[datetime] = Field(default=None, description='完成时间')
    duration_seconds: Optional[int] = Field(default=None, description='执行时长（秒）')

    # 结果
    result: Optional[dict] = Field(default=None, sa_column=Column(JSON), description='执行结果')
    error_message: Optional[str] = Field(default=None, description='错误信息')
    # 创建信息（逻辑外键）
    started_by: UUID = Field(description='启动者用户ID')

    class Config:
        json_schema_extra = {

            'example': {
                'process_key': 'workspace_approval',
                'business_key': 'workspace_123',
                'business_type': 'workspace_creation',
                'status': 'waiting',
                'variables': {
                    'workspace_name': '新工作空间',
                    'applicant': '张三',
                    'reason': '项目需要',
                },
                'current_node_id': 'manager_approval',

            }
        }
