"""LLM provider data models."""

from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4


class LLMProvider(SQLModel, table=True):
    """LLM provider model for managing AI service configurations."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    workspace_id: UUID = Field(foreign_key="workspace.id", index=True)  # 租户隔离
    provider_type: str  # OPENAI, ANTHROPIC, etc.
    api_key_encrypted: str
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_by: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# LLMModel 不需要持久化，作为配置类使用
class LLMModel(SQLModel):
    """LLM model configuration (not persisted to database)."""

    provider_type: str
    model_name: str
    max_tokens: int
    supports_streaming: bool
