"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-10 17:46:00
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-11 10:10:01
FilePath: : AAfflux: api: app: schemas: team.py
Description:团队管理相关的 Pydantic Schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr

from app.utils.rbac import Role


class TeamBase(BaseModel):
    """团队基础信息"""

    name: str = Field(min_length=1, max_length=255, description='团队名称')
    description: Optional[str] = Field(None, description='团队描述')
    settings: Optional[dict] = Field(default_factory=dict, description='团队配置')


class TeamCreate(TeamBase):
    """创建团队请求"""

    organization_id: Optional[UUID] = Field(None, description='所属企业ID')


class TeamUpdate(BaseModel):
    """更新团队请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description='团队名称')
    description: Optional[str] = Field(None, description='团队描述')
    settings: Optional[dict] = Field(None, description='团队配置')


class TeamResponse(TeamBase):
    """团队响应"""

    id: UUID = Field(description='团队ID')
    organization_id: Optional[UUID] = Field(description='所属企业ID')
    created_by: UUID = Field(description='创建者ID')
    created_at: datetime = Field(description='创建时间')
    updated_at: datetime = Field(description='更新时间')

    class Config:
        from_attributes = True


class TeamMemberResponse(BaseModel):
    """团队成员响应"""

    id: UUID = Field(description='成员记录ID')
    team_id: UUID = Field(description='团队ID')
    user_id: UUID = Field(description='用户ID')
    role: str = Field(description='角色')
    joined_at: datetime = Field(description='加入时间')

    class Config:
        from_attributes = True


class TeamMemberCreate(BaseModel):
    """添加团队成员请求"""

    user_id: UUID = Field(description='用户ID')
    role: str = Field(default=Role.MEMBER.value, description='角色')


class TeamMemberUpdate(BaseModel):
    """更新团队成员请求"""

    role: str = Field(description='新角色')


class TeamInvitationCreate(BaseModel):
    """发送团队邀请请求"""

    email: EmailStr = Field(description='邀请邮箱')
    role: str = Field(default=Role.MEMBER.value, description='邀请角色')


class TeamInvitationResponse(BaseModel):
    """团队邀请响应"""

    id: UUID = Field(description='邀请ID')
    team_id: UUID = Field(description='团队ID')
    email: str = Field(description='邀请邮箱')
    role: str = Field(description='邀请角色')
    token: str = Field(description='邀请令牌')
    status: str = Field(description='邀请状态')
    invited_by: UUID = Field(description='邀请人ID')
    expires_at: datetime = Field(description='过期时间')
    created_at: datetime = Field(description='创建时间')

    class Config:
        from_attributes = True


class TeamInvitationAccept(BaseModel):
    """接受团队邀请请求"""

    token: str = Field(description='邀请令牌')


class TeamListResponse(BaseModel):
    """团队列表响应"""

    total: int = Field(description='总数')
    items: list[TeamResponse] = Field(description='团队列表')
    limit: int = Field(description='每页数量')
    offset: int = Field(description='偏移量')
