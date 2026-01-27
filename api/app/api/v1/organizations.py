"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/api/v1/organizations.py
Description: 组织管理API端点

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.middleware.auth import get_current_user
from app.models.auth.user import UserEntity
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationStatsResponse,
    OrganizationUpdate,
)
from app.services.organization_service import OrganizationService

router = APIRouter(prefix='/organizations', tags=['Organization Management'])

# 依赖注入定义
DbSession = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[UserEntity, Depends(get_current_user)]


def get_organization_service(session: DbSession) -> OrganizationService:
    """获取企业服务实例"""
    return OrganizationService(session)


OrganizationServiceDep = Annotated[OrganizationService, Depends(get_organization_service)]


@router.post(
    '',
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary='创建企业',
)
async def create_organization(
    data: OrganizationCreate,
    current_user: CurrentUser,
    service: OrganizationServiceDep,
) -> OrganizationResponse:
    """创建新企业"""
    organization = await service.create_organization(data, current_user.id)
    return OrganizationResponse.model_validate(organization)


@router.get(
    '/{organization_id}',
    response_model=OrganizationResponse,
    summary='获取企业信息',
)
async def get_organization(
    organization_id: UUID,
    service: OrganizationServiceDep,
) -> OrganizationResponse:
    """获取指定企业信息"""
    organization = await service.get_organization(organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Organization not found')
    return OrganizationResponse.model_validate(organization)


@router.put(
    '/{organization_id}',
    response_model=OrganizationResponse,
    summary='更新企业信息',
)
async def update_organization(
    organization_id: UUID,
    data: OrganizationUpdate,
    service: OrganizationServiceDep,
) -> OrganizationResponse:
    """更新企业信息"""
    organization = await service.update_organization(organization_id, data)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Organization not found')
    return OrganizationResponse.model_validate(organization)


@router.delete(
    '/{organization_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='删除企业',
)
async def delete_organization(
    organization_id: UUID,
    service: OrganizationServiceDep,
) -> None:
    """删除企业（级联删除团队和工作空间）"""
    success = await service.delete_organization(organization_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Organization not found')


@router.get(
    '/{organization_id}/teams',
    summary='获取企业团队列表',
)
async def get_organization_teams(
    organization_id: UUID,
    service: OrganizationServiceDep,
):
    """获取企业下的所有团队"""
    teams = await service.get_organization_teams(organization_id)
    return teams


@router.get(
    '/{organization_id}/stats',
    response_model=OrganizationStatsResponse,
    summary='获取企业统计信息',
)
async def get_organization_stats(
    organization_id: UUID,
    service: OrganizationServiceDep,
) -> OrganizationStatsResponse:
    """获取企业使用统计"""
    stats = await service.get_usage_stats(organization_id)
    return OrganizationStatsResponse(organization_id=organization_id, **stats)
