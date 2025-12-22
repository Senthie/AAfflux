"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-10 14:41:10
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-22 14:28:14
FilePath: : AAfflux: api: app: services: team_service.py
Description:团队管理服务，实现了团队的crud操作，还有团队成员的邀请链接，令牌的审查。
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.tenant.organization import Team, TeamMember
from app.models.tenant.invitation import TeamInvitation
from app.models.auth.user import User
from app.schemas.team import TeamCreate
from app.utils.rbac import Role
from app.utils.invitation_security import InvitationSecurityManager
from app.services.invitation_audit_service import InvitationAuditService
from app.services.email_service import EmailService
from app.core.redis import get_redis
from app.core.config import settings


class TeamService:
    """团队管理服务"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._redis = None
        self._security_manager = None
        self._audit_service = None
        self._email_service = EmailService()

    async def _get_redis(self):
        """获取Redis客户端"""
        if self._redis is None:
            self._redis = await get_redis()
            # 确保链接建立
            if not self._redis.redis:
                await self._redis.connect()
        return self._redis

    async def _get_security_manager(self):
        """获取安全管理器"""
        if self._security_manager is None:
            redis_client = await self._get_redis()
            self._security_manager = InvitationSecurityManager(redis_client)
        return self._security_manager

    async def _get_audit_service(self):
        """获取审计服务"""
        if self._audit_service is None:
            self._audit_service = InvitationAuditService(self.session)
        return self._audit_service

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
        self,
        team_id: UUID,
        email: str,
        role: str,
        invited_by: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
    ) -> dict:
        """发送团队邀请（安全版本）"""

        security_manager = await self._get_security_manager()
        audit_service = await self._get_audit_service()

        # 1. 检查频率限制
        rate_check = await security_manager.check_rate_limit(invited_by)
        if not rate_check['allowed']:
            # 记录频率限制日志
            await audit_service.log_rate_limit_exceeded(
                user_id=invited_by,
                limit_type=rate_check['period'],
                current_count=rate_check['current_count'],
                limit=rate_check['limit'],
                ip_address=ip_address,
                user_agent=user_agent,
                workspace_id=workspace_id,
            )
            raise ValueError(rate_check['reason'])

        # 2. 检查重复邀请
        if await self._check_duplicate_invitation(team_id, email):
            raise ValueError(f'邮箱 {email} 已有待处理的邀请')

        # 3. 生成安全令牌
        secure_token = security_manager.generate_secure_token(team_id, email)

        # 4. 创建邀请记录
        invitation = TeamInvitation(
            team_id=team_id,
            email=email,
            role=role,
            token=secure_token,
            invited_by=invited_by,
            expires_at=datetime.utcnow()
            + timedelta(days=settings.invitation_security.token_expire_days),
        )

        self.session.add(invitation)
        await self.session.flush()  # 获取invitation.id

        # 5. 增加频率计数
        await security_manager.increment_rate_limit(invited_by)

        # 6. 记录审计日志
        await audit_service.log_invitation_sent(
            invitation_id=invitation.id,
            team_id=team_id,
            inviter_id=invited_by,
            invitee_email=email,
            role=role,
            ip_address=ip_address,
            user_agent=user_agent,
            workspace_id=workspace_id,
        )

        await self.session.commit()
        await self.session.refresh(invitation)

        # 7. 获取团队和邀请者信息
        team = await self.get_team(team_id)
        inviter = await self.session.get(User, invited_by)

        # 8. 发送邀请邮件
        email_sent = await self._email_service.send_invitation_email(
            to_email=email,
            inviter_name=inviter.username if inviter else '系统管理员',
            team_name=team.name if team else '未知团队',
            invite_token=secure_token,
            expires_at=invitation.expires_at.strftime('%Y年%m月%d日 %H:%M'),
        )

        return {
            'invitation': invitation,
            'email_sent': email_sent,
            'token': secure_token,
            'expires_at': invitation.expires_at,
            'message': '邀请邮件已发送' if email_sent else '邀请创建成功，但邮件发送失败',
        }

    async def accept_invitation(
        self,
        token: str,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
    ) -> Optional[TeamMember]:
        """接受团队邀请（安全版本）"""

        security_manager = await self._get_security_manager()
        audit_service = await self._get_audit_service()

        # 1. 检查令牌使用情况
        token_usage = await security_manager.check_token_usage(token)
        if token_usage['used']:
            await audit_service.log_invitation_failed(
                token=token,
                user_id=user_id,
                reason='令牌已被使用',
                ip_address=ip_address,
                user_agent=user_agent,
                workspace_id=workspace_id,
            )
            return None

        # 2. 检查是否在黑名单中
        redis_client = await self._get_redis()
        blocked_key = f'blocked_tokens:{token}'
        if await redis_client.exists(blocked_key):
            await audit_service.log_invitation_failed(
                token=token,
                user_id=user_id,
                reason='令牌已被阻止',
                ip_address=ip_address,
                user_agent=user_agent,
                workspace_id=workspace_id,
            )
            return None

        # 3. 查找邀请记录
        invitation = await self.session.execute(
            select(TeamInvitation).where(
                TeamInvitation.token == token, TeamInvitation.status == 'PENDING'
            )
        )

        invite_obj = invitation.scalar_one_or_none()
        if not invite_obj:
            # 记录尝试使用无效令牌
            await security_manager.record_token_attempt(token, success=False)
            await audit_service.log_invitation_failed(
                token=token,
                user_id=user_id,
                reason='令牌无效',
                ip_address=ip_address,
                user_agent=user_agent,
                workspace_id=workspace_id,
            )
            return None

        # 4. 检查令牌是否过期
        if invite_obj.expires_at < datetime.utcnow():
            await security_manager.record_token_attempt(token, success=False)
            await audit_service.log_invitation_failed(
                token=token,
                user_id=user_id,
                reason='令牌已过期',
                ip_address=ip_address,
                user_agent=user_agent,
                workspace_id=workspace_id,
            )
            return None

        # 5. 验证令牌签名
        if not security_manager.verify_token_signature(token, invite_obj.team_id, invite_obj.email):
            await security_manager.record_token_attempt(token, success=False)
            await audit_service.log_invitation_failed(
                token=token,
                user_id=user_id,
                reason='令牌签名无效',
                ip_address=ip_address,
                user_agent=user_agent,
                workspace_id=workspace_id,
            )
            return None

        # 6. 创建团队成员
        try:
            member = await self.add_member(invite_obj.team_id, user_id, invite_obj.role)

            # 7. 立即使令牌失效
            invite_obj.status = 'ACCEPTED'
            invite_obj.accepted_at = datetime.utcnow()

            # 8. 记录令牌使用成功
            await security_manager.record_token_attempt(token, success=True, user_id=user_id)

            # 9. 记录审计日志
            await audit_service.log_invitation_accepted(
                invitation_id=invite_obj.id,
                team_id=invite_obj.team_id,
                accepter_id=user_id,
                token=token,
                ip_address=ip_address,
                user_agent=user_agent,
                workspace_id=workspace_id,
            )

            await self.session.commit()
            return member

        except ValueError as e:
            # 如果用户已经是成员，也要记录日志
            await audit_service.log_invitation_failed(
                token=token,
                user_id=user_id,
                reason=str(e),
                ip_address=ip_address,
                user_agent=user_agent,
                workspace_id=workspace_id,
            )
            return None

    async def get_team_members(self, team_id: UUID) -> List[TeamMember]:
        """获取团队成员列表"""
        result = await self.session.execute(select(TeamMember).where(TeamMember.team_id == team_id))
        return list(result.scalars().all())
        # 需要在 TeamService 中添加

    async def get_team(self, team_id: UUID) -> Optional[Team]:
        """获取团队信息"""
        return await self.session.get(Team, team_id)

    async def get_invitation_by_token(self, token: str) -> Optional[TeamInvitation]:
        """根据令牌获取邀请信息"""
        invitation = await self.session.execute(
            select(TeamInvitation).where(
                TeamInvitation.token == token, TeamInvitation.status == 'PENDING'
            )
        )
        return invitation.scalar_one_or_none()

    async def get_pending_invitations(self, team_id: UUID) -> List[TeamInvitation]:
        """获取团队待处理的邀请列表"""
        result = await self.session.execute(
            select(TeamInvitation).where(
                TeamInvitation.team_id == team_id,
                TeamInvitation.status == 'PENDING',
                TeamInvitation.expires_at > datetime.utcnow(),
            )
        )
        return list(result.scalars().all())

    async def _check_duplicate_invitation(self, team_id: UUID, email: str) -> bool:
        """检查重复邀请"""
        existing = await self.session.execute(
            select(TeamInvitation).where(
                TeamInvitation.team_id == team_id,
                TeamInvitation.email == email,
                TeamInvitation.status == 'PENDING',
                TeamInvitation.expires_at > datetime.utcnow(),
            )
        )
        return existing.scalar_one_or_none() is not None
