"""工作流模型 - 5张表。

本模块定义了DAG工作流相关的数据模型：
1. Workflow - 工作流表
2. Node - 节点表
3. Connection - 连接表
4. ExecutionRecord - 执行记录表
5. NodeExecutionResult - 节点执行结果表

工作流是系统的核心功能，支持可视化的DAG编排。
"""

from datetime import datetime
from uuid import UUID
from typing import Optional, List
from sqlmodel import Field, Column, Relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import BaseModel, TimestampMixin, WorkspaceMixin, AuditMixin, SoftDeleteMixin


class Workflow(BaseModel, TimestampMixin, AuditMixin, WorkspaceMixin, SoftDeleteMixin, table=True):
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

    __tablename__ = 'workflows'

    name: str = Field(max_length=255, index=True)
    description: Optional[str] = None
    input_schema: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    output_schema: dict = Field(default_factory=dict, sa_column=Column(JSONB))


class Node(BaseModel, table=True):
    """节点表 - 工作流中的处理节点。

    定义工作流中的各个处理单元，包括类型、配置和位置信息。
    节点类型包括：LLM、CONDITION、CODE、HTTP、TRANSFORM等。

    Attributes:
    已经继承
        id: 节点唯一标识符（UUID）

        workflow_id: 所属工作流ID（逻辑外键）
        type: 节点类型（LLM/CONDITION/CODE/HTTP/TRANSFORM）
        name: 节点名称
        config: 节点配置（JSONB格式）
        position: 节点位置坐标（JSONB格式，包含x和y）
    """

    __tablename__ = 'nodes'

    workflow_id: UUID = Field(index=True)  # Logical FK to workflows
    type: str = Field(max_length=50)  # LLM, CONDITION, CODE, HTTP, TRANSFORM
    name: str = Field(max_length=255)
    config: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    position: dict = Field(default_factory=dict, sa_column=Column(JSONB))  # {x, y}


class Connection(BaseModel, table=True):
    """连接表 - 节点之间的连接关系。

    定义工作流中节点之间的数据流向。
    连接指定了源节点的输出如何传递到目标节点的输入。

    Attributes:
    已经继承
        id: 连接唯一标识符（UUID）

        workflow_id: 所属工作流ID（逻辑外键）
        source_node_id: 源节点ID（逻辑外键）
        target_node_id: 目标节点ID（逻辑外键）
        source_output: 源节点的输出端口名称
        target_input: 目标节点的输入端口名称
    """

    __tablename__ = 'connections'

    workflow_id: UUID = Field(index=True)  # Logical FK to workflows
    source_node_id: UUID = Field(index=True)  # Logical FK to nodes
    target_node_id: UUID = Field(index=True)  # Logical FK to nodes
    source_output: str = Field(max_length=255)
    target_input: str = Field(max_length=255)


class ExecutionRecord(BaseModel, table=True):
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

    __tablename__ = 'execution_records'

    workflow_id: UUID = Field(index=True)  # Logical FK to workflows
    inputs: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    outputs: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    status: str = Field(max_length=20, index=True)  # PENDING, RUNNING, SUCCESS, FAILED
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # Relationships
    node_results: List['NodeExecutionResult'] = Relationship(
        back_populates='execution_record',
        sa_relationship_kwargs={
            'primaryjoin': 'ExecutionRecord.id == foreign(NodeExecutionResult.execution_record_id)'
        },
    )


class NodeExecutionResult(BaseModel, table=True):
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

    __tablename__ = 'node_execution_results'

    execution_record_id: UUID = Field(index=True)  # Logical FK to execution_records
    node_id: UUID = Field(index=True)  # Logical FK to nodes
    status: str = Field(max_length=20)
    inputs: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    outputs: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    error: Optional[str] = None
    duration_ms: int

    # Relationships
    execution_record: Optional[ExecutionRecord] = Relationship(
        back_populates='node_results',
        sa_relationship_kwargs={
            'primaryjoin': 'foreign(NodeExecutionResult.execution_record_id) == ExecutionRecord.id'
        },
    )
