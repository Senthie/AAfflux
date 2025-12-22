"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-22 10:27:51
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-22 14:25:18
FilePath: : AAfflux: api: app: schemas: application.py
Description:应用相关的Pydantic schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    """创建应用请求"""
    name: str = Field(..., min_length=1, max_length=255, description="应用名称")
    description: Optional[str] = Field(None, max_length=1000, description="应用描述")
    workflow_id: UUID = Field(..., description="关联的工作流ID")
    config: Dict[str, Any] = Field(default_factory=dict, description="应用配置")


class ApplicationUpdate(BaseModel):
    """更新应用请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="应用名称")
    description: Optional[str] = Field(None, max_length=1000, description="应用描述")
    workflow_id: Optional[UUID] = Field(None, description="关联的工作流ID")
    config: Optional[Dict[str, Any]] = Field(None, description="应用配置")
    is_published: Optional[bool] = Field(None, description="是否发布")


class ApplicationResponse(BaseModel):
    """应用响应"""
    id: UUID
    name: str
    description: Optional[str] = None
    workflow_id: UUID
    config: Dict[str, Any]
    is_published: bool
    api_endpoint: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationListItem(BaseModel):
    """应用列表项"""
    id: UUID
    name: str
    description: Optional[str] = None
    workflow_id: UUID
    is_published: bool
    api_endpoint: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    """应用列表响应"""
    items: List[ApplicationListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class APIKeyCreate(BaseModel):
    """创建API密钥请求"""
    name: str = Field(..., min_length=1, max_length=255, description="密钥名称")
    expires_in_days: Optional[int] = Field(None, ge=1, le=3650, description="过期天数")


class APIKeyResponse(BaseModel):
    """API密钥响应"""
    id: UUID
    name: str
    key_prefix: str  # 只显示前缀，不显示完整密钥
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    """创建API密钥响应（包含完整密钥）"""
    id: UUID
    name: str
    api_key: str  # 完整密钥，只在创建时返回
    key_prefix: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """API密钥列表响应"""
    items: List[APIKeyResponse]
    total: int


class ApplicationPublishRequest(BaseModel):
    """应用发布请求"""
    is_published: bool = Field(..., description="是否发布")


class ApplicationRuntimeRequest(BaseModel):
    """应用运行时请求"""
    inputs: Dict[str, Any] = Field(default_factory=dict, description="输入参数")


class ApplicationRuntimeResponse(BaseModel):
    """应用运行时响应"""
    execution_id: UUID
    outputs: Optional[Dict[str, Any]] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class ApplicationQuery(BaseModel):
    """应用查询参数"""
    name: Optional[str] = None
    is_published: Optional[bool] = None
    workflow_id: Optional[UUID] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
