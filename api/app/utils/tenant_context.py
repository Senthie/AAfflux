"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:57:35
FilePath: /api/app/utils/tenant_context.py
Description: Tenant Context工具

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.tenant.organization import Team, TeamMember, Workspace
from app.utils.rbac import Permission, Role


@dataclass
class TenantContext:
    """租户上下文信息"""

    user_id: UUID
    workspace_id: UUID
    team_id: UUID
    organization_id: Optional[UUID]
    role: Role

    def __post_init__(self):
        """验证上下文有效性"""
        pass


class TenantContextManager:
    """租户上下文管理器"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_context(self, user_id: UUID, workspace_id: UUID) -> Optional[TenantContext]:
        """获取用户在指定工作空间的上下文"""
        # 1. 查询工作空间信息
        workspace = await self.session.get(Workspace, workspace_id)
        if not workspace:
            return None

        # 2. 查询用户在团队中的角色
        team_member = await self.session.execute(
            select(TeamMember).where(
                TeamMember.team_id == workspace.team_id, TeamMember.user_id == user_id
            )
        )
        member = team_member.scalar_one_or_none()
        if not member:
            return None

        # 3. 查询团队和企业信息
        team = await self.session.get(Team, workspace.team_id)

        return TenantContext(
            user_id=user_id,
            workspace_id=workspace_id,
            team_id=workspace.team_id,
            organization_id=team.organization_id if team else None,
            role=Role(member.role),
        )

    async def verify_access(self, user_id: UUID, workspace_id: UUID) -> bool:
        """验证用户是否有权访问工作空间"""
        context = await self.get_user_context(user_id, workspace_id)
        return context is not None

    async def get_user_workspaces(self, user_id: UUID) -> List[UUID]:
        """获取用户有权访问的所有工作空间"""
        workspace_ids = []

        # 1. 查询用户所在的所有团队
        team_members = await self.session.execute(
            select(TeamMember).where(
                TeamMember.user_id == user_id, TeamMember.is_deleted.is_(False)
            )
        )
        team_member_list = team_members.scalars().all()

        # 2. 获取所有团队ID
        team_ids = [member.team_id for member in team_member_list]

        if not team_ids:
            return workspace_ids

        # 3. 查询这些团队下的所有工作空间
        workspaces = await self.session.execute(
            select(Workspace).where(
                Workspace.team_id.in_(team_ids), Workspace.is_deleted.is_(False)
            )
        )
        workspace_list = workspaces.scalars().all()

        # 4. 收集工作空间ID
        workspace_ids = [workspace.id for workspace in workspace_list]

        return workspace_ids

    async def get_user_workspaces_with_roles(self, user_id: UUID) -> Dict[UUID, Role]:
        """获取用户在各个工作空间的角色映射"""
        workspace_roles = {}

        # 查询用户的团队成员关系
        team_members = await self.session.execute(
            select(TeamMember, Workspace)
            .join(Workspace, TeamMember.team_id == Workspace.team_id)
            .where(
                TeamMember.user_id == user_id,
                TeamMember.is_deleted.is_(False),
                Workspace.is_deleted.is_(False),
            )
        )

        results = team_members.all()

        for team_member, workspace in results:
            workspace_roles[workspace.id] = Role(team_member.role)

        return workspace_roles

    async def check_workspace_access(
        self, user_id: UUID, workspace_id: UUID, required_permission: Permission
    ) -> bool:
        """检查用户是否有权限访问指定工作空间的特定操作"""
        context = await self.get_user_context(user_id, workspace_id)

        if not context:
            return False

        # 使用RBAC检查权限
        from app.utils.rbac import has_permission

        return has_permission(context.role, required_permission)
