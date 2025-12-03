"""任务服务"""

from typing import List, Optional
from uuid import UUID

from sqlmodel import Session

from api.app.engine.bpm import TaskDispatcher
from api.app.models.bpm import Task, TaskStatus


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

    async def claim_task(self, task_id: UUID, user_id: UUID):
        """认领任务"""
        return await self.dispatcher.claim_task(task_id, user_id)

    async def complete_task(
        self, task_id: UUID, user_id: UUID, result: dict, comment: Optional[str] = None
    ):
        """完成任务"""
        from api.app.engine.bpm import ProcessExecutor
        
        executor = ProcessExecutor(self.session)
        return await executor.complete_task(task_id, user_id, result, comment)

    async def get_task(self, task_id: UUID) -> Optional[Task]:
        """获取任务详情"""
        return self.session.get(Task, task_id)
