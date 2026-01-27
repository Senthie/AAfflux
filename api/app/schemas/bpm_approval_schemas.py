"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/schemas/bpm_approval_schemas.py
Description: Bpm Approval Schemas数据模式

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ApprovalRequest(BaseModel):
    """审批请求"""

    action: str = Field(..., description='审批动作: approve/reject')
    comment: Optional[str] = Field(None, description='审批意见')


class ApprovalResponse(BaseModel):
    """审批响应"""

    id: UUID
    task_id: UUID
    approver_id: UUID
    approver_name: str
    action: str
    comment: Optional[str]
    approved_at: datetime
