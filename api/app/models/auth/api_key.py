"""API密钥模型 - 1张表。

本模块定义了API密钥的数据模型。
支持应用的API访问控制和密钥管理。
"""

from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from sqlmodel import SQLModel, Field


class APIKey(SQLModel, table=True):
    """API密钥表 - 管理应用API密钥。
    
    存储应用的API密钥，用于外部系统调用应用API。
    支持密钥的创建、撤销和使用追踪。
    
    Attributes:
        id: 密钥记录唯一标识符（UUID）
        application_id: 应用ID（逻辑外键）
        key_hash: 密钥哈希值（唯一）
        key_prefix: 密钥前缀（用于显示，如 "sk_live_abc..."）
        name: 密钥名称（用户自定义，便于识别）
        last_used_at: 最后使用时间
        is_active: 是否激活
        created_by: 创建者用户ID（逻辑外键）
        created_at: 创建时间
    
    业务规则：
        - 密钥以哈希形式存储，原始密钥只在创建时显示一次
        - 每个应用可以有多个API密钥
        - 密钥可以随时撤销（设置 is_active = False）
        - 记录最后使用时间用于安全审计
    """
    __tablename__ = "api_keys"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    application_id: UUID = Field(index=True)  # Logical FK to applications
    key_hash: str = Field(max_length=255, unique=True, index=True)
    key_prefix: str = Field(max_length=20)  # 如 "sk_live_abc"
    name: str = Field(max_length=255)
    last_used_at: Optional[datetime] = None
    is_active: bool = Field(default=True, index=True)
    created_by: UUID = Field(index=True)  # Logical FK to users
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
