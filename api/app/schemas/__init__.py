"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:51:53
FilePath: /api/app/schemas/__init__.py
Description: Pydantic Schemas - 请求/响应模型模块初始化

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from app.schemas.bpm_approval_schemas import (
    ApprovalRequest,
    ApprovalResponse,
)
from app.schemas.bpm_process_schemas import (
    ProcessDefinitionCreate,
    ProcessDefinitionResponse,
    ProcessInstanceCreate,
    ProcessInstanceResponse,
)
from app.schemas.bpm_task_schemas import (
    TaskClaimRequest,
    TaskCompleteRequest,
    TaskResponse,
)

__all__ = [
    'ProcessDefinitionCreate',
    'ProcessDefinitionResponse',
    'ProcessInstanceCreate',
    'ProcessInstanceResponse',
    'TaskResponse',
    'TaskCompleteRequest',
    'TaskClaimRequest',
    'ApprovalRequest',
    'ApprovalResponse',
]
