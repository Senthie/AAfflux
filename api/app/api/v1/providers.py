"""
Author: Senthie seemoon2077@gmail.com
Date: 2026-01-08 14:12:08
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:34:27
FilePath: /api/app/api/v1/providers.py
Description:LLM提供商管理API端点

本模块实现了LLM提供商配置的REST API接口。

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_session
from app.schemas.provider import (
    LLMCallRequest,
    LLMCallResponse,
    LLMModelInfo,
    LLMProviderCreate,
    LLMProviderListResponse,
    LLMProviderResponse,
    LLMProviderUpdate,
    LLMProviderValidationRequest,
    LLMProviderValidationResponse,
)
from app.services.llm_provider_service import LLMProviderService
from app.utils.llm import LLMError

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/providers', tags=['LLM Providers'])


def get_llm_provider_service(session: AsyncSession = Depends(get_session)) -> LLMProviderService:
    """获取LLM提供商服务实例"""
    return LLMProviderService(session)


# TODO: 添加认证和权限检查依赖
def get_current_user_context():
    """获取当前用户上下文（临时实现）"""
    # 这里应该从JWT令牌中解析用户信息和工作空间信息
    # 临时返回固定值用于测试
    from uuid import uuid4

    return {'user_id': uuid4(), 'workspace_id': uuid4()}


@router.post('/', response_model=LLMProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    provider_data: LLMProviderCreate,
    service: LLMProviderService = Depends(get_llm_provider_service),
    context=Depends(get_current_user_context),
):
    """创建LLM提供商配置

    创建新的LLM提供商配置，包括API密钥验证。
    """
    try:
        return await service.create_provider(
            provider_data=provider_data,
            workspace_id=context['workspace_id'],
            created_by=context['user_id'],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None
    except Exception as e:
        logger.error(f'Failed to create LLM provider: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error'
        ) from None


@router.get('/', response_model=LLMProviderListResponse)
async def list_providers(
    skip: int = Query(0, ge=0, description='跳过的记录数'),
    limit: int = Query(100, ge=1, le=1000, description='返回的记录数'),
    service: LLMProviderService = Depends(get_llm_provider_service),
    context=Depends(get_current_user_context),
):
    """获取LLM提供商列表

    返回当前工作空间的所有LLM提供商配置。
    """
    try:
        providers = await service.list_providers(
            workspace_id=context['workspace_id'], skip=skip, limit=limit
        )

        return LLMProviderListResponse(
            providers=providers,
            total=len(providers),  # TODO: 实现真实的总数统计
            page=skip // limit + 1,
            page_size=limit,
        )
    except Exception as e:
        logger.error(f'Failed to list LLM providers: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error'
        ) from None


@router.get('/{provider_id}', response_model=LLMProviderResponse)
async def get_provider(
    provider_id: UUID,
    service: LLMProviderService = Depends(get_llm_provider_service),
    context=Depends(get_current_user_context),
):
    """获取LLM提供商详情

    根据ID获取特定的LLM提供商配置。
    """
    try:
        return await service.get_provider(
            provider_id=provider_id, workspace_id=context['workspace_id']
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None
    except Exception as e:
        logger.error(f'Failed to get LLM provider: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error'
        ) from None


@router.put('/{provider_id}', response_model=LLMProviderResponse)
async def update_provider(
    provider_id: UUID,
    provider_data: LLMProviderUpdate,
    service: LLMProviderService = Depends(get_llm_provider_service),
    context=Depends(get_current_user_context),
):
    """更新LLM提供商配置

    更新指定的LLM提供商配置，如果更新API密钥会重新验证。
    """
    try:
        return await service.update_provider(
            provider_id=provider_id,
            provider_data=provider_data,
            workspace_id=context['workspace_id'],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None
    except Exception as e:
        logger.error(f'Failed to update LLM provider: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error'
        ) from None


@router.delete('/{provider_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: UUID,
    service: LLMProviderService = Depends(get_llm_provider_service),
    context=Depends(get_current_user_context),
):
    """删除LLM提供商配置

    删除指定的LLM提供商配置。如果配置被工作流引用，将拒绝删除。
    """
    try:
        await service.delete_provider(provider_id=provider_id, workspace_id=context['workspace_id'])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None
    except Exception as e:
        logger.error(f'Failed to delete LLM provider: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error'
        ) from None


@router.get('/{provider_id}/models', response_model=List[LLMModelInfo])
async def get_provider_models(
    provider_id: UUID,
    service: LLMProviderService = Depends(get_llm_provider_service),
    context=Depends(get_current_user_context),
):
    """获取提供商支持的模型列表

    返回指定LLM提供商支持的所有模型信息。
    """
    try:
        return await service.get_provider_models(
            provider_id=provider_id, workspace_id=context['workspace_id']
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None
    except LLMError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f'Failed to fetch models: {e.message}'
        ) from None
    except Exception as e:
        logger.error(f'Failed to get provider models: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error'
        ) from None


@router.post('/call', response_model=LLMCallResponse)
async def call_llm(
    request: LLMCallRequest,
    service: LLMProviderService = Depends(get_llm_provider_service),
    context=Depends(get_current_user_context),
):
    """调用LLM生成响应

    使用指定的LLM提供商和模型生成响应。
    """
    try:
        return await service.call_llm(request=request, workspace_id=context['workspace_id'])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None
    except LLMError as e:
        # 根据错误类型返回不同的HTTP状态码
        if 'authentication' in e.message.lower():
            status_code = status.HTTP_401_UNAUTHORIZED
        elif 'rate limit' in e.message.lower():
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif 'timeout' in e.message.lower():
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
        else:
            status_code = status.HTTP_502_BAD_GATEWAY

        raise HTTPException(
            status_code=status_code, detail=f'LLM call failed: {e.message}'
        ) from None
    except Exception as e:
        logger.error(f'Failed to call LLM: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error'
        ) from None


@router.post('/validate', response_model=LLMProviderValidationResponse)
async def validate_provider(
    request: LLMProviderValidationRequest,
    service: LLMProviderService = Depends(get_llm_provider_service),
):
    """验证LLM提供商配置

    验证API密钥是否有效，并返回可用的模型列表。
    """
    try:
        return await service.validate_api_key(request)
    except Exception as e:
        logger.error(f'Failed to validate provider: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error'
        ) from None
