"""User and organization related data models."""

from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4


class User(SQLModel, table=True):
    """User model for authentication and profile management."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    name: str
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Organization(SQLModel, table=True):
    """Organization model for enterprise-level grouping."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    description: Optional[str] = None
    created_by: UUID = Field(foreign_key="user.id")
    settings: dict = Field(default_factory=dict, sa_column=Column(JSON))  # 企业级别配置
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Team(SQLModel, table=True):
    """Team model for collaborative workspaces."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    organization_id: Optional[UUID] = Field(default=None, foreign_key="organization.id")
    description: Optional[str] = None
    settings: dict = Field(default_factory=dict, sa_column=Column(JSON))  # 团队级别配置
    created_by: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TeamMember(SQLModel, table=True):
    """Team membership with role-based access control."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    team_id: UUID = Field(foreign_key="team.id")
    user_id: UUID = Field(foreign_key="user.id")
    role: str  # ADMIN, MEMBER, GUEST
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class Workspace(SQLModel, table=True):
    """Workspace model for resource isolation within teams."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    team_id: UUID = Field(foreign_key="team.id", index=True)
    description: Optional[str] = None
    settings: dict = Field(default_factory=dict, sa_column=Column(JSON))  # 工作空间级别配置
    created_by: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
