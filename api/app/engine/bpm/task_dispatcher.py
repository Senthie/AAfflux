"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-04 09:50:20
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-08 03:28:23
FilePath: /api/app/engine/bpm/task_dispatcher.py
Description: 任务分发器

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.bpm import Task, TaskStatus


class TaskDispatcher:
    """任务分发器 - 负责任务分配和通知"""

    def __init__(self, session: Session):
        self.session = session

    async def assign_task(self, task_id: UUID, assignee_id: UUID) -> None:
        """
        description: 分配任务给指定用户
        :param {UUID} task_id 任务ID
        :param {UUID} assignee_id: 任务处理人的id
        return {*}
        """
        task = self.session.get(Task, task_id)
        if not task:
            raise ValueError('Task not found')

        task.assignee = assignee_id
        task.status = TaskStatus.ASSIGNED

        self.session.add(task)
        self.session.commit()

        # TODO: 发送通知
        await self._notify_assignee(task, assignee_id)

    async def claim_task(self, task_id: UUID, user_id: UUID) -> None:
        """
        description: 用户认领任务

        :param {UUID} task_id 任务ID
        :param {UUID} user_id 用户ID
        """
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
        """
        description: 获取用户的任务列表
        :param {UUID} user_id 用户ID
        :param {UUID} workspace_id 任务所属的工作区ID
        :param {TaskStatus} status 任务状态
        """
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
