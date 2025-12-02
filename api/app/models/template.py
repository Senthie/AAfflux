"""Prompt template data models."""

from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4


class PromptTemplate(SQLModel, table=True):
    """Prompt template model for reusable prompt configurations."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    workspace_id: UUID = Field(foreign_key="workspace.id", index=True)  # 租户隔离
    content: str
    variables: list = Field(default_factory=list, sa_column=Column(JSON))
    version: int = Field(default=1)
    created_by: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    versions: List["PromptTemplateVersion"] = Relationship(back_populates="template")


class PromptTemplateVersion(SQLModel, table=True):
    """Prompt template version model for maintaining template history."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    template_id: UUID = Field(foreign_key="prompttemplate.id", index=True)
    version: int
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    template: Optional[PromptTemplate] = Relationship(back_populates="versions")
