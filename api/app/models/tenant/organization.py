"""
Author: Senthie seemoon2077@gmail.com
Date: 2026-01-07 15:44:21
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-12 12:09:00
FilePath: /api/app/models/tenant/organization.py
Description:租户层模型 - 4张表。

本模块定义了系统的三层租户架构：
1. Organization - 企业表（顶层）
2. Team - 团队表（中层）
3. Workspace - 工作空间表（资源隔离层）
4. TeamMember - 团队成员表（用户-团队关联）

租户层级关系：Organization → Team → User-> Workspace
资源隔离单位：Workspace（所有业务资源都关联到 workspace_id）

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from datetime import datetime
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field

from app.models.base import AuditMixin, BaseEntity, SoftDeleteMixin, TimestampMixin, WorkspaceMixin


class Organization(BaseEntity, TimestampMixin, AuditMixin, SoftDeleteMixin, table=True):  # type: ignore
    """企业表 - 顶层组织实体。

    企业是系统中的最高层级组织单位，可以包含多个团队。
    企业级配置会被下级团队继承。

    Attributes:
    已经继承
        id: 企业唯一标识符（UUID）
        created_at: 创建时间
        updated_at: 最后更新时间
        created_by: 创建者用户ID（物理外键）
        deleted_at: Optional[datetime] = Field(default=None)
        is_deleted: bool = Field(default=False)

        settings: 企业级配置（JSONB格式）
        name: 企业名称
        description: 企业描述

    """

    __tablename__ = 'organizations'  # type: ignore

    name: str = Field(max_length=255, index=True)
    description: Optional[str] = None
    settings: dict = Field(default_factory=dict, sa_column=Column(JSONB))


class Team(WorkspaceMixin, BaseEntity, TimestampMixin, AuditMixin, SoftDeleteMixin, table=True):  # type: ignore
    """团队表 - 中层组织实体。

    团队是协作的基本单位，可以属于企业或独立存在。
    团队包含多个成员和工作空间。

    Attributes:
    已经继承
        id: 团队唯一标识符（UUID）
        created_by: 创建者用户ID（逻辑外键）
        created_at: 创建时间
        updated_at: 最后更新时间
        deleted_at: Optional[datetime] = Field(default=None)
        is_deleted: bool = Field(default=False)

        name: 团队名称
        organization_id: 所属企业ID（物理外键，可选）
        description: 团队描述
        settings: 团队级配置（JSONB格式）

    """

    __tablename__ = 'teams'  # type: ignore

    name: str = Field(max_length=255, index=True)
    organization_id: Optional[UUID] = Field(default=None, index=True)  # Logical FK to organizations
    description: Optional[str] = None
    settings: dict = Field(default_factory=dict, sa_column=Column(JSONB))


class TenantAccountRole(enum.StrEnum):
    OWNER = 'owner'  # 顶级拥有
    ADMIN = 'admin'  # 可以创建和修改资源
    EDITOR = 'editor'  # 可编辑
    NORMAL = 'normal'  # 只读访问
    DATASET_OPERATOR = 'dataset_operator'  # 数据集管理的专业角色

    @staticmethod
    def is_valid_role(role: str) -> bool:
        if not role:
            return False
        return role in {
            TenantAccountRole.OWNER,
            TenantAccountRole.ADMIN,
            TenantAccountRole.EDITOR,
            TenantAccountRole.NORMAL,
            TenantAccountRole.DATASET_OPERATOR,
        }

    @staticmethod
    def is_privileged_role(role: Optional['TenantAccountRole']) -> bool:
        if not role:
            return False
        return role in {TenantAccountRole.OWNER, TenantAccountRole.ADMIN}

    @staticmethod
    def is_admin_role(role: Optional['TenantAccountRole']) -> bool:
        if not role:
            return False
        return role == TenantAccountRole.ADMIN

    @staticmethod
    def is_non_owner_role(role: Optional['TenantAccountRole']) -> bool:
        if not role:
            return False
        return role in {
            TenantAccountRole.ADMIN,
            TenantAccountRole.EDITOR,
            TenantAccountRole.NORMAL,
            TenantAccountRole.DATASET_OPERATOR,
        }

    @staticmethod
    def is_editing_role(role: Optional['TenantAccountRole']) -> bool:
        if not role:
            return False
        return role in {TenantAccountRole.OWNER, TenantAccountRole.ADMIN, TenantAccountRole.EDITOR}

    @staticmethod
    def is_dataset_edit_role(role: Optional['TenantAccountRole']) -> bool:
        if not role:
            return False
        return role in {
            TenantAccountRole.OWNER,
            TenantAccountRole.ADMIN,
            TenantAccountRole.EDITOR,
            TenantAccountRole.DATASET_OPERATOR,
        }


class WorkspacePlan(enum.StrEnum):
    """
    用户订阅状态
    """

    FREE = 'free'
    PRO = 'pro'
    ENTERPRISE = 'enterprise'


class WorkspaceStatus(enum.StrEnum):
    """Workspace status enum."""

    NORMAL = 'normal'
    ARCHIVE = 'archive'


class Workspace(BaseEntity, TimestampMixin, SoftDeleteMixin, table=True):  # type: ignore
    """工作空间表 - 资源隔离单元。

    工作空间是资源隔离的基本单位，所有业务资源（工作流、应用等）都关联到工作空间。
    这是多租户隔离的核心：每个资源表都包含 workspace_id 字段。

    Attributes:
     已经继承
        id: 工作空间唯一标识符（UUID）
        created_by: 创建者用户ID（逻辑外键）
        created_at: 创建时间
        updated_at: 最后更新时间
        deleted_at: Optional[datetime] = Field(default=None)
        is_deleted: bool = Field(default=False)

        name: 工作空间名称
        description: 工作空间描述
        settings: 工作空间级配置（JSONB格式）

        encrypt_public_key：加密公钥
        plan: 租户的订阅计划
        status: 租户的状态，归档 or 正常

    v0.0.1 2026/1/8:
        移除了 `team_id` 由 `WorkspaceAccountUser` 进行数据表关联
        移除 `AuditMixin` 的字段，因为workspace会更具Accounts表进行用户关联
    """

    __tablename__ = 'workspaces'  # type: ignore

    name: str = Field(max_length=255, index=True)
    description: Optional[str] = None
    settings: dict = Field(default_factory=dict, sa_column=Column(JSONB))

    encrypt_public_key: str = Field(default='', max_length=1024)
    plan: WorkspacePlan = Field(default=WorkspacePlan.FREE, max_length=16)
    status: WorkspaceStatus = Field(default=WorkspaceStatus.NORMAL, max_length=16)

    def set_status(self, status: WorkspaceStatus) -> None:
        """设置工作空间状态。

        Args:
            status: WorkspaceStatus 枚举值
        """
        self.status = status
        if hasattr(self, 'touch'):
            self.touch()  # 更新时间戳

    def is_normal(self) -> bool:
        """检查工作空间是否处于活跃状态。

        Returns:
            bool: 如果状态为 NORMAL 返回 True
        """
        return self.status == WorkspaceStatus.NORMAL

    def archive(self) -> None:
        """归档工作空间。"""
        self.set_status(WorkspaceStatus.ARCHIVE)

    def normal(self) -> None:
        """设置工作空间为正常状态"""
        self.set_status(WorkspaceStatus.NORMAL)

    def set_plan(self, plan: WorkspacePlan) -> None:
        """设置工作空间计划。

        Args:
            plan: WorkspacePlan 枚举值
        """
        self.plan = plan
        if hasattr(self, 'touch'):
            self.touch()  # 更新时间戳


class WorkspaceAccountUser(
    WorkspaceMixin,
    BaseEntity,
    TimestampMixin,
    SoftDeleteMixin,
    table=True,  # type: ignore
):
    """
    租户账户表 - 用户与租户的关联关系。

    建立用户和租户之间的多对多关系，并定义用户在租户中的角色。

    Attributes:
    已经继承
        id: 账户记录唯一标识符（UUID）

        workspace_id: 工作空间ID（逻辑外键）
        user_id: 用户ID（逻辑外键）
        role: 角色（ADMIN-管理员/MEMBER-成员/GUEST-访客）
        joined_at: 加入时间
    """

    __tablename__ = 'workspace_accounts'  # type: ignore
    __table_args__ = (UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_user'),)

    # 外联属性
    user_id: UUID = Field(index=True)  # Logical FK to users
    # 关键 key
    role: TenantAccountRole = Field(default=TenantAccountRole.NORMAL, max_length=16)
    current: bool = Field(default=True)
    invited_by: UUID | None = Field(default=None)


class TeamMember(BaseEntity, table=True):  # type: ignore
    """团队成员表 - 用户与团队的关联关系。

    建立用户和团队之间的多对多关系，并定义用户在团队中的角色。
    一个用户可以属于多个团队，在不同团队中可以有不同角色。

    Attributes:
    已经继承
        id: 成员记录唯一标识符（UUID）

        team_id: 团队ID（逻辑外键）
        user_id: 用户ID（逻辑外键）
        role: 角色（ADMIN-管理员/MEMBER-成员/GUEST-访客）
        joined_at: 加入时间

    v0.0.1:
        移除了 `role` 属性，团队的权限通过 workspace 进行分配
    """

    __tablename__ = 'team_members'  # type: ignore

    team_id: UUID = Field(index=True)  # Logical FK to teams
    user_id: UUID = Field(index=True)  # Logical FK to users
    joined_at: datetime = Field(default_factory=datetime.utcnow)
