"""
插件管理 API 端点

本模块提供插件和已安装插件的 RESTful API 接口。
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.response import ResponseModel, ResponseSchemaModel, response_base
from app.enums.custom_response_code_enum import CustomResponseCodeEnum
from app.middleware.auth import get_current_user
from app.models.auth.user import UserEntity
from app.schemas.page_schemas import PageRequest, PageResponse
from app.schemas.plugin import (
    InstalledPluginCreate,
    InstalledPluginDeleteResponse,
    InstalledPluginListResponse,
    InstalledPluginResponse,
    InstalledPluginUpdate,
    PluginCreate,
    PluginDeleteResponse,
    PluginResponse,
    PluginUpdate,
)
from app.services.plugin_service import (
    InstalledPluginNotFoundError,
    PluginAlreadyExistsError,
    PluginNotFoundError,
    PluginService,
)

router = APIRouter(prefix='/plugins', tags=['Plugin Management'])

# Dependency injection definitions
DbSession = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[UserEntity, Depends(get_current_user)]


# ============================================================================
# Plugin Endpoints
# ============================================================================


@router.post(
    '/',
    summary='创建插件',
)
async def create_plugin(
    plugin_data: PluginCreate,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[PluginResponse] | ResponseModel:
    """
    创建新插件。

    Args:
        plugin_data: 插件创建数据
        current_user: 当前认证用户
        session: 数据库会话

    Returns:
        创建的插件
    """
    service = PluginService(session)

    try:
        plugin = await service.create_plugin(plugin_data)
        return response_base.success(data=plugin)
    except PluginAlreadyExistsError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.BAD_REQUEST,
            data=str(e),
        )
    except Exception as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.INTERNAL_SERVER_ERROR,
            data=f'Failed to create plugin: {str(e)}',
        )


@router.post(
    '/list',
    summary='获取插件列表',
)
async def list_plugins(
    current_user: CurrentUser,
    session: DbSession,
    page_req: PageRequest,
    category: Optional[str] = Query(None, description='插件分类过滤'),
    plugin_type: Optional[str] = Query(None, description='插件类型过滤'),
    is_active: Optional[bool] = Query(None, description='是否激活过滤'),
    is_verified: Optional[bool] = Query(None, description='是否已验证过滤'),
) -> ResponseSchemaModel[PageResponse[PluginResponse]]:
    """
    获取插件列表，支持多种过滤条件。

    Args:
        current_user: now login user
        session: 数据库会话
        skip: 跳过的记录数
        limit: 返回的记录数
        category: 插件分类过滤
        plugin_type: 插件类型过滤
        is_active: 是否激活过滤
        is_verified: 是否已验证过滤

    Returns:
        插件列表和总数
    """
    service = PluginService(session)

    res = await service.list_plugins(
        page_req,
        category=category,
        plugin_type=plugin_type,
        is_active=is_active,
        is_verified=is_verified,
    )

    return response_base.success(data=res)


@router.get(
    '/{plugin_id}',
    summary='获取插件详情',
)
async def get_plugin(
    plugin_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[PluginResponse] | ResponseModel:
    """
    获取插件详细信息。

    Args:
        plugin_id: 插件ID
        current_user: 当前认证用户
        session: 数据库会话

    Returns:
        插件详情
    """
    service = PluginService(session)

    try:
        plugin = await service.get_plugin(plugin_id)
        return response_base.success(data=plugin)
    except PluginNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )


@router.put(
    '/{plugin_id}',
    summary='更新插件',
)
async def update_plugin(
    plugin_id: UUID,
    plugin_data: PluginUpdate,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[PluginResponse] | ResponseModel:
    """
    更新插件信息。

    Args:
        plugin_id: 插件ID
        plugin_data: 插件更新数据
        current_user: 当前认证用户
        session: 数据库会话

    Returns:
        更新后的插件
    """
    service = PluginService(session)

    try:
        plugin = await service.update_plugin(plugin_id, plugin_data)
        return response_base.success(data=plugin)
    except PluginNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )


@router.delete(
    '/{plugin_id}',
    summary='删除插件',
)
async def delete_plugin(
    plugin_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[PluginDeleteResponse] | ResponseModel:
    """
    删除插件（软删除）。

    Args:
        plugin_id: 插件ID
        current_user: 当前认证用户
        session: 数据库会话

    Returns:
        删除确认
    """
    service = PluginService(session)

    try:
        await service.delete_plugin(plugin_id)
        return response_base.success(
            data=PluginDeleteResponse(
                success=True,
                message='Plugin deleted successfully',
                plugin_id=plugin_id,
            )
        )
    except PluginNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )


# ============================================================================
# Installed Plugin Endpoints
# ============================================================================


@router.post(
    '/install',
    summary='安装插件到工作空间',
)
async def install_plugin(
    plugin_data: InstalledPluginCreate,
    workspace_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[InstalledPluginResponse] | ResponseModel:
    """
    安装插件到指定工作空间。

    Args:
        plugin_data: 安装插件数据
        workspace_id: 工作空间ID
        current_user: 当前认证用户
        session: 数据库会话

    Returns:
        已安装插件
    """
    service = PluginService(session)

    try:
        installed_plugin = await service.install_plugin(
            workspace_id=workspace_id,
            user=current_user,
            plugin_data=plugin_data,
        )
        return response_base.success(data=installed_plugin)
    except PluginNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )
    except Exception as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.INTERNAL_SERVER_ERROR,
            data=f'Failed to install plugin: {str(e)}',
        )


@router.get(
    '/installed',
    summary='获取工作空间已安装插件列表',
)
async def list_installed_plugins(
    workspace_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    skip: int = Query(0, ge=0, description='跳过的记录数'),
    limit: int = Query(100, ge=1, le=1000, description='返回的记录数'),
    is_enabled: Optional[bool] = Query(None, description='是否启用过滤'),
) -> ResponseSchemaModel[InstalledPluginListResponse]:
    """
    获取工作空间已安装插件列表。

    Args:
        workspace_id: 工作空间ID
        current_user: 当前认证用户
        session: 数据库会话
        skip: 跳过的记录数
        limit: 返回的记录数
        is_enabled: 是否启用过滤

    Returns:
        已安装插件列表和总数
    """
    service = PluginService(session)

    installed_plugins, total = await service.list_installed_plugins(
        workspace_id=workspace_id,
        skip=skip,
        limit=limit,
        is_enabled=is_enabled,
    )

    return response_base.success(
        data=InstalledPluginListResponse(
            installed_plugins=installed_plugins,
            total=total,
            page=skip // limit + 1,
            page_size=limit,
        )
    )


@router.get(
    '/installed/{installed_plugin_id}',
    summary='获取已安装插件详情',
)
async def get_installed_plugin(
    installed_plugin_id: UUID,
    workspace_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[InstalledPluginResponse] | ResponseModel:
    """
    获取已安装插件详细信息。

    Args:
        installed_plugin_id: 安装记录ID
        workspace_id: 工作空间ID
        current_user: 当前认证用户
        session: 数据库会话

    Returns:
        已安装插件详情
    """
    service = PluginService(session)

    try:
        installed_plugin = await service.get_installed_plugin(installed_plugin_id, workspace_id)
        return response_base.success(data=installed_plugin)
    except InstalledPluginNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )


@router.put(
    '/installed/{installed_plugin_id}',
    summary='更新已安装插件配置',
)
async def update_installed_plugin(
    installed_plugin_id: UUID,
    workspace_id: UUID,
    plugin_data: InstalledPluginUpdate,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[InstalledPluginResponse] | ResponseModel:
    """
    更新已安装插件的配置。

    Args:
        installed_plugin_id: 安装记录ID
        workspace_id: 工作空间ID
        plugin_data: 更新数据
        current_user: 当前认证用户
        session: 数据库会话

    Returns:
        更新后的已安装插件
    """
    service = PluginService(session)

    try:
        installed_plugin = await service.update_installed_plugin(
            installed_plugin_id, workspace_id, plugin_data
        )
        return response_base.success(data=installed_plugin)
    except InstalledPluginNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )


@router.delete(
    '/installed/{installed_plugin_id}',
    summary='卸载插件',
)
async def uninstall_plugin(
    installed_plugin_id: UUID,
    workspace_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[InstalledPluginDeleteResponse] | ResponseModel:
    """
    从工作空间卸载插件（软删除）。

    Args:
        installed_plugin_id: 安装记录ID
        workspace_id: 工作空间ID
        current_user: 当前认证用户
        session: 数据库会话

    Returns:
        卸载确认
    """
    service = PluginService(session)

    try:
        await service.uninstall_plugin(installed_plugin_id, workspace_id)
        return response_base.success(
            data=InstalledPluginDeleteResponse(
                success=True,
                message='Plugin uninstalled successfully',
                installed_plugin_id=installed_plugin_id,
            )
        )
    except InstalledPluginNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )
