"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:52:18
FilePath: /api/app/schemas/bpm_task_schemas.py
Description: Bpm Task Schemas数据模式

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

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

    result: dict = Field(..., description='任务结果')
    comment: Optional[str] = Field(None, description='处理意见')
