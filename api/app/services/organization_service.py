"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-10 16:44:17
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-11 12:15:44
FilePath: : AAfflux: api: app: services: organization_service.py
Description:企业服务管理
"""

from typing import List, Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.tenant.organization import Organization, Team, Workspace
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


class OrganizationService:
    """企业管理服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_organization(self, data: OrganizationCreate, creator_id: UUID) -> Organization:
        """创建企业"""
        organization = Organization(
            name=data.name,
            description=data.description,
            settings=data.settings or {},
            created_by=creator_id,
        )

        self.session.add(organization)
        await self.session.commit()
        await self.session.refresh(organization)

        return organization

    async def get_organization(self, org_id: UUID) -> Optional[Organization]:
        """获取企业信息"""
        return await self.session.get(Organization, org_id)

    async def update_organization(
        self, org_id: UUID, data: OrganizationUpdate
    ) -> Optional[Organization]:
        """更新企业信息"""
        organization = await self.session.get(Organization, org_id)
        if not organization:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(organization, field, value)

        await self.session.commit()
        await self.session.refresh(organization)

        return organization

    async def delete_organization(self, org_id: UUID) -> bool:
        """删除企业（级联删除团队和工作空间）"""
        organization = await self.session.get(Organization, org_id)
        if not organization:
            return False

        # 软删除企业
        organization.soft_delete()

        # 级联软删除所有团队
        teams = await self.session.execute(select(Team).where(Team.organization_id == org_id))
        for team in teams.scalars():
            team.soft_delete()

        await self.session.commit()
        return True

    async def get_organization_teams(self, org_id: UUID) -> List[Team]:
        """获取企业下的所有团队"""
        result = await self.session.execute(
            select(Team).where(Team.organization_id == org_id, Team.is_deleted.is_(False))
        )
        return list(result.scalars().all())

    async def get_usage_stats(self, org_id: UUID) -> dict:
        """获取企业使用统计"""
        from sqlmodel import func

        from app.models.application.application import Application
        from app.models.tenant.organization import TeamMember
        from app.models.workflow.workflow import WorkflowModel

        # 统计团队数量
        team_count = await self.session.scalar(
            select(func.count(Team.id)).where(
                Team.organization_id == org_id, Team.is_deleted.is_(False)
            )
        )

        # 统计工作空间数量
        workspace_count = await self.session.scalar(
            select(func.count(Workspace.id))
            .select_from(Team)
            .join(Workspace, Team.id == Workspace.team_id)
            .where(
                Team.organization_id == org_id,
                Team.is_deleted.is_(False),
                Workspace.is_deleted.is_(False),
            )
        )

        # 统计成员数量（去重）
        member_count = await self.session.scalar(
            select(func.count(func.distinct(TeamMember.user_id)))
            .select_from(Team)
            .join(TeamMember, Team.id == TeamMember.team_id)
            .where(Team.organization_id == org_id, Team.is_deleted.is_(False))
        )

        # 统计工作流数量
        workflow_count = await self.session.scalar(
            select(func.count(WorkflowModel.id))
            .select_from(Team)
            .join(Workspace, Team.id == Workspace.team_id)
            .join(WorkflowModel, Workspace.id == WorkflowModel.workspace_id)
            .where(
                Team.organization_id == org_id,
                Team.is_deleted.is_(False),
                Workspace.is_deleted.is_(False),
                WorkflowModel.is_deleted.is_(False),
            )
        )

        # 统计应用数量
        application_count = await self.session.scalar(
            select(func.count(Application.id))
            .select_from(Team)
            .join(Workspace, Team.id == Workspace.team_id)
            .join(Application, Workspace.id == Application.workspace_id)
            .where(
                Team.organization_id == org_id,
                Team.is_deleted.is_(False),
                Workspace.is_deleted.is_(False),
                Application.is_deleted.is_(False),
            )
        )

        return {
            'team_count': team_count or 0,
            'workspace_count': workspace_count or 0,
            'member_count': member_count or 0,
            'workflow_count': workflow_count or 0,
            'application_count': application_count or 0,
        }
