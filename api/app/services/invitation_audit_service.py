"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:54:08
FilePath: /api/app/services/invitation_audit_service.py
Description: Invitation Audit Service服务

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.audit.audit_log import AuditLog
from app.models.tenant.invitation import TeamInvitation


class InvitationAuditService:
    """邀请审计服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_invitation_sent(
        self,
        invitation_id: UUID,
        team_id: UUID,
        inviter_id: UUID,
        invitee_email: str,
        role: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
    ):
        """记录邀请发送日志"""
        audit_log = AuditLog(
            workspace_id=workspace_id or team_id,
            user_id=inviter_id,
            action='INVITATION_SENT',
            resource_type='TEAM_INVITATION',
            resource_id=invitation_id,  # 逻辑外键关联
            # 大幅简化details，移除冗余字段
            details={
                'security_context': {
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                },
                'business_context': {
                    'invite_method': 'email',
                    'expires_hours': 168,
                },
            },
            ip_address=ip_address,
            user_agent=user_agent,
            status='SUCCESS',
        )

        self.session.add(audit_log)
        await self.session.commit()

    async def log_invitation_accepted(
        self,
        invitation_id: UUID,
        team_id: UUID,
        accepter_id: UUID,
        token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
    ):
        """记录邀请接受日志"""
        audit_log = AuditLog(
            workspace_id=workspace_id or team_id,
            user_id=accepter_id,
            action='INVITATION_ACCEPTED',
            resource_type='TEAM_INVITATION',
            resource_id=invitation_id,  # 逻辑外键关联
            details={
                'security_context': {
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'token_used': token[:8] + '...',  # 只记录令牌前8位
                },
                'business_context': {
                    'acceptance_method': 'token_validation',
                },
            },
            ip_address=ip_address,
            user_agent=user_agent,
            status='SUCCESS',
        )

        self.session.add(audit_log)
        await self.session.commit()

    async def log_invitation_failed(
        self,
        token: str,
        user_id: Optional[UUID],
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
    ):
        """记录邀请失败日志"""
        audit_log = AuditLog(
            workspace_id=workspace_id,
            user_id=user_id,
            action='INVITATION_FAILED',
            resource_type='TEAM_INVITATION',
            resource_id=None,  # 失败时可能无法确定invitation_id
            details={
                'security_context': {
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'token_attempted': token[:8] + '...',
                },
                'failure_context': {
                    'reason': reason,
                    'failure_type': 'token_validation_failed',
                },
            },
            ip_address=ip_address,
            user_agent=user_agent,
            status='FAILED',
            error_message=reason,
        )

        self.session.add(audit_log)
        await self.session.commit()

    async def log_rate_limit_exceeded(
        self,
        user_id: UUID,
        limit_type: str,
        current_count: int,
        limit: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
    ):
        """记录频率限制超出日志"""
        audit_log = AuditLog(
            workspace_id=workspace_id,
            user_id=user_id,
            action='INVITATION_RATE_LIMITED',
            resource_type='USER',
            resource_id=user_id,
            details={
                'security_context': {
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                },
                'rate_limit_context': {
                    'limit_type': limit_type,
                    'current_count': current_count,
                    'limit': limit,
                    'exceeded_by': current_count - limit,
                },
            },
            ip_address=ip_address,
            user_agent=user_agent,
            status='BLOCKED',
            error_message=f'Rate limit exceeded: {current_count}/{limit} for {limit_type}',
        )

        self.session.add(audit_log)
        await self.session.commit()

    # 新增查询方法 - 利用逻辑外键关联

    async def get_invitation_audit_trail(self, invitation_id: UUID) -> Dict[str, Any]:
        """通过现有的resource_id外键查询邀请的完整审计轨迹"""

        # 1. 通过外键查询审计记录
        stmt = (
            select(AuditLog)
            .where(
                AuditLog.resource_type == 'TEAM_INVITATION', AuditLog.resource_id == invitation_id
            )
            .order_by(AuditLog.created_at)
        )

        result = await self.session.exec(stmt)
        audit_logs = result.all()

        # 2. 通过外键获取关联的invitation详情
        invitation = await self.session.get(TeamInvitation, invitation_id)

        # 3. 组合返回完整信息
        return {
            'invitation': invitation,  # 当前状态
            'audit_trail': audit_logs,  # 历史轨迹
            'summary': self._generate_audit_summary(audit_logs),
        }

    async def get_team_audit_summary(self, team_id: UUID, hours: int = 24) -> Dict[str, Any]:
        """查询团队相关的审计汇总"""

        # 计算时间范围
        since = datetime.utcnow() - timedelta(hours=hours)

        # 通过JOIN查询（利用现有外键）
        stmt = (
            select(AuditLog, TeamInvitation)
            .join(TeamInvitation, AuditLog.resource_id == TeamInvitation.id)
            .where(
                AuditLog.resource_type == 'TEAM_INVITATION',
                TeamInvitation.team_id == team_id,
                AuditLog.created_at >= since,
            )
            .order_by(AuditLog.created_at.desc())
        )

        result = await self.session.exec(stmt)
        results = result.all()

        return self._process_team_audit_data(results)

    async def get_security_events(self, user_id: UUID, hours: int = 24) -> List[AuditLog]:
        """获取用户相关的安全事件"""

        since = datetime.utcnow() - timedelta(hours=hours)

        stmt = (
            select(AuditLog)
            .where(
                AuditLog.user_id == user_id,
                AuditLog.created_at >= since,
                AuditLog.action.in_(['INVITATION_FAILED', 'INVITATION_RATE_LIMITED']),
            )
            .order_by(AuditLog.created_at.desc())
        )

        result = await self.session.exec(stmt)
        return result.all()

    async def detect_suspicious_activity(self, ip_address: str, hours: int = 1) -> Dict[str, Any]:
        """检测可疑活动"""

        since = datetime.utcnow() - timedelta(hours=hours)

        stmt = select(AuditLog).where(
            AuditLog.ip_address == ip_address,
            AuditLog.created_at >= since,
            AuditLog.status.in_(['FAILED', 'BLOCKED']),
        )

        result = await self.session.exec(stmt)
        failed_attempts = result.all()

        return {
            'ip_address': ip_address,
            'failed_attempts_count': len(failed_attempts),
            'time_window_hours': hours,
            'is_suspicious': len(failed_attempts) >= 5,  # 阈值可配置
            'recent_failures': failed_attempts[:10],  # 最近10次失败
        }

    # 私有辅助方法

    def _generate_audit_summary(self, audit_logs: List[AuditLog]) -> Dict[str, Any]:
        """生成审计轨迹摘要"""

        if not audit_logs:
            return {'total_events': 0}

        actions = {}
        for log in audit_logs:
            actions[log.action] = actions.get(log.action, 0) + 1

        return {
            'total_events': len(audit_logs),
            'actions_summary': actions,
            'first_event': audit_logs[0].created_at,
            'last_event': audit_logs[-1].created_at,
            'status_summary': {
                'success': len([log for log in audit_logs if log.status == 'SUCCESS']),
                'failed': len([log for log in audit_logs if log.status == 'FAILED']),
                'blocked': len([log for log in audit_logs if log.status == 'BLOCKED']),
            },
        }

    def _process_team_audit_data(self, results: List[tuple]) -> Dict[str, Any]:
        """处理团队审计数据"""

        if not results:
            return {'total_events': 0, 'invitations': []}

        # 按邀请分组
        invitations_data = {}
        for audit_log, invitation in results:
            inv_id = str(invitation.id)
            if inv_id not in invitations_data:
                invitations_data[inv_id] = {'invitation': invitation, 'events': []}
            invitations_data[inv_id]['events'].append(audit_log)

        return {
            'total_events': len(results),
            'unique_invitations': len(invitations_data),
            'invitations': list(invitations_data.values()),
            'summary': self._generate_team_summary(results),
        }

    def _generate_team_summary(self, results: List[tuple]) -> Dict[str, Any]:
        """生成团队审计摘要"""

        total_events = len(results)
        if total_events == 0:
            return {}

        # 统计各种状态
        success_count = len([r for r in results if r[0].status == 'SUCCESS'])
        failed_count = len([r for r in results if r[0].status == 'FAILED'])

        # 统计各种操作
        actions = {}
        for audit_log, _ in results:
            actions[audit_log.action] = actions.get(audit_log.action, 0) + 1

        return {
            'success_rate': round(success_count / total_events * 100, 2),
            'total_invitations_sent': actions.get('INVITATION_SENT', 0),
            'total_invitations_accepted': actions.get('INVITATION_ACCEPTED', 0),
            'total_failures': failed_count,
            'actions_breakdown': actions,
        }
