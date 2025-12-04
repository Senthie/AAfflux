# 
# Author: kk123047 3254834740@qq.com
# Date: 2025-12-02 10:58:51
# LastEditors: kk123047 3254834740@qq.com
# LastEditTime: 2025-12-04 10:56:28
# FilePath: : AAfflux: api: app: models: application: llm_provider.py
# Description: 
# 
"""LLM提供商模型 - 1张表。

本模块定义了LLM提供商配置的数据模型。
支持多种LLM服务提供商（OpenAI、Anthropic等）的配置管理。
"""

from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import BaseModel, TimestampMixin, WorkspaceMixin, AuditMixin


class LLMProvider(BaseModel, TimestampMixin, AuditMixin, WorkspaceMixin, table=True):
    """LLM提供商表 - AI模型服务配置。

    存储LLM服务提供商的配置信息，包括API密钥和自定义配置。
    每个工作空间可以配置多个LLM提供商。

    Attributes:
    已经继承
        id: 提供商配置唯一标识符（UUID）
        workspace_id: 所属工作空间ID（逻辑外键，租户隔离）
        created_by: 创建者用户ID（逻辑外键）
        created_at: 创建时间
        updated_at: 最后更新时间

        name: 配置名称（用户自定义）
        provider_type: 提供商类型（OPENAI/ANTHROPIC/AZURE等）
        api_key_encrypted: 加密的API密钥
        config: 提供商特定配置（JSONB格式）

    """

    __tablename__ = "llm_providers"
    name: str = Field(max_length=255)
    provider_type: str = Field(max_length=50)  # OPENAI, ANTHROPIC, AZURE, etc.
    api_key_encrypted: str = Field(max_length=500)
    config: dict = Field(default_factory=dict, sa_column=Column(JSONB))


# LLMModel 不需要持久化，作为配置类使用
class LLMModel(SQLModel):
    """LLM model configuration (not persisted to database)."""

    provider_type: str
    model_name: str
    max_tokens: int
    supports_streaming: bool
