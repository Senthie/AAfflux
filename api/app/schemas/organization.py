"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-10 17:45:47
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-11 15:15:49
FilePath: : AAfflux: api: app: schemas: organization.py
Description:企业管理相关的 Pydantic Schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class OrganizationBase(BaseModel):
    """企业基础信息"""

    name: str = Field(min_length=1, max_length=255, description='企业名称')
    description: Optional[str] = Field(None, description='企业描述')
    settings: Optional[dict] = Field(default_factory=dict, description='企业配置')


class OrganizationCreate(OrganizationBase):
    """创建企业请求"""

    pass


class OrganizationUpdate(BaseModel):
    """更新企业请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description='企业名称')
    description: Optional[str] = Field(None, description='企业描述')
    settings: Optional[dict] = Field(None, description='企业配置')


class OrganizationResponse(OrganizationBase):
    """企业响应"""

    id: UUID = Field(description='企业ID')
    created_by: UUID = Field(description='创建者ID')
    created_at: datetime = Field(description='创建时间')
    updated_at: datetime = Field(description='更新时间')

    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    """企业列表响应"""

    total: int = Field(description='总数')
    items: list[OrganizationResponse] = Field(description='企业列表')
    limit: int = Field(description='每页数量')
    offset: int = Field(description='偏移量')


class OrganizationStatsResponse(BaseModel):
    """企业统计响应"""

    organization_id: UUID = Field(description='企业ID')
    team_count: int = Field(description='团队数量')
    workspace_count: int = Field(description='工作空间数量')
    member_count: int = Field(description='成员数量')
    workflow_count: int = Field(description='工作流数量')
    application_count: int = Field(description='应用数量')
