"""任务分发器"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from api.app.models.bpm import Task, TaskStatus
from sqlmodel import Session, select


class TaskDispatcher:
    """任务分发器 - 负责任务分配和通知"""

    def __init__(self, session: Session):
        self.session = session

    async def assign_task(self, task_id: UUID, assignee_id: UUID):
        """分配任务给指定用户"""
        task = self.session.get(Task, task_id)
        if not task:
            raise ValueError('Task not found')

        task.assignee = assignee_id
        task.status = TaskStatus.ASSIGNED

        self.session.add(task)
        self.session.commit()

        # TODO: 发送通知
        await self._notify_assignee(task, assignee_id)

    async def claim_task(self, task_id: UUID, user_id: UUID):
        """用户认领任务"""
        task = self.session.get(Task, task_id)
        if not task:
            raise ValueError('Task not found')

        if task.assignee and task.assignee != user_id:
            raise ValueError('Task already assigned to another user')

        task.assignee = user_id
        task.status = TaskStatus.IN_PROGRESS
        task.claimed_at = datetime.utcnow()

        self.session.add(task)
        self.session.commit()

    async def get_user_tasks(
        self, user_id: UUID, workspace_id: UUID, status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """获取用户的任务列表"""
        statement = select(Task).where(
            Task.assignee == user_id,
            Task.workspace_id == workspace_id,
        )

        if status:
            statement = statement.where(Task.status == status)

        tasks = self.session.exec(statement).all()
        return list(tasks)

    async def _notify_assignee(self, task: Task, assignee_id: UUID):
        """通知任务处理人"""
        # TODO: 实现通知逻辑（邮件、站内信、Webhook等）
        pass
