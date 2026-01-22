"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-22 10:18:19
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-22 14:12:47
FilePath: : AAfflux: api: app: services: execution_record_service.py
Description:记录创建、查询、清理
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlmodel import and_, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.workflow.workflow import ExecutionRecordModel, NodeExecutionResultModel
from app.schemas.execution import (
    ExecutionRecordCreate,
    ExecutionRecordQuery,
    ExecutionRecordUpdate,
    ExecutionStatistics,
)


class ExecutionRecordService:
    """执行记录服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_execution_record(self, data: ExecutionRecordCreate) -> ExecutionRecordModel:
        """创建执行记录"""
        execution_record = ExecutionRecordModel(
            workflow_id=data.workflow_id,
            inputs=data.inputs,
            status='PENDING',
            started_at=datetime.utcnow(),
        )
        self.session.add(execution_record)
        await self.session.commit()
        await self.session.refresh(execution_record)
        return execution_record

    async def get_execution_record(self, execution_id: UUID) -> Optional[ExecutionRecordModel]:
        """获取单个执行记录"""
        statement = select(ExecutionRecordModel).where(ExecutionRecordModel.id == execution_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def update_execution_record(
        self, execution_id: UUID, data: ExecutionRecordUpdate
    ) -> Optional[ExecutionRecordModel]:
        """更新执行记录"""
        execution_record = await self.get_execution_record(execution_id)
        if not execution_record:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(execution_record, key, value)

        self.session.add(execution_record)
        await self.session.commit()
        await self.session.refresh(execution_record)
        return execution_record

    async def delete_execution_record(self, execution_id: UUID) -> bool:
        """删除执行记录"""
        execution_record = await self.get_execution_record(execution_id)
        if not execution_record:
            return False

        await self.session.delete(execution_record)
        await self.session.commit()
        return True

    async def list_execution_records(
        self, query: ExecutionRecordQuery
    ) -> Tuple[List[ExecutionRecordModel], int]:
        """分页查询执行记录列表"""
        statement = select(ExecutionRecordModel)

        # 构建查询条件
        conditions = []
        if query.workflow_id:
            conditions.append(ExecutionRecordModel.workflow_id == query.workflow_id)
        if query.status:
            conditions.append(ExecutionRecordModel.status == query.status)
        if query.start_date:
            conditions.append(ExecutionRecordModel.started_at >= query.start_date)
        if query.end_date:
            conditions.append(ExecutionRecordModel.started_at <= query.end_date)

        if conditions:
            statement = statement.where(and_(*conditions))

        # 获取总数
        count_statement = select(func.count()).select_from(ExecutionRecordModel)
        if conditions:
            count_statement = count_statement.where(and_(*conditions))
        total_result = await self.session.execute(count_statement)
        total = total_result.scalar_one()

        # 分页
        statement = statement.order_by(ExecutionRecordModel.started_at.desc())
        statement = statement.offset((query.page - 1) * query.page_size)
        statement = statement.limit(query.page_size)

        result = await self.session.execute(statement)
        records = result.scalars().all()
        return list(records), total

    async def get_execution_records_by_workflow(
        self, workflow_id: UUID, limit: int = 50
    ) -> List[ExecutionRecordModel]:
        """按工作流查询执行记录"""
        statement = (
            select(ExecutionRecordModel)
            .where(ExecutionRecordModel.workflow_id == workflow_id)
            .order_by(ExecutionRecordModel.started_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_execution_records_by_date_range(
        self, start_date: datetime, end_date: datetime, workflow_id: Optional[UUID] = None
    ) -> List[ExecutionRecordModel]:
        """按时间范围查询执行记录"""
        statement = select(ExecutionRecordModel).where(
            and_(
                ExecutionRecordModel.started_at >= start_date,
                ExecutionRecordModel.started_at <= end_date,
            )
        )

        if workflow_id:
            statement = statement.where(ExecutionRecordModel.workflow_id == workflow_id)

        statement = statement.order_by(ExecutionRecordModel.started_at.desc())
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_execution_statistics(
        self, workflow_id: Optional[UUID] = None, days: int = 30
    ) -> ExecutionStatistics:
        """获取执行统计信息"""
        start_date = datetime.utcnow() - timedelta(days=days)

        statement = select(ExecutionRecordModel).where(
            ExecutionRecordModel.started_at >= start_date
        )

        if workflow_id:
            statement = statement.where(ExecutionRecordModel.workflow_id == workflow_id)

        result = await self.session.execute(statement)
        records = list(result.scalars().all())

        total = len(records)
        successful = sum(1 for r in records if r.status == 'SUCCESS')
        failed = sum(1 for r in records if r.status == 'FAILED')
        running = sum(1 for r in records if r.status == 'RUNNING')
        pending = sum(1 for r in records if r.status == 'PENDING')

        # 计算平均执行时间
        completed_records = [r for r in records if r.duration_ms is not None]
        avg_duration = None
        if completed_records:
            avg_duration = sum(r.duration_ms for r in completed_records) / len(completed_records)

        # 计算成功率
        success_rate = 0.0
        if total > 0:
            success_rate = (successful / total) * 100

        return ExecutionStatistics(
            total_executions=total,
            successful_executions=successful,
            failed_executions=failed,
            running_executions=running,
            pending_executions=pending,
            average_duration_ms=avg_duration,
            success_rate=success_rate,
        )

    async def get_node_execution_results(
        self, execution_id: UUID
    ) -> List[NodeExecutionResultModel]:
        """获取执行记录的节点结果"""
        statement = select(NodeExecutionResultModel).where(
            NodeExecutionResultModel.execution_record_id == execution_id
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def cleanup_expired_records(self, days: int = 90) -> int:
        """清理过期的执行记录"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        statement = select(ExecutionRecordModel).where(
            and_(
                ExecutionRecordModel.started_at < cutoff_date,
                or_(
                    ExecutionRecordModel.status == 'SUCCESS',
                    ExecutionRecordModel.status == 'FAILED',
                ),
            )
        )

        result = await self.session.execute(statement)
        records = list(result.scalars().all())
        count = len(records)

        for record in records:
            await self.session.delete(record)

        await self.session.commit()
        return count

    async def cleanup_failed_records(self, days: int = 30) -> int:
        """清理失败的执行记录"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        statement = select(ExecutionRecordModel).where(
            and_(
                ExecutionRecordModel.started_at < cutoff_date,
                ExecutionRecordModel.status == 'FAILED',
            )
        )

        result = await self.session.execute(statement)
        records = list(result.scalars().all())
        count = len(records)

        for record in records:
            await self.session.delete(record)

        await self.session.commit()
        return count
