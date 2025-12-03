"""基础模型和混入类，供所有数据库模型使用。

本模块提供了可复用的基础模型类和混入类，用于标准化数据库表的通用字段。
"""

from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from sqlmodel import SQLModel, Field


class TimestampMixin(SQLModel):
    """时间戳混入类。
    
    为模型添加创建时间和更新时间字段。
    所有需要记录时间戳的表都应该继承此混入类。
    
    Attributes:
        created_at: 记录创建时间，自动设置为当前 UTC 时间
        updated_at: 记录更新时间，自动设置为当前 UTC 时间
    """
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class UUIDMixin(SQLModel):
    """UUID 主键混入类。
    
    为模型添加 UUID 类型的主键字段。
    使用 UUID 而非自增 ID 可以避免分布式系统中的 ID 冲突。
    
    Attributes:
        id: UUID 类型的主键，自动生成
    """
    id: UUID = Field(default_factory=uuid4, primary_key=True)


class BaseModel(UUIDMixin, TimestampMixin, SQLModel):
    """基础模型类。
    
    组合了 UUID 主键和时间戳混入，提供完整的基础字段。
    所有业务模型都可以继承此类以获得标准字段。
    
    继承的字段：
        - id: UUID 主键
        - created_at: 创建时间
        - updated_at: 更新时间
    """
    pass
