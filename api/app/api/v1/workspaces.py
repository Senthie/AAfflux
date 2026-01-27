"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-10 17:45:21
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:35:55
FilePath: /api/app/api/v1/workspaces.py
Description: Description:工作空间管理 API 端点"

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.response import ResponseSchemaModel
from app.middleware.auth import get_current_user
from app.models.auth.user import UserEntity
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceDeleteResponse,
    WorkspaceResourceMove,
    WorkspaceResourcesResponse,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix='/workspaces', tags=['Workspace Management'])

# 依赖注入定义
DbSession = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[UserEntity, Depends(get_current_user)]


def get_workspace_service(session: DbSession) -> WorkspaceService:
    """获取工作空间服务实例"""
    return WorkspaceService(session)


WorkspaceServiceDep = Annotated[WorkspaceService, Depends(get_workspace_service)]


@router.get(
    '',
    response_model=ResponseSchemaModel[list[WorkspaceResponse]],
    summary='获取用户可访问的工作空间',
)
async def list_user_workspaces(
    current_user: CurrentUser,
    service: WorkspaceServiceDep,
) -> ResponseSchemaModel[list[WorkspaceResponse]]:
    """获取当前用户可访问的所有工作空间"""
    res = await service.get_user_workspaces(current_user.id)
    return res


@router.post(
    '',
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary='创建工作空间',
)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: CurrentUser,
    service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    """创建新工作空间"""
    workspace = await service.create_workspace(data, current_user.id)
    return WorkspaceResponse.model_validate(workspace)


@router.get(
    '/{workspace_id}',
    response_model=WorkspaceResponse,
    summary='获取工作空间信息',
)
async def get_workspace(
    workspace_id: UUID,
    service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    """获取指定工作空间信息"""
    workspace = await service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Workspace not found')
    return WorkspaceResponse.model_validate(workspace)


@router.put(
    '/{workspace_id}',
    response_model=WorkspaceResponse,
    summary='更新工作空间信息',
)
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    """更新工作空间信息"""
    workspace = await service.update_workspace(workspace_id, data)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Workspace not found')
    return WorkspaceResponse.model_validate(workspace)


@router.delete(
    '/{workspace_id}',
    response_model=WorkspaceDeleteResponse,
    summary='删除工作空间',
)
async def delete_workspace(
    workspace_id: UUID,
    service: WorkspaceServiceDep,
) -> WorkspaceDeleteResponse:
    """删除工作空间（级联删除资源）"""
    success = await service.delete_workspace(workspace_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Workspace not found')

    return WorkspaceDeleteResponse(
        success=True, message='Workspace deleted successfully', workspace_id=workspace_id
    )


@router.get(
    '/{workspace_id}/resources',
    response_model=WorkspaceResourcesResponse,
    summary='获取工作空间资源',
)
async def get_workspace_resources(
    workspace_id: UUID,
    service: WorkspaceServiceDep,
) -> WorkspaceResourcesResponse:
    """获取工作空间下的所有资源"""
    resources = await service.list_resources(workspace_id)
    return WorkspaceResourcesResponse(workspace_id=workspace_id, **resources)


@router.post(
    '/resources/move',
    summary='移动资源',
)
async def move_resource(
    data: WorkspaceResourceMove,
    service: WorkspaceServiceDep,
) -> dict:
    """移动资源到其他工作空间"""
    success = await service.move_resource(
        data.resource_id, data.resource_type, data.target_workspace_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Failed to move resource'
        )

    return {'success': True, 'message': 'Resource moved successfully'}


@router.get(
    '/teams/{team_id}/workspaces',
    response_model=list[WorkspaceResponse],
    summary='获取团队工作空间列表',
)
async def get_team_workspaces(
    team_id: UUID,
    service: WorkspaceServiceDep,
) -> list[WorkspaceResponse]:
    """获取团队下的所有工作空间"""
    workspaces = await service.get_team_workspaces(team_id)
    return [WorkspaceResponse.model_validate(ws) for ws in workspaces]
