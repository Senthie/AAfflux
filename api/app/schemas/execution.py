"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-22 10:19:06
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-22 14:38:40
FilePath: : AAfflux: api: app: schemas: execution.py
Description:执行记录相关的Pydantic schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class NodeExecutionResultResponse(BaseModel):
    """节点执行结果响应"""

    id: UUID
    execution_record_id: UUID
    node_id: UUID
    status: str
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int

    class Config:
        from_attributes = True


class ExecutionRecordCreate(BaseModel):
    """创建执行记录请求"""

    workflow_id: UUID
    inputs: Dict[str, Any] = Field(default_factory=dict)


class ExecutionRecordUpdate(BaseModel):
    """更新执行记录请求"""

    outputs: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


class ExecutionRecordResponse(BaseModel):
    """执行记录响应"""

    id: UUID
    workflow_id: UUID
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]] = None
    status: str
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    node_results: List[NodeExecutionResultResponse] = []

    class Config:
        from_attributes = True


class ExecutionRecordListItem(BaseModel):
    """执行记录列表项"""

    id: UUID
    workflow_id: UUID
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


class ExecutionRecordListResponse(BaseModel):
    """执行记录列表响应"""

    items: List[ExecutionRecordListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ExecutionStatistics(BaseModel):
    """执行统计信息"""

    total_executions: int
    successful_executions: int
    failed_executions: int
    running_executions: int
    pending_executions: int
    average_duration_ms: Optional[float] = None
    success_rate: float


class ExecutionRecordQuery(BaseModel):
    """执行记录查询参数"""

    workflow_id: Optional[UUID] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
