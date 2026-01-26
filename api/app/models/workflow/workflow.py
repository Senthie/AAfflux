"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-24 16:24:52
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-26 11:51:40
FilePath: /api/app/models/workflow/workflow.py
Description:工作流模型 - 5张表。
    本模块定义了DAG工作流相关的数据模型：
    1. Workflow - 工作流表
    2. Node - 节点表
    3. Connection - 连接表
    4. ExecutionRecord - 执行记录表
    5. NodeExecutionResult - 节点执行结果表

    工作流是系统的核心功能，支持可视化的DAG编排。

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship

from app.models.base import AuditMixin, BaseModel, SoftDeleteMixin, TimestampMixin, WorkspaceMixin


class NodeModel(PydanticBaseModel):
    """节点数据结构"""

    id: UUID  # 字符串ID，便于前端使用
    plugin_id: UUID
    type: str  # NodeTypeEnum as string to avoid circular import
    config: Dict[str, Any]
    ui: Dict[str, Any]  # {x, y, width, height, ...}


class ConnectionModel(PydanticBaseModel):
    """
    连接数据结构
    :param {str} id `source_node_id`_to_`target_node_id`
        as 2a9919a2-547f-471c-a03f-c02294a1256c_to_e1668919-79bf-40e8-bdcf-788661689265
    """

    id: str
    source_node_id: str
    target_node_id: str


class GraphModel(PydanticBaseModel):
    """工作流完整数据"""

    nodes: List[NodeModel]
    connections: List[ConnectionModel]


class WorkflowModel(
    BaseModel,
    TimestampMixin,
    AuditMixin,
    WorkspaceMixin,
    SoftDeleteMixin,
    table=True,  # type: ignore
):
    """工作流表 - DAG工作流定义。

    存储工作流的基本信息和输入输出schema。
    工作流由多个节点和连接组成，形成有向无环图（DAG）。

    Attributes:
    已经继承
        id: 工作流唯一标识符（UUID）
        workspace_id: 所属工作空间ID（逻辑外键，租户隔离字段）
        created_at: 创建时间
        updated_at: 最后更新时间
        deleted_at: Optional[datetime] = Field(default=None)
        is_deleted: bool = Field(default=False)

        name: 工作流名称
        description: 工作流描述
        input_schema: 输入参数schema（JSONB格式）
        output_schema: 输出结果schema（JSONB格式）
    """

    __tablename__ = 'workflows'  # type: ignore
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = None
    input_schema: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    output_schema: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    # 存储完整的节点和连接数据
    graph: dict = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))
    # 乐观锁版本
    version: int = Field(default=1, sa_column_kwargs={'server_default': '1'})
    # 数据hash，用于快速检测变更
    data_hash: str = Field(max_length=64, nullable=True)

    # ========== 索引配置 ==========
    # Note: Removed invalid postgresql_ops configuration


class ExecutionRecordModel(BaseModel, table=True):  # type: ignore
    """执行记录表 - 工作流执行历史。

    记录工作流的每次执行，包括输入、输出、状态和耗时。
    用于调试、审计和性能分析。

    Attributes:
    已经继承
        id: 执行记录唯一标识符（UUID）

        workflow_id: 工作流ID（逻辑外键）
        inputs: 输入参数（JSONB格式）
        outputs: 输出结果（JSONB格式）
        status: 执行状态（PENDING/RUNNING/SUCCESS/FAILED）
        error: 错误信息（如果失败）
        started_at: 开始时间
        completed_at: 完成时间
        duration_ms: 执行耗时（毫秒）
    """

    __tablename__ = 'execution_records'  # type: ignore

    workflow_id: UUID = Field(index=True)  # Logical FK to workflows
    inputs: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    outputs: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    status: str = Field(max_length=20, index=True)  # PENDING, RUNNING, SUCCESS, FAILED
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # Relationships
    node_results: List['NodeExecutionResultModel'] = Relationship(
        back_populates='execution_record',
        sa_relationship_kwargs={
            'primaryjoin': 'ExecutionRecordModel.id == foreign(NodeExecutionResultModel.execution_record_id)'
        },
    )


class NodeExecutionResultModel(BaseModel, table=True):  # type: ignore
    """节点执行结果表 - 单个节点的执行记录。

    记录工作流执行过程中每个节点的执行情况。
    包括输入、输出、状态和耗时，用于详细的执行追踪。

    Attributes:
    已经继承
        id: 节点执行结果唯一标识符（UUID）

        execution_record_id: 所属执行记录ID（逻辑外键）
        node_id: 节点ID（逻辑外键）
        status: 执行状态
        inputs: 输入数据（JSONB格式）
        outputs: 输出数据（JSONB格式）
        error: 错误信息（如果失败）
        duration_ms: 执行耗时（毫秒）
    """

    __tablename__ = 'node_execution_results'  # type: ignore

    execution_record_id: UUID = Field(index=True)  # Logical FK to execution_records
    node_id: str = Field(index=True)  # Logical FK to nodes (now string ID)
    status: str = Field(max_length=20)
    inputs: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    outputs: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    error: Optional[str] = None
    duration_ms: int

    # Relationships
    execution_record: Optional[ExecutionRecordModel] = Relationship(
        back_populates='node_results',
        sa_relationship_kwargs={
            'primaryjoin': 'foreign(NodeExecutionResultModel.execution_record_id) == ExecutionRecordModel.id'
        },
    )
