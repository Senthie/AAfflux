"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-22 10:29:13
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:20
FilePath: /api/app/api/v1/app_runtime.py
Description: 运行时api端点 供外部调用

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_session
from app.schemas.application import ApplicationRuntimeRequest, ApplicationRuntimeResponse
from app.schemas.execution import ExecutionRecordCreate
from app.services.application_service import ApplicationService
from app.services.execution_record_service import ExecutionRecordService

router = APIRouter(prefix='/runtime', tags=['runtime'])


async def get_application_by_api_key(
    authorization: str = Header(..., description='API密钥'),
    session: AsyncSession = Depends(get_session),
):
    """通过API密钥获取应用"""
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='无效的授权头格式')

    api_key = authorization.replace('Bearer ', '')

    service = ApplicationService(session)
    application = await service.get_application_by_api_key(api_key)

    if not application:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='无效的API密钥')

    if not application.is_published:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='应用未发布')

    return application


@router.post('/apps/{application_id}/execute', response_model=ApplicationRuntimeResponse)
async def execute_application(
    application_id: UUID,
    request: ApplicationRuntimeRequest,
    application=Depends(get_application_by_api_key),
    session: AsyncSession = Depends(get_session),
):
    """执行应用"""
    # 验证应用ID是否匹配
    if application.id != application_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='API密钥与应用不匹配')

    # 创建执行记录
    execution_service = ExecutionRecordService(session)
    execution_data = ExecutionRecordCreate(
        workflow_id=application.workflow_id, inputs=request.inputs
    )

    execution_record = await execution_service.create_execution_record(execution_data)

    # TODO: 这里应该触发工作流执行
    # 目前先返回创建的执行记录

    return ApplicationRuntimeResponse(
        execution_id=execution_record.id,
        outputs=execution_record.outputs,
        status=execution_record.status,
        started_at=execution_record.started_at,
        completed_at=execution_record.completed_at,
        duration_ms=execution_record.duration_ms,
        error=execution_record.error,
    )


@router.get(
    '/apps/{application_id}/executions/{execution_id}', response_model=ApplicationRuntimeResponse
)
async def get_execution_status(
    application_id: UUID,
    execution_id: UUID,
    application=Depends(get_application_by_api_key),
    session: AsyncSession = Depends(get_session),
):
    """获取执行状态"""
    # 验证应用ID是否匹配
    if application.id != application_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='API密钥与应用不匹配')

    # 获取执行记录
    execution_service = ExecutionRecordService(session)
    execution_record = await execution_service.get_execution_record(execution_id)

    if not execution_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='执行记录不存在')

    # 验证执行记录是否属于该应用的工作流
    if execution_record.workflow_id != application.workflow_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='执行记录不属于该应用')

    return ApplicationRuntimeResponse(
        execution_id=execution_record.id,
        outputs=execution_record.outputs,
        status=execution_record.status,
        started_at=execution_record.started_at,
        completed_at=execution_record.completed_at,
        duration_ms=execution_record.duration_ms,
        error=execution_record.error,
    )


@router.get('/apps/{application_id}/info')
async def get_application_info(
    application_id: UUID, application=Depends(get_application_by_api_key)
):
    """获取应用信息（公开接口）"""
    # 验证应用ID是否匹配
    if application.id != application_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='API密钥与应用不匹配')

    return {
        'id': application.id,
        'name': application.name,
        'description': application.description,
        'api_endpoint': application.api_endpoint,
        'is_published': application.is_published,
    }
