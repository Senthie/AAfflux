"""插件模型 - 2张表。

本模块定义了插件系统的数据模型。
支持插件的下载、安装和管理。
"""

from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlmodel import Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import BaseModel, TimestampMixin, WorkspaceMixin


class Plugin(BaseModel, TimestampMixin, table=True):
    """插件表 - 插件定义。

    存储可用插件的信息和配置。
    插件可以扩展系统功能，如自定义节点类型、工具等。

    Attributes:
    已经继承
        id: 插件唯一标识符（UUID）
        created_at: 创建时间
        updated_at: 更新时间

        name: 插件名称
        display_name: 显示名称
        description: 插件描述
        version: 插件版本
        author: 插件作者
        icon: 插件图标URL
        category: 插件分类（tool-工具/node-节点/integration-集成）
        plugin_type: 插件类型（builtin-内置/custom-自定义/marketplace-市场）
        manifest: 插件清单（JSONB格式，包含配置schema等）
        source_url: 源代码URL
        documentation_url: 文档URL
        install_count: 安装次数
        rating: 评分（0-5）
        is_active: 是否激活
        is_verified: 是否已验证


    业务规则：
        - 插件可以是内置、自定义或来自市场
        - 插件需要验证后才能公开
        - 记录安装次数和评分
        - 插件清单定义配置schema和能力
    """

    __tablename__ = 'plugins'

    name: str = Field(max_length=255, unique=True, index=True)
    display_name: str = Field(max_length=255)
    description: str
    version: str = Field(max_length=50)
    author: str = Field(max_length=255)
    icon: Optional[str] = Field(default=None, max_length=500)
    category: str = Field(max_length=50, index=True)  # tool, node, integration
    plugin_type: str = Field(max_length=50, index=True)  # builtin, custom, marketplace
    manifest: dict = Field(sa_column=Column(JSONB))
    source_url: Optional[str] = Field(default=None, max_length=500)
    documentation_url: Optional[str] = Field(default=None, max_length=500)
    install_count: int = Field(default=0)
    rating: float = Field(default=0.0)
    is_active: bool = Field(default=True, index=True)
    is_verified: bool = Field(default=False, index=True)


class InstalledPlugin(BaseModel, TimestampMixin, WorkspaceMixin, table=True):
    """已安装插件表 - 工作空间插件。

    记录工作空间安装的插件及其配置。
    每个工作空间可以独立安装和配置插件。

    Attributes:
        id: 安装记录唯一标识符（UUID）
        workspace_id: 所属工作空间ID（逻辑外键，租户隔离）
        updated_at: 更新时间

        plugin_id: 插件ID（逻辑外键）
        config: 插件配置（JSONB格式）
        is_enabled: 是否启用
        installed_by: 安装者用户ID（逻辑外键）
        installed_at: 安装时间


    业务规则：
        - 插件安装在工作空间级别
        - 每个工作空间可以独立配置插件
        - 可以启用或禁用已安装的插件
        - 记录安装者和安装时间
    """

    __tablename__ = 'installed_plugins'

    plugin_id: UUID = Field(index=True)  # Logical FK to plugins
    config: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    is_enabled: bool = Field(default=True, index=True)
    installed_by: UUID = Field(index=True)  # Logical FK to users
    installed_at: datetime = Field(default_factory=datetime.utcnow, index=True)
