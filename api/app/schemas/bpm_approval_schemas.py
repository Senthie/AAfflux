"""审批相关 Schemas"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ApprovalRequest(BaseModel):
    """审批请求"""

    action: str = Field(..., description="审批动作: approve/reject")
    comment: Optional[str] = Field(None, description="审批意见")


class ApprovalResponse(BaseModel):
    """审批响应"""

    id: UUID
    task_id: UUID
    approver_id: UUID
    approver_name: str
    action: str
    comment: Optional[str]
    approved_at: datetime
