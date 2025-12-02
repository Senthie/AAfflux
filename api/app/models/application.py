"""Application data models."""

from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4


class Application(SQLModel, table=True):
    """Application model for published workflow APIs."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    workspace_id: UUID = Field(foreign_key="workspace.id", index=True)  # 租户隔离
    workflow_id: UUID = Field(foreign_key="workflow.id")
    api_key_hash: str
    endpoint: str
    is_published: bool = Field(default=False)
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_by: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
