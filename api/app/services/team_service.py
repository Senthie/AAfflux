"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-10 14:41:10
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-11 16:34:53
FilePath: : AAfflux: api: app: services: team_service.py
Description:团队管理服务
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.tenant.organization import Team, TeamMember
from app.models.tenant.invitation import TeamInvitation
from app.schemas.team import TeamCreate
from app.utils.rbac import Role


class TeamService:
    """团队管理服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_team(self, data: TeamCreate, creator_id: UUID) -> Team:
        """创建团队"""
        team = Team(
            name=data.name,
            organization_id=data.organization_id,
            description=data.description,
            settings=data.settings or {},
            created_by=creator_id,
        )

        self.session.add(team)
        await self.session.flush()  # 获取 team.id

        # 创建者自动成为团队管理员
        team_member = TeamMember(
            team_id=team.id, user_id=creator_id, role=Role.ADMIN.value, joined_at=datetime.utcnow()
        )

        self.session.add(team_member)
        await self.session.commit()
        await self.session.refresh(team)

        return team

    async def add_member(
        self, team_id: UUID, user_id: UUID, role: str = Role.MEMBER.value
    ) -> TeamMember:
        """添加团队成员"""
        # 检查是否已经是成员
        existing = await self.session.execute(
            select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        )

        if existing.scalar_one_or_none():
            raise ValueError('User is already a team member')

        member = TeamMember(
            team_id=team_id, user_id=user_id, role=role, joined_at=datetime.utcnow()
        )

        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)

        return member

    async def remove_member(self, team_id: UUID, user_id: UUID) -> bool:
        """移除团队成员"""
        member = await self.session.execute(
            select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        )

        member_obj = member.scalar_one_or_none()
        if not member_obj:
            return False

        await self.session.delete(member_obj)
        await self.session.commit()

        return True

    async def update_member_role(
        self, team_id: UUID, user_id: UUID, new_role: str
    ) -> Optional[TeamMember]:
        """更新成员角色"""
        member = await self.session.execute(
            select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        )

        member_obj = member.scalar_one_or_none()
        if not member_obj:
            return None

        member_obj.role = new_role
        await self.session.commit()
        await self.session.refresh(member_obj)

        return member_obj

    async def send_invitation(
        self, team_id: UUID, email: str, role: str, invited_by: UUID
    ) -> TeamInvitation:
        """发送团队邀请"""
        import secrets

        # 生成邀请令牌
        token = secrets.token_urlsafe(32)

        invitation = TeamInvitation(
            team_id=team_id,
            email=email,
            role=role,
            token=token,
            invited_by=invited_by,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        self.session.add(invitation)
        await self.session.commit()
        await self.session.refresh(invitation)

        # TODO: 发送邮件

        return invitation

    async def accept_invitation(self, token: str, user_id: UUID) -> Optional[TeamMember]:
        """接受团队邀请"""
        # 查找邀请
        invitation = await self.session.execute(
            select(TeamInvitation).where(
                TeamInvitation.token == token, TeamInvitation.status == 'PENDING'
            )
        )

        invite_obj = invitation.scalar_one_or_none()
        if not invite_obj or invite_obj.expires_at < datetime.utcnow():
            return None

        # 创建团队成员
        member = await self.add_member(invite_obj.team_id, user_id, invite_obj.role)

        # 更新邀请状态
        invite_obj.status = 'ACCEPTED'
        invite_obj.accepted_at = datetime.utcnow()

        await self.session.commit()

        return member

    async def get_team_members(self, team_id: UUID) -> List[TeamMember]:
        """获取团队成员列表"""
        result = await self.session.execute(select(TeamMember).where(TeamMember.team_id == team_id))
        return list(result.scalars().all())
        # 需要在 TeamService 中添加

    async def get_team(self, team_id: UUID) -> Optional[Team]:
        """获取团队信息"""
        return await self.session.get(Team, team_id)

    # 需要实现邮件发送功能
    async def _send_invitation_email(self, invitation: TeamInvitation):
        """发送邀请邮件"""
        # TODO: 集成邮件服务
        pass
