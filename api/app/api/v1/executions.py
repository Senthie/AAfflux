"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/api/v1/executions.py
Description: 执行记录API端点

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from math import ceil
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_current_user, get_session
from app.models.auth.user import UserEntity
from app.schemas.execution import (
    ExecutionRecordListItem,
    ExecutionRecordListResponse,
    ExecutionRecordQuery,
    ExecutionRecordResponse,
    ExecutionStatistics,
    NodeExecutionResultResponse,
)
from app.services.execution_record_service import ExecutionRecordService

router = APIRouter(prefix='/executions', tags=['executions'])


@router.get('', response_model=ExecutionRecordListResponse)
async def list_execution_records(
    workflow_id: UUID = Query(None, description='工作流ID'),
    status: str = Query(None, description='执行状态'),
    start_date: str = Query(None, description='开始日期'),
    end_date: str = Query(None, description='结束日期'),
    page: int = Query(1, ge=1, description='页码'),
    page_size: int = Query(20, ge=1, le=100, description='每页数量'),
    session: AsyncSession = Depends(get_session),
    current_user: UserEntity = Depends(get_current_user),
):
    """分页查询执行记录列表"""
    service = ExecutionRecordService(session)

    query = ExecutionRecordQuery(
        workflow_id=workflow_id, status=status, page=page, page_size=page_size
    )

    records, total = await service.list_execution_records(query)

    items = [
        ExecutionRecordListItem(
            id=record.id,
            workflow_id=record.workflow_id,
            status=record.status,
            started_at=record.started_at,
            completed_at=record.completed_at,
            duration_ms=record.duration_ms,
            error=record.error,
        )
        for record in records
    ]

    return ExecutionRecordListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size),
    )


@router.get('/{execution_id}', response_model=ExecutionRecordResponse)
async def get_execution_record(
    execution_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: UserEntity = Depends(get_current_user),
):
    """获取单个执行记录详情"""
    service = ExecutionRecordService(session)
    record = await service.get_execution_record(execution_id)

    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='执行记录不存在')

    return record


@router.get('/{execution_id}/nodes', response_model=List[NodeExecutionResultResponse])
async def get_execution_node_results(
    execution_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: UserEntity = Depends(get_current_user),
):
    """获取执行记录的节点结果"""
    service = ExecutionRecordService(session)

    # 验证执行记录是否存在
    record = await service.get_execution_record(execution_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='执行记录不存在')

    node_results = await service.get_node_execution_results(execution_id)
    return node_results


@router.delete('/{execution_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_execution_record(
    execution_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: UserEntity = Depends(get_current_user),
):
    """删除执行记录"""
    service = ExecutionRecordService(session)

    success = await service.delete_execution_record(execution_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='执行记录不存在')

    return None


@router.get('/workflows/{workflow_id}/executions', response_model=List[ExecutionRecordListItem])
async def get_workflow_executions(
    workflow_id: UUID,
    limit: int = Query(50, ge=1, le=100, description='返回数量限制'),
    session: AsyncSession = Depends(get_session),
    current_user: UserEntity = Depends(get_current_user),
):
    """获取工作流的执行记录"""
    service = ExecutionRecordService(session)
    records = await service.get_execution_records_by_workflow(workflow_id, limit)

    return [
        ExecutionRecordListItem(
            id=record.id,
            workflow_id=record.workflow_id,
            status=record.status,
            started_at=record.started_at,
            completed_at=record.completed_at,
            duration_ms=record.duration_ms,
            error=record.error,
        )
        for record in records
    ]


@router.get('/statistics', response_model=ExecutionStatistics)
async def get_execution_statistics(
    workflow_id: UUID = Query(None, description='工作流ID'),
    days: int = Query(30, ge=1, le=365, description='统计天数'),
    session: AsyncSession = Depends(get_session),
    current_user: UserEntity = Depends(get_current_user),
):
    """获取执行统计信息"""
    service = ExecutionRecordService(session)
    statistics = await service.get_execution_statistics(workflow_id, days)
    return statistics
