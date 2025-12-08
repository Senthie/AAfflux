"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-04 09:50:20
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-08 03:29:16
FilePath: /api/app/api/v1/bpm_tasks.py
Description: 任务 API

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.schemas.bpm_task_schemas import TaskCompleteRequest, TaskResponse
from app.services.bpm_task_service import TaskService

router = APIRouter()


def get_session():
    """获取数据库会话（待实现）"""
    pass


def get_current_user():
    """获取当前用户（待实现）"""
    pass


@router.get('/my-tasks', response_model=List[TaskResponse])
async def get_my_tasks(
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """获取我的待办任务"""
    service = TaskService(session)
    tasks = await service.get_my_tasks(
        user_id=current_user.id,
        workspace_id=current_user.workspace_id,
    )
    return tasks


@router.post('/{task_id}/claim')
async def claim_task(
    task_id: UUID,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """认领任务"""
    service = TaskService(session)
    await service.claim_task(task_id, current_user.id)
    return {'message': 'Task claimed successfully'}


@router.post('/{task_id}/complete')
async def complete_task(
    task_id: UUID,
    request: TaskCompleteRequest,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """完成任务"""
    service = TaskService(session)
    await service.complete_task(
        task_id=task_id,
        user_id=current_user.id,
        result=request.result,
        comment=request.comment,
    )
    return {'message': 'Task completed successfully'}


@router.get('/{task_id}', response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    session: Session = Depends(get_session),
):
    """获取任务详情"""
    service = TaskService(session)
    task = await service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail='Task not found')

    return task
