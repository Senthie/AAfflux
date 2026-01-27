"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:55:00
FilePath: /api/app/services/plugin_service.py
Description: 插件服务

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth.user import UserEntity
from app.models.plugin.plugin import InstalledPlugin, Plugin
from app.schemas.page_schemas import PageRequest, PageResponse
from app.schemas.plugin import (
    InstalledPluginCreate,
    InstalledPluginResponse,
    InstalledPluginUpdate,
    PluginCreate,
    PluginResponse,
    PluginUpdate,
)


class PluginNotFoundError(Exception):
    """插件未找到异常"""

    pass


class InstalledPluginNotFoundError(Exception):
    """已安装插件未找到异常"""

    pass


class PluginAlreadyExistsError(Exception):
    """插件已存在异常"""

    pass


class PluginService:
    """插件服务类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================================================================
    # Plugin CRUD 操作
    # ========================================================================

    async def create_plugin(self, plugin_data: PluginCreate) -> PluginResponse:
        """创建插件

        Args:
            plugin_data: 插件创建数据

        Returns:
            创建的插件

        Raises:
            PluginAlreadyExistsError: 插件名称已存在
        """
        # 检查插件名称是否已存在
        stmt = select(Plugin).where(
            Plugin.name == plugin_data.name,  # type: ignore
            Plugin.is_deleted.is_(False),  # type: ignore
        )
        result = await self.session.execute(stmt)
        existing_plugin = result.scalar_one_or_none()

        if existing_plugin:
            raise PluginAlreadyExistsError(f'Plugin with name {plugin_data.name} already exists')

        # 创建插件
        plugin = Plugin(**plugin_data.model_dump())
        self.session.add(plugin)
        await self.session.commit()
        await self.session.refresh(plugin)

        return PluginResponse.model_validate(plugin)

    async def get_plugin(self, plugin_id: UUID) -> PluginResponse:
        """获取插件详情

        Args:
            plugin_id: 插件ID

        Returns:
            插件详情

        Raises:
            PluginNotFoundError: 插件不存在
        """
        stmt = select(Plugin).where(
            Plugin.id == plugin_id,  # type: ignore
            Plugin.is_deleted.is_(False),  # type: ignore
        )
        result = await self.session.execute(stmt)
        plugin = result.scalar_one_or_none()

        if not plugin:
            raise PluginNotFoundError(f'Plugin {plugin_id} not found')

        return PluginResponse.model_validate(plugin)

    async def list_plugins(
        self,
        page_req: PageRequest,
        category: Optional[str] = None,
        plugin_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
    ) -> PageResponse[PluginResponse]:
        """获取插件列表

        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            category: 插件分类过滤
            plugin_type: 插件类型过滤
            is_active: 是否激活过滤
            is_verified: 是否已验证过滤

        Returns:
            插件列表和总数
        """
        # 构建查询条件
        conditions = [Plugin.is_deleted.is_(False)]  # type: ignore

        if category:
            conditions.append(Plugin.category == category)  # type: ignore
        if plugin_type:
            conditions.append(Plugin.plugin_type == plugin_type)  # type: ignore
        if is_active is not None:
            conditions.append(Plugin.is_active.is_(is_active))  # type: ignore
        if is_verified is not None:
            conditions.append(Plugin.is_verified.is_(is_verified))  # type: ignore

        # 查询总数
        count_stmt = select(func.count()).select_from(Plugin).where(*conditions)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # compute table skip by current * size
        skip = (page_req.current - 1) * page_req.size
        # 查询插件列表
        stmt = (
            select(Plugin)
            .where(*conditions)
            .order_by(Plugin.created_at.desc())  # type: ignore
            .offset(skip)
            .limit(page_req.size)
        )
        result = await self.session.execute(stmt)
        plugins = result.scalars().all()

        records = [PluginResponse.model_validate(p) for p in plugins]

        return PageResponse[PluginResponse](
            records=records, total=total, size=page_req.size, current=page_req.current
        )

    async def update_plugin(self, plugin_id: UUID, plugin_data: PluginUpdate) -> PluginResponse:
        """更新插件

        Args:
            plugin_id: 插件ID
            plugin_data: 插件更新数据

        Returns:
            更新后的插件

        Raises:
            PluginNotFoundError: 插件不存在
        """
        stmt = select(Plugin).where(
            Plugin.id == plugin_id,  # type: ignore
            Plugin.is_deleted.is_(False),  # type: ignore
        )
        result = await self.session.execute(stmt)
        plugin = result.scalar_one_or_none()

        if not plugin:
            raise PluginNotFoundError(f'Plugin {plugin_id} not found')

        # 更新插件字段
        update_data = plugin_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plugin, field, value)

        await self.session.commit()
        await self.session.refresh(plugin)

        return PluginResponse.model_validate(plugin)

    async def delete_plugin(self, plugin_id: UUID) -> None:
        """删除插件（软删除）

        Args:
            plugin_id: 插件ID

        Raises:
            PluginNotFoundError: 插件不存在
        """
        stmt = select(Plugin).where(
            Plugin.id == plugin_id,  # type: ignore
            Plugin.is_deleted.is_(False),  # type: ignore
        )
        result = await self.session.execute(stmt)
        plugin = result.scalar_one_or_none()

        if not plugin:
            raise PluginNotFoundError(f'Plugin {plugin_id} not found')

        # 软删除
        plugin.is_deleted = True  # type: ignore
        await self.session.commit()

    # ========================================================================
    # InstalledPlugin CRUD 操作
    # ========================================================================

    async def install_plugin(
        self,
        workspace_id: UUID,
        user: UserEntity,
        plugin_data: InstalledPluginCreate,
    ) -> InstalledPluginResponse:
        """安装插件到工作空间

        Args:
            workspace_id: 工作空间ID
            user: 当前用户
            plugin_data: 安装插件数据

        Returns:
            已安装插件

        Raises:
            PluginNotFoundError: 插件不存在
        """
        # 验证插件是否存在
        plugin_stmt = select(Plugin).where(
            Plugin.id == plugin_data.plugin_id,  # type: ignore
            Plugin.is_deleted.is_(False),  # type: ignore
        )
        plugin_result = await self.session.execute(plugin_stmt)
        plugin = plugin_result.scalar_one_or_none()

        if not plugin:
            raise PluginNotFoundError(f'Plugin {plugin_data.plugin_id} not found')

        # 创建安装记录
        installed_plugin = InstalledPlugin(
            workspace_id=workspace_id,  # type: ignore
            installed_by=user.id,  # type: ignore
            **plugin_data.model_dump(),
        )
        self.session.add(installed_plugin)

        # 增加安装次数
        plugin.install_count += 1  # type: ignore

        await self.session.commit()
        await self.session.refresh(installed_plugin)

        # 加载插件详情
        await self.session.refresh(installed_plugin)
        response = InstalledPluginResponse.model_validate(installed_plugin)
        response.plugin = PluginResponse.model_validate(plugin)

        return response

    async def get_installed_plugin(
        self, installed_plugin_id: UUID, workspace_id: UUID
    ) -> InstalledPluginResponse:
        """获取已安装插件详情

        Args:
            installed_plugin_id: 安装记录ID
            workspace_id: 工作空间ID

        Returns:
            已安装插件详情

        Raises:
            InstalledPluginNotFoundError: 已安装插件不存在
        """
        stmt = select(InstalledPlugin).where(
            InstalledPlugin.id == installed_plugin_id,  # type: ignore
            InstalledPlugin.workspace_id == workspace_id,  # type: ignore
            InstalledPlugin.is_deleted.is_(False),  # type: ignore
        )
        result = await self.session.execute(stmt)
        installed_plugin = result.scalar_one_or_none()

        if not installed_plugin:
            raise InstalledPluginNotFoundError(
                f'Installed plugin {installed_plugin_id} not found in workspace {workspace_id}'
            )

        # 加载插件详情
        plugin_stmt = select(Plugin).where(Plugin.id == installed_plugin.plugin_id)  # type: ignore
        plugin_result = await self.session.execute(plugin_stmt)
        plugin = plugin_result.scalar_one_or_none()

        response = InstalledPluginResponse.model_validate(installed_plugin)
        if plugin:
            response.plugin = PluginResponse.model_validate(plugin)

        return response

    async def list_installed_plugins(
        self,
        workspace_id: UUID,
        skip: int = 0,
        limit: int = 100,
        is_enabled: Optional[bool] = None,
    ) -> tuple[list[InstalledPluginResponse], int]:
        """获取工作空间已安装插件列表

        Args:
            workspace_id: 工作空间ID
            skip: 跳过的记录数
            limit: 返回的记录数
            is_enabled: 是否启用过滤

        Returns:
            已安装插件列表和总数
        """
        # 构建查询条件
        conditions = [
            InstalledPlugin.workspace_id == workspace_id,  # type: ignore
            InstalledPlugin.is_deleted.is_(False),  # type: ignore
        ]

        if is_enabled is not None:
            conditions.append(InstalledPlugin.is_enabled.is_(is_enabled))  # type: ignore

        # 查询总数
        count_stmt = select(func.count()).select_from(InstalledPlugin).where(*conditions)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # 查询已安装插件列表
        stmt = (
            select(InstalledPlugin)
            .where(*conditions)
            .order_by(InstalledPlugin.installed_at.desc())  # type: ignore
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        installed_plugins = result.scalars().all()

        # 加载插件详情
        responses = []
        for installed_plugin in installed_plugins:
            plugin_stmt = select(Plugin).where(Plugin.id == installed_plugin.plugin_id)  # type: ignore
            plugin_result = await self.session.execute(plugin_stmt)
            plugin = plugin_result.scalar_one_or_none()

            response = InstalledPluginResponse.model_validate(installed_plugin)
            if plugin:
                response.plugin = PluginResponse.model_validate(plugin)
            responses.append(response)

        return responses, total

    async def update_installed_plugin(
        self,
        installed_plugin_id: UUID,
        workspace_id: UUID,
        plugin_data: InstalledPluginUpdate,
    ) -> InstalledPluginResponse:
        """更新已安装插件配置

        Args:
            installed_plugin_id: 安装记录ID
            workspace_id: 工作空间ID
            plugin_data: 更新数据

        Returns:
            更新后的已安装插件

        Raises:
            InstalledPluginNotFoundError: 已安装插件不存在
        """
        stmt = select(InstalledPlugin).where(
            InstalledPlugin.id == installed_plugin_id,  # type: ignore
            InstalledPlugin.workspace_id == workspace_id,  # type: ignore
            InstalledPlugin.is_deleted.is_(False),  # type: ignore
        )
        result = await self.session.execute(stmt)
        installed_plugin = result.scalar_one_or_none()

        if not installed_plugin:
            raise InstalledPluginNotFoundError(
                f'Installed plugin {installed_plugin_id} not found in workspace {workspace_id}'
            )

        # 更新字段
        update_data = plugin_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(installed_plugin, field, value)

        await self.session.commit()
        await self.session.refresh(installed_plugin)

        # 加载插件详情
        plugin_stmt = select(Plugin).where(Plugin.id == installed_plugin.plugin_id)  # type: ignore
        plugin_result = await self.session.execute(plugin_stmt)
        plugin = plugin_result.scalar_one_or_none()

        response = InstalledPluginResponse.model_validate(installed_plugin)
        if plugin:
            response.plugin = PluginResponse.model_validate(plugin)

        return response

    async def uninstall_plugin(self, installed_plugin_id: UUID, workspace_id: UUID) -> None:
        """卸载插件（软删除）

        Args:
            installed_plugin_id: 安装记录ID
            workspace_id: 工作空间ID

        Raises:
            InstalledPluginNotFoundError: 已安装插件不存在
        """
        stmt = select(InstalledPlugin).where(
            InstalledPlugin.id == installed_plugin_id,  # type: ignore
            InstalledPlugin.workspace_id == workspace_id,  # type: ignore
            InstalledPlugin.is_deleted.is_(False),  # type: ignore
        )
        result = await self.session.execute(stmt)
        installed_plugin = result.scalar_one_or_none()

        if not installed_plugin:
            raise InstalledPluginNotFoundError(
                f'Installed plugin {installed_plugin_id} not found in workspace {workspace_id}'
            )

        # 软删除
        installed_plugin.is_deleted = True  # type: ignore
        await self.session.commit()
