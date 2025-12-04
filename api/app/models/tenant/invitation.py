"""团队邀请模型 - 1张表。

本模块定义了团队邀请的数据模型。
支持邀请成员加入团队的完整流程。
"""

from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlmodel import Field
from app.models.base import BaseModel, TimestampMixin


class TeamInvitation(BaseModel, TimestampMixin, table=True):
    """团队邀请表 - 管理团队成员邀请。

    存储团队邀请信息，支持邀请流程管理。
    邀请通过邮件发送，包含唯一的邀请令牌。

    Attributes:
    已经继承
        id: 邀请记录唯一标识符（UUID）
        created_at: 创建时间

        team_id: 团队ID（逻辑外键）
        email: 被邀请人邮箱
        role: 邀请角色（ADMIN/MEMBER/GUEST）
        token: 邀请令牌（唯一）
        invited_by: 邀请人用户ID（逻辑外键）
        status: 邀请状态（PENDING-待接受/ACCEPTED-已接受/EXPIRED-已过期/CANCELLED-已取消）
        expires_at: 过期时间
        accepted_at: 接受时间
    业务规则：
        - 邀请令牌通过邮件发送
        - 邀请有效期通常为7天
        - 接受邀请后创建 TeamMember 记录
        - 同一邮箱在同一团队只能有一个待处理的邀请
    """

    __tablename__ = "team_invitations"

    team_id: UUID = Field(index=True)  # Logical FK to teams
    email: str = Field(max_length=255, index=True)
    role: str = Field(max_length=16)  # ADMIN, MEMBER, GUEST
    token: str = Field(max_length=255, unique=True, index=True)
    invited_by: UUID = Field(index=True)  # Logical FK to users
    status: str = Field(
        max_length=20, index=True, default="PENDING"
    )  # PENDING, ACCEPTED, EXPIRED, CANCELLED
    expires_at: datetime
    accepted_at: Optional[datetime] = None
