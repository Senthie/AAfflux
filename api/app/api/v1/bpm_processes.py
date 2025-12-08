"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-04 09:50:20
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-08 03:30:14
FilePath: /api/app/api/v1/bpm_processes.py
Description: 流程 API

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.schemas.bpm_process_schemas import (
    ProcessInstanceCreate,
    ProcessInstanceResponse,
)
from app.services.bpm_process_service import ProcessService

router = APIRouter()


# TODO: 实现依赖注入
def get_session():
    """获取数据库会话（待实现）"""
    pass


def get_current_user():
    """获取当前用户（待实现）"""
    pass


@router.post('/start', response_model=ProcessInstanceResponse)
async def start_process(
    request: ProcessInstanceCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """启动流程实例"""
    service = ProcessService(session)

    instance = await service.start_process(
        process_key=request.process_key,
        workspace_id=current_user.workspace_id,
        user_id=current_user.id,
        variables=request.variables,
        business_key=request.business_key,
        business_type=request.business_type,
    )

    return instance


@router.get('/{instance_id}', response_model=ProcessInstanceResponse)
async def get_process_instance(
    instance_id: UUID,
    session: Session = Depends(get_session),
):
    """
    description: 获取流程实例详情
    param {UUID} instance_id
    param {Session} session
    return {*}
    """
    service = ProcessService(session)
    instance = await service.get_process_instance(instance_id)

    if not instance:
        raise HTTPException(status_code=404, detail='Process instance not found')

    return instance


@router.post('/{instance_id}/cancel')
async def cancel_process(
    instance_id: UUID,
    reason: str,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    description: 取消流程
    param {UUID} instance_id
    param {str} reason
    param {Session} session
    param {*} current_user
    return {*}
    """
    service = ProcessService(session)
    await service.cancel_process(instance_id, current_user.id, reason)

    return {'message': 'Process cancelled successfully'}
