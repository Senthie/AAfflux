"""流程相关 Schemas"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProcessDefinitionCreate(BaseModel):
    """创建流程定义"""

    key: str = Field(..., description="流程唯一标识")
    name: str = Field(..., description="流程名称")
    description: Optional[str] = None
    category: Optional[str] = None
    nodes: list = Field(default_factory=list, description="流程节点")
    form_schema: Optional[dict] = None


class ProcessDefinitionResponse(BaseModel):
    """流程定义响应"""

    id: UUID
    key: str
    name: str
    description: Optional[str]
    version: int
    is_active: bool
    created_at: datetime


class ProcessInstanceCreate(BaseModel):
    """启动流程实例"""

    process_key: str = Field(..., description="流程标识")
    business_key: Optional[str] = Field(None, description="业务键")
    business_type: Optional[str] = None
    variables: dict = Field(default_factory=dict, description="流程变量")


class ProcessInstanceResponse(BaseModel):
    """流程实例响应"""

    id: UUID
    process_key: str
    business_key: Optional[str]
    status: str
    current_node_id: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
