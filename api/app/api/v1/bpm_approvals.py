"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-04 09:50:20
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-22 14:39:38
FilePath: : AAfflux: api: app: api: v1: bpm_approvals.py
Description: 审批 API

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_current_user, get_session
from app.schemas.bpm_approval_schemas import ApprovalRequest, ApprovalResponse
from app.services.bpm_approval_service import ApprovalService
from app.services.bpm_task_service import TaskService

router = APIRouter()


@router.post('/{task_id}/approve', response_model=ApprovalResponse)
async def approve_task(
    task_id: UUID,
    request: ApprovalRequest,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    description: 审批通过
    param {UUID} task_id
    param {ApprovalRequest} request
    param {Session} session
    param {*} current_user
    return {*}
    """
    approval_service = ApprovalService(session)

    # 创建审批记录
    approval = await approval_service.approve_task(
        task_id=task_id,
        user_id=current_user.id,
        user_name=current_user.name,
        comment=request.comment,
        workspace_id=current_user.workspace_id,
    )

    # 完成任务
    task_service = TaskService(session)
    await task_service.complete_task(
        task_id=task_id,
        user_id=current_user.id,
        result={'approved': True},
        comment=request.comment,
    )

    return approval


@router.post('/{task_id}/reject', response_model=ApprovalResponse)
async def reject_task(
    task_id: UUID,
    request: ApprovalRequest,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    description: 审批拒绝
    param {UUID} task_id
    param {ApprovalRequest} request
    param {Session} session
    param {*} current_user
    return {*}
    """
    approval_service = ApprovalService(session)

    approval = await approval_service.reject_task(
        task_id=task_id,
        user_id=current_user.id,
        user_name=current_user.name,
        comment=request.comment or '拒绝',
        workspace_id=current_user.workspace_id,
    )

    # 完成任务
    task_service = TaskService(session)
    await task_service.complete_task(
        task_id=task_id,
        user_id=current_user.id,
        result={'approved': False},
        comment=request.comment,
    )

    return approval
