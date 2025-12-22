"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-22 10:28:40
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-22 14:39:25
FilePath: : AAfflux: api: app: api: v1: applications.py
Description:应用管理api端点
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.dependencies import get_session, get_current_user
from app.models.auth.user import User
from app.services.application_service import ApplicationService
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationListItem,
    ApplicationQuery,
    ApplicationPublishRequest,
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyResponse,
    APIKeyListResponse
)
from math import ceil

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """创建应用"""
    service = ApplicationService(session)
    application = service.create_application(data, current_user.id)
    return application


@router.get("", response_model=ApplicationListResponse)
async def list_applications(
    name: str = Query(None, description="应用名称"),
    is_published: bool = Query(None, description="是否发布"),
    workflow_id: UUID = Query(None, description="工作流ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """分页查询应用列表"""
    service = ApplicationService(session)

    query = ApplicationQuery(
        name=name,
        is_published=is_published,
        workflow_id=workflow_id,
        page=page,
        page_size=page_size
    )

    applications, total = service.list_applications(query, current_user.id)

    items = [
        ApplicationListItem(
            id=app.id,
            name=app.name,
            description=app.description,
            workflow_id=app.workflow_id,
            is_published=app.is_published,
            api_endpoint=app.api_endpoint,
            created_at=app.created_at,
            updated_at=app.updated_at
        )
        for app in applications
    ]

    return ApplicationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size)
    )


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """获取单个应用详情"""
    service = ApplicationService(session)
    application = service.get_application(application_id)

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="应用不存在"
        )

    return application


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: UUID,
    data: ApplicationUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """更新应用"""
    service = ApplicationService(session)
    application = service.update_application(application_id, data, current_user.id)

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="应用不存在"
        )

    return application


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """删除应用"""
    service = ApplicationService(session)
    success = service.delete_application(application_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="应用不存在"
        )

    return None


@router.post("/{application_id}/publish", response_model=ApplicationResponse)
async def publish_application(
    application_id: UUID,
    data: ApplicationPublishRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """发布/取消发布应用"""
    service = ApplicationService(session)
    application = service.publish_application(
        application_id,
        data.is_published,
        current_user.id
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="应用不存在"
        )

    return application


@router.post("/{application_id}/api-keys", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    application_id: UUID,
    data: APIKeyCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """为应用创建API密钥"""
    service = ApplicationService(session)
    api_key_data = service.create_api_key(application_id, data, current_user.id)

    if not api_key_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="应用不存在"
        )

    return api_key_data


@router.get("/{application_id}/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    application_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """获取应用的API密钥列表"""
    service = ApplicationService(session)

    # 验证应用是否存在
    application = service.get_application(application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="应用不存在"
        )

    api_keys = service.list_api_keys(application_id)

    items = [
        APIKeyResponse(
            id=key.id,
            name=key.name,
            key_prefix=key.key_prefix,
            created_at=key.created_at,
            expires_at=key.expires_at,
            last_used_at=key.last_used_at,
            is_active=key.is_active
        )
        for key in api_keys
    ]

    return APIKeyListResponse(
        items=items,
        total=len(items)
    )


@router.delete("/{application_id}/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    application_id: UUID,
    api_key_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """撤销API密钥"""
    service = ApplicationService(session)
    success = service.revoke_api_key(application_id, api_key_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )

    return None
