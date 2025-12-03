"""审批记录模型"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ApprovalAction(str, Enum):
    """审批动作"""
    APPROVE = "approve"       # 同意
    REJECT = "reject"         # 拒绝
    TRANSFER = "transfer"     # 转交
    DELEGATE = "delegate"     # 委托
    RETURN = "return"         # 退回


class Approval(SQLModel, table=True):
    """审批记录表 - 记录每次审批操作"""

    __tablename__ = "bpm_approvals"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # 关联任务
    task_id: UUID = Field(foreign_key="bpm_tasks.id", index=True)
    process_instance_id: UUID = Field(foreign_key="bpm_process_instances.id", index=True)
    
    # 审批人
    approver_id: UUID = Field(foreign_key="users.id", index=True, description="审批人")
    approver_name: str = Field(max_length=255, description="审批人姓名（冗余）")
    
    # 审批动作
    action: ApprovalAction = Field(description="审批动作")
    
    # 审批意见
    comment: Optional[str] = Field(default=None, description="审批意见")
    
    # 附件
    attachments: list = Field(default_factory=list, description="附件列表")
    
    # 转交/委托信息
    transfer_to: Optional[UUID] = Field(default=None, foreign_key="users.id", description="转交给")
    transfer_reason: Optional[str] = Field(default=None, description="转交原因")
    
    # 签名
    signature: Optional[str] = Field(default=None, description="电子签名")
    
    # IP 和设备信息
    ip_address: Optional[str] = Field(default=None, max_length=50, description="IP地址")
    user_agent: Optional[str] = Field(default=None, description="用户代理")
    
    # 时间
    approved_at: datetime = Field(default_factory=datetime.utcnow, description="审批时间")
    
    # 租户隔离
    workspace_id: UUID = Field(foreign_key="workspaces.id", index=True)

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_uuid",
                "approver_id": "user_uuid",
                "approver_name": "张三",
                "action": "approve",
                "comment": "同意创建工作空间",
                "approved_at": "2024-12-02T10:30:00Z"
            }
        }
