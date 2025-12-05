"""对话模型 - 2张表。

本模块定义了对话和消息的数据模型。
支持终端用户与AI应用的多轮对话。
"""

from uuid import UUID
from typing import Optional
from sqlmodel import Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import BaseModel, TimestampMixin, WorkspaceMixin


class Conversation(BaseModel, WorkspaceMixin, TimestampMixin, table=True):
    """对话表 - 会话管理。

    存储终端用户与AI应用的对话会话。
    每个对话包含多条消息，形成完整的对话历史。

    Attributes:
    已经继承
        id: 对话唯一标识符（UUID）
        workspace_id: 所属工作空间ID（逻辑外键，租户隔离）
        created_at: 创建时间
        updated_at: 最后更新时间

        application_id: 关联的应用ID（逻辑外键）
        end_user_id: 终端用户ID（逻辑外键）
        title: 对话标题（自动生成或用户设置）
        status: 对话状态（active-活跃/archived-已归档/deleted-已删除）
        summary: 对话摘要（可选）
        message_count: 消息数量
        metadata: 自定义元数据（JSONB格式）

         测试查看插件是否使用
    业务规则：
        - 每个对话属于一个终端用户和一个应用
        - 对话标题可以自动从第一条消息生成
        - 支持对话归档和删除
        - 记录消息数量用于统计和限制
    """

    __tablename__ = 'conversations'
    application_id: UUID = Field(index=True)  # Logical FK to applications
    end_user_id: UUID = Field(index=True)  # Logical FK to end_users
    title: str = Field(max_length=500)
    status: str = Field(max_length=20, index=True, default='active')  # active, archived, deleted
    summary: Optional[str] = None
    message_count: int = Field(default=0)
    custom_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSONB))


class Message(BaseModel, TimestampMixin, table=True):
    """消息表 - 对话消息。

    存储对话中的每条消息，包括用户输入和AI回复。
    记录完整的消息内容、Token使用和执行信息。

    Attributes:
       已经继承
        id: 对话唯一标识符（UUID）
        created_at: 创建时间


        conversation_id: 所属对话ID（逻辑外键）
        application_id: 关联的应用ID（逻辑外键）
        workflow_run_id: 工作流执行ID（逻辑外键，可选）
        role: 消息角色（user-用户/assistant-助手/system-系统）
        content: 消息内容
        query: 用户查询（如果是用户消息）
        answer: AI回答（如果是助手消息）
        inputs: 输入参数（JSONB格式）
        outputs: 输出结果（JSONB格式）
        model_provider: 使用的模型提供商
        model_name: 使用的模型名称
        prompt_tokens: 提示词Token数
        completion_tokens: 完成Token数
        total_tokens: 总Token数
        latency: 响应延迟（秒）
        status: 消息状态（success-成功/failed-失败/processing-处理中）
        error: 错误信息（如果失败）
        metadata: 自定义元数据（JSONB格式）


    业务规则：
        - 消息按时间顺序排列形成对话
        - 记录Token使用用于计费和统计
        - 支持关联到工作流执行记录
        - 记录模型信息用于追踪和分析
    """

    __tablename__ = 'messages'

    conversation_id: UUID = Field(index=True)  # Logical FK to conversations
    application_id: UUID = Field(index=True)  # Logical FK to applications
    workflow_run_id: Optional[UUID] = Field(
        default=None, index=True
    )  # Logical FK to execution_records
    role: str = Field(max_length=20, index=True)  # user, assistant, system
    content: str
    query: Optional[str] = None
    answer: Optional[str] = None
    inputs: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    outputs: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    model_provider: Optional[str] = Field(default=None, max_length=100)
    model_name: Optional[str] = Field(default=None, max_length=100)
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    latency: float = Field(default=0.0)
    status: str = Field(max_length=20, index=True, default='success')  # success, failed, processing
    error: Optional[str] = None
    custom_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
