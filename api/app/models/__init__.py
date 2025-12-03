"""数据模型包 - 导出所有数据库模型。

本包包含系统的所有 SQLModel 数据模型定义。
模型按业务域分组组织，便于维护和理解。

模型分层（按业务域）：
1. 基础层 (base.py) - 基础模型类和混入
2. 认证域 (auth/) - 用户、令牌、API密钥（4张表）
3. 租户域 (tenant/) - 企业、团队、工作空间、成员、邀请（5张表）
4. 工作流域 (workflow/) - DAG工作流、节点、执行（5张表）
5. 应用域 (application/) - 应用、LLM提供商、提示词（4张表）
6. 对话域 (conversation/) - 对话、消息、标注、终端用户（5张表）
7. 知识库域 (dataset/) - 知识库、文档、段落（4张表）
8. 插件域 (plugin/) - 插件系统（2张表）
9. BPM域 (bpm/) - 业务流程管理（6张表）
10. 计费域 (billing/) - 订阅和用量（2张表）
11. 文件域 (file/) - 文件引用（1张表）
12. 审计域 (audit/) - 审计日志（1张表）

总计：37张核心表（31张主业务表 + 6张BPM表）+ MongoDB文件存储
"""

# 基础模型
from app.models.base import BaseModel, TimestampMixin, UUIDMixin

# 认证域
from app.models.auth import User, RefreshToken, PasswordReset, APIKey

# 租户域
from app.models.tenant import Organization, Team, Workspace, TeamMember, TeamInvitation

# 工作流域
from app.models.workflow import (
    Workflow,
    Node,
    Connection,
    ExecutionRecord,
    NodeExecutionResult,
)

# 应用域
from app.models.application import (
    Application,
    LLMProvider,
    PromptTemplate,
    PromptTemplateVersion,
)

# 对话域
from app.models.conversation import (
    Conversation,
    Message,
    MessageAnnotation,
    MessageFeedback,
    EndUser,
)

# 知识库域
from app.models.dataset import (
    Dataset,
    Document,
    DocumentSegment,
    DatasetApplicationJoin,
)

# 插件域
from app.models.plugin import Plugin, InstalledPlugin

# BPM域
from app.models.bpm import (
    ProcessDefinition,
    ProcessInstance,
    ProcessStatus,
    Task,
    TaskStatus,
    TaskType,
    Approval,
    ApprovalAction,
    FormDefinition,
    FormData,
)

# 计费域
from app.models.billing import Subscription, UsageRecord

# 文件域
from app.models.file import FileReference

# 审计域
from app.models.audit import AuditLog

__all__ = [
    # 基础模型
    "BaseModel",
    "TimestampMixin",
    "UUIDMixin",
    # 认证域
    "User",
    "RefreshToken",
    "PasswordReset",
    "APIKey",
    # 租户域
    "Organization",
    "Team",
    "Workspace",
    "TeamMember",
    "TeamInvitation",
    # 工作流域
    "Workflow",
    "Node",
    "Connection",
    "ExecutionRecord",
    "NodeExecutionResult",
    # 应用域
    "Application",
    "LLMProvider",
    "PromptTemplate",
    "PromptTemplateVersion",
    # 对话域
    "Conversation",
    "Message",
    "MessageAnnotation",
    "MessageFeedback",
    "EndUser",
    # 知识库域
    "Dataset",
    "Document",
    "DocumentSegment",
    "DatasetApplicationJoin",
    # 插件域
    "Plugin",
    "InstalledPlugin",
    # BPM域
    "ProcessDefinition",
    "ProcessInstance",
    "ProcessStatus",
    "Task",
    "TaskStatus",
    "TaskType",
    "Approval",
    "ApprovalAction",
    "FormDefinition",
    "FormData",
    # 计费域
    "Subscription",
    "UsageRecord",
    # 文件域
    "FileReference",
    # 审计域
    "AuditLog",
]


def get_file_service():
    """Lazy import file service to avoid config dependency."""
    from app.models.file import get_file_service as _get_file_service
    return _get_file_service()
