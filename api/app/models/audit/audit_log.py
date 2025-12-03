"""审计日志模型 - 1张表。

本模块定义了审计日志的数据模型。
记录系统中的所有重要操作，用于安全审计和问题追踪。
"""

from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class AuditLog(SQLModel, table=True):
    """审计日志表 - 记录系统操作日志。
    
    记录用户在系统中的所有重要操作，包括创建、更新、删除等。
    用于安全审计、问题追踪和合规要求。
    
    Attributes:
        id: 日志记录唯一标识符（UUID）
        user_id: 操作用户ID（逻辑外键，可选，支持系统操作）
        workspace_id: 工作空间ID（逻辑外键，可选）
        action: 操作类型（CREATE/UPDATE/DELETE/EXECUTE/LOGIN/LOGOUT等）
        resource_type: 资源类型（WORKFLOW/APPLICATION/USER/TEAM等）
        resource_id: 资源ID（逻辑外键，可选）
        details: 操作详情（JSONB格式，包含操作前后的数据）
        ip_address: 客户端IP地址
        user_agent: 客户端User-Agent
        status: 操作状态（SUCCESS/FAILED）
        error_message: 错误信息（如果操作失败）
        created_at: 创建时间
    
    业务规则：
        - 所有重要操作都应记录审计日志
        - 日志只能创建，不能修改或删除
        - 定期归档旧日志以控制表大小
        - 支持按时间范围、用户、资源类型等维度查询
    """
    __tablename__ = "audit_logs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, index=True)  # Logical FK to users
    workspace_id: Optional[UUID] = Field(default=None, index=True)  # Logical FK to workspaces
    action: str = Field(max_length=100, index=True)  # CREATE, UPDATE, DELETE, EXECUTE, LOGIN, LOGOUT
    resource_type: str = Field(max_length=50, index=True)  # WORKFLOW, APPLICATION, USER, TEAM, etc.
    resource_id: Optional[UUID] = Field(default=None, index=True)
    details: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    ip_address: Optional[str] = Field(default=None, max_length=50)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    status: str = Field(max_length=20, index=True, default="SUCCESS")  # SUCCESS, FAILED
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
