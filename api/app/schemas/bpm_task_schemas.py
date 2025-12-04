"""任务相关 Schemas"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TaskResponse(BaseModel):
    """任务响应"""

    id: UUID
    task_name: str
    task_type: str
    description: Optional[str]
    status: str
    priority: int
    assignee: Optional[UUID]
    due_date: Optional[datetime]
    created_at: datetime


class TaskClaimRequest(BaseModel):
    """认领任务请求"""

    pass  # 用户ID从认证信息获取


class TaskCompleteRequest(BaseModel):
    """完成任务请求"""

    result: dict = Field(..., description="任务结果")
    comment: Optional[str] = Field(None, description="处理意见")
