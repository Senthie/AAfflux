"""Pydantic Schemas - 请求/响应模型"""

from app.schemas.bpm_process_schemas import (
    ProcessDefinitionCreate,
    ProcessDefinitionResponse,
    ProcessInstanceCreate,
    ProcessInstanceResponse,
)
from app.schemas.bpm_task_schemas import (
    TaskResponse,
    TaskCompleteRequest,
    TaskClaimRequest,
)
from app.schemas.bpm_approval_schemas import (
    ApprovalRequest,
    ApprovalResponse,
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
