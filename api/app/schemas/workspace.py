"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-10 17:46:17
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-09 12:21:20
FilePath: /api/app/schemas/workspace.py
Description:工作空间管理相关的 Pydantic Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.tenant.organization import WorkspacePlan, WorkspaceStatus


class WorkspaceBase(BaseModel):
    """工作空间基础信息"""

    name: str = Field(min_length=1, max_length=255, description='工作空间名称')
    description: Optional[str] = Field(None, description='工作空间描述')
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description='工作空间配置')


class WorkspaceCreate(WorkspaceBase):
    """创建工作空间请求"""

    # 之前报错找不到这个类，现在明确定义在这里，保存即可解决
    team_id: UUID = Field(description='所属团队ID')


class WorkspaceUpdate(BaseModel):
    """更新工作空间请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description='工作空间名称')
    description: Optional[str] = Field(None, description='工作空间描述')
    settings: Optional[Dict[str, Any]] = Field(None, description='工作空间配置')


class WorkspaceResponse(WorkspaceBase):
    """工作空间响应"""

    id: UUID = Field(description='工作空间ID')
    name: str = Field(description='工作空间名称')
    description: str = Field(description='工作空间描述')
    created_at: datetime = Field(description='创建时间')
    updated_at: datetime = Field(description='更新时间')
    plan: WorkspacePlan = Field(description='工作空间套餐')
    status: WorkspaceStatus = Field(description='工作空间的状态')

    class Config:
        from_attributes = True


class WorkspaceResourcesResponse(BaseModel):
    """工作空间资源响应"""

    workspace_id: UUID = Field(description='工作空间ID')
    workflows: List[Dict[str, Any]] = Field(description='工作流列表')
    applications: List[Dict[str, Any]] = Field(description='应用列表')
    files: List[Dict[str, Any]] = Field(description='文件列表')


class WorkspaceResourceMove(BaseModel):
    """移动资源请求"""

    resource_id: UUID = Field(description='资源ID')
    resource_type: str = Field(description='资源类型', pattern='^(workflow|application|file)$')
    target_workspace_id: UUID = Field(description='目标工作空间ID')


class WorkspaceListResponse(BaseModel):
    """工作空间列表响应"""

    total: int = Field(description='总数')
    items: List[WorkspaceResponse] = Field(description='工作空间列表')
    limit: int = Field(description='每页数量')
    offset: int = Field(description='偏移量')


class WorkspaceDeleteResponse(BaseModel):
    """工作空间删除响应"""

    success: bool = Field(description='删除是否成功')
    message: str = Field(description='响应消息')
    workspace_id: UUID = Field(description='被删除的工作空间ID')
