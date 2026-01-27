"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:52:40
FilePath: /api/app/schemas/plugin.py
Description: 插件数据模型
插件相关的 Pydantic schemas
本模块定义了插件管理相关的数据验证和序列化模式。

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class PluginBase(BaseModel):
    """插件基础模式"""

    name: str = Field(..., min_length=1, max_length=255, description='插件名称')
    display_name: str = Field(..., min_length=1, max_length=255, description='显示名称')
    description: str = Field(..., description='插件描述')
    version: str = Field(..., max_length=50, description='插件版本')
    author: str = Field(..., max_length=255, description='插件作者')
    icon: Optional[str] = Field(None, max_length=500, description='插件图标URL')
    category: str = Field(..., max_length=50, description='插件分类（tool/node/integration）')
    plugin_type: str = Field(
        ..., max_length=50, description='插件类型（builtin/custom/marketplace）'
    )
    manifest: Dict[str, Any] = Field(default_factory=dict, description='插件清单（配置schema等）')
    source_url: Optional[str] = Field(None, max_length=500, description='源代码URL')
    documentation_url: Optional[str] = Field(None, max_length=500, description='文档URL')

    @validator('category')
    def validate_category(cls, v):
        """验证插件分类"""
        allowed_categories = ['tool', 'node', 'integration']
        if v.lower() not in allowed_categories:
            raise ValueError(f'Category must be one of: {allowed_categories}')
        return v.lower()

    @validator('plugin_type')
    def validate_plugin_type(cls, v):
        """验证插件类型"""
        allowed_types = ['builtin', 'custom', 'marketplace']
        if v.lower() not in allowed_types:
            raise ValueError(f'Plugin type must be one of: {allowed_types}')
        return v.lower()


class PluginCreate(PluginBase):
    """创建插件的请求模式"""

    is_active: bool = Field(default=True, description='是否激活')
    is_verified: bool = Field(default=False, description='是否已验证')


class PluginUpdate(BaseModel):
    """更新插件的请求模式"""

    display_name: Optional[str] = Field(None, min_length=1, max_length=255, description='显示名称')
    description: Optional[str] = Field(None, description='插件描述')
    version: Optional[str] = Field(None, max_length=50, description='插件版本')
    author: Optional[str] = Field(None, max_length=255, description='插件作者')
    icon: Optional[str] = Field(None, max_length=500, description='插件图标URL')
    category: Optional[str] = Field(None, max_length=50, description='插件分类')
    plugin_type: Optional[str] = Field(None, max_length=50, description='插件类型')
    manifest: Optional[Dict[str, Any]] = Field(None, description='插件清单')
    source_url: Optional[str] = Field(None, max_length=500, description='源代码URL')
    documentation_url: Optional[str] = Field(None, max_length=500, description='文档URL')
    is_active: Optional[bool] = Field(None, description='是否激活')
    is_verified: Optional[bool] = Field(None, description='是否已验证')

    @validator('category')
    def validate_category(cls, v):
        """验证插件分类"""
        if v is not None:
            allowed_categories = ['tool', 'node', 'integration']
            if v.lower() not in allowed_categories:
                raise ValueError(f'Category must be one of: {allowed_categories}')
            return v.lower()
        return v

    @validator('plugin_type')
    def validate_plugin_type(cls, v):
        """验证插件类型"""
        if v is not None:
            allowed_types = ['builtin', 'custom', 'marketplace']
            if v.lower() not in allowed_types:
                raise ValueError(f'Plugin type must be one of: {allowed_types}')
            return v.lower()
        return v


class PluginResponse(PluginBase):
    """插件响应模式"""

    id: UUID = Field(..., description='插件ID')
    install_count: int = Field(..., description='安装次数')
    rating: float = Field(..., description='评分（0-5）')
    is_active: bool = Field(..., description='是否激活')
    is_verified: bool = Field(..., description='是否已验证')
    created_at: datetime = Field(..., description='创建时间')
    updated_at: datetime = Field(..., description='更新时间')

    class Config:
        from_attributes = True


class PluginDeleteResponse(BaseModel):
    """插件删除响应模式"""

    success: bool = Field(..., description='是否成功')
    message: str = Field(..., description='消息')
    plugin_id: UUID = Field(..., description='插件ID')


# ============================================================================
# 已安装插件相关 Schemas
# ============================================================================


class InstalledPluginBase(BaseModel):
    """已安装插件基础模式"""

    plugin_id: UUID = Field(..., description='插件ID')
    config: Dict[str, Any] = Field(default_factory=dict, description='插件配置')
    is_enabled: bool = Field(default=True, description='是否启用')


class InstalledPluginCreate(InstalledPluginBase):
    """安装插件的请求模式"""

    pass


class InstalledPluginUpdate(BaseModel):
    """更新已安装插件的请求模式"""

    config: Optional[Dict[str, Any]] = Field(None, description='插件配置')
    is_enabled: Optional[bool] = Field(None, description='是否启用')


class InstalledPluginResponse(InstalledPluginBase):
    """已安装插件响应模式"""

    id: UUID = Field(..., description='安装记录ID')
    workspace_id: UUID = Field(..., description='工作空间ID')
    installed_by: UUID = Field(..., description='安装者用户ID')
    installed_at: datetime = Field(..., description='安装时间')
    created_at: datetime = Field(..., description='创建时间')
    updated_at: datetime = Field(..., description='更新时间')

    # 包含插件详情
    plugin: Optional[PluginResponse] = Field(None, description='插件详情')

    class Config:
        from_attributes = True


class InstalledPluginListResponse(BaseModel):
    """已安装插件列表响应模式"""

    installed_plugins: list[InstalledPluginResponse] = Field(..., description='已安装插件列表')
    total: int = Field(..., description='总数量')
    page: int = Field(..., description='当前页码')
    page_size: int = Field(..., description='每页大小')


class InstalledPluginDeleteResponse(BaseModel):
    """卸载插件响应模式"""

    success: bool = Field(..., description='是否成功')
    message: str = Field(..., description='消息')
    installed_plugin_id: UUID = Field(..., description='安装记录ID')
