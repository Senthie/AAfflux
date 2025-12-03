"""租户层模型 - 4张表。

本模块定义了系统的三层租户架构：
1. Organization - 企业表（顶层）
2. Team - 团队表（中层）
3. Workspace - 工作空间表（资源隔离层）
4. TeamMember - 团队成员表（用户-团队关联）

租户层级关系：Organization → Team → Workspace
资源隔离单位：Workspace（所有业务资源都关联到 workspace_id）
"""

from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class Organization(SQLModel, table=True):
    """企业表 - 顶层组织实体。
    
    企业是系统中的最高层级组织单位，可以包含多个团队。
    企业级配置会被下级团队继承。
    
    Attributes:
        id: 企业唯一标识符（UUID）
        name: 企业名称
        description: 企业描述
        created_by: 创建者用户ID（物理外键）
        settings: 企业级配置（JSONB格式）
        created_at: 创建时间
        updated_at: 最后更新时间
    """
    __tablename__ = "organizations"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = None
    created_by: UUID = Field(foreign_key="users.id", index=True)  ##修改为逻辑外键
    settings: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Team(SQLModel, table=True):
    """团队表 - 中层组织实体。
    
    团队是协作的基本单位，可以属于企业或独立存在。
    团队包含多个成员和工作空间。
    
    Attributes:
        id: 团队唯一标识符（UUID）
        name: 团队名称
        organization_id: 所属企业ID（物理外键，可选）
        description: 团队描述
        settings: 团队级配置（JSONB格式）
        created_by: 创建者用户ID（逻辑外键）
        created_at: 创建时间
        updated_at: 最后更新时间
    """
    __tablename__ = "teams"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    organization_id: Optional[UUID] = Field(default=None, foreign_key="organizations.id", index=True)##修改为逻辑外键
    description: Optional[str] = None
    settings: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    created_by: UUID = Field(index=True)  # Logical FK to users
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Workspace(SQLModel, table=True):
    """工作空间表 - 资源隔离单元。
    
    工作空间是资源隔离的基本单位，所有业务资源（工作流、应用等）都关联到工作空间。
    这是多租户隔离的核心：每个资源表都包含 workspace_id 字段。
    
    Attributes:
        id: 工作空间唯一标识符（UUID）
        name: 工作空间名称
        team_id: 所属团队ID（逻辑外键）
        description: 工作空间描述
        settings: 工作空间级配置（JSONB格式）
        created_by: 创建者用户ID（逻辑外键）
        created_at: 创建时间
        updated_at: 最后更新时间
    """
    __tablename__ = "workspaces"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    team_id: UUID = Field(index=True)  # Logical FK to teams
    description: Optional[str] = None
    settings: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    created_by: UUID = Field(index=True)  # Logical FK to users
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TeamMember(SQLModel, table=True):
    """团队成员表 - 用户与团队的关联关系。
    
    建立用户和团队之间的多对多关系，并定义用户在团队中的角色。
    一个用户可以属于多个团队，在不同团队中可以有不同角色。
    
    Attributes:
        id: 成员记录唯一标识符（UUID）
        team_id: 团队ID（逻辑外键）
        user_id: 用户ID（逻辑外键）
        role: 角色（ADMIN-管理员/MEMBER-成员/GUEST-访客）
        joined_at: 加入时间
    """
    __tablename__ = "team_members"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    team_id: UUID = Field(index=True)  # Logical FK to teams
    user_id: UUID = Field(index=True)  # Logical FK to users
    role: str = Field(default="MEMBER", max_length=16)  # ADMIN, MEMBER, GUEST
    joined_at: datetime = Field(default_factory=datetime.utcnow)
