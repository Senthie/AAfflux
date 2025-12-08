"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-04 09:50:20
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-08 01:58:03
FilePath: /api/app/services/bpm_task_service.py
Description: 任务服务

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import List, Optional
from uuid import UUID

from sqlmodel import Session

from app.engine.bpm import TaskDispatcher
from app.models.bpm import Task, TaskStatus


class TaskService:
    """任务服务"""

    def __init__(self, session: Session):
        self.session = session
        self.dispatcher = TaskDispatcher(session)

    async def get_my_tasks(
        self, user_id: UUID, workspace_id: UUID, status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """获取我的任务"""
        return await self.dispatcher.get_user_tasks(user_id, workspace_id, status)

    async def claim_task(self, task_id: UUID, user_id: UUID) -> None:
        """
        description: 认领任务
        param {*} self
        param {UUID} task_id 任务ID
        param {UUID} user_id 用户ID
        """
        return await self.dispatcher.claim_task(task_id, user_id)

    async def complete_task(
        self, task_id: UUID, user_id: UUID, result: dict, comment: Optional[str] = None
    ):
        """
        description: 认领任务
        param {*} self
        param {UUID} task_id 任务ID
        param {UUID} user_id 用户ID
        param {dict} result 任务结果
        param {Optional[str]} Optional 其他可选项
        """
        from app.engine.bpm import ProcessExecutor

        executor = ProcessExecutor(self.session)
        return await executor.complete_task(task_id, user_id, result, comment)

    async def get_task(self, task_id: UUID) -> Optional[Task]:
        """获取任务详情"""
        return self.session.get(Task, task_id)
