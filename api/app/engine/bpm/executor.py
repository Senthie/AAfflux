"""流程执行器"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from api.app.models.bpm import ProcessInstance, ProcessStatus, Task, TaskStatus, ProcessDefinition


class ProcessExecutor:
    """流程执行引擎"""

    def __init__(self, session: Session):
        self.session = session

    async def start_process(
        self,
        process_key: str,
        workspace_id: UUID,
        started_by: UUID,
        variables: dict,
        business_key: Optional[str] = None,
    ) -> ProcessInstance:
        """启动流程实例"""
        # 获取流程定义
        statement = select(ProcessDefinition).where(
            ProcessDefinition.key == process_key,
            ProcessDefinition.is_latest,
            ProcessDefinition.is_active,
        )
        process_def = self.session.exec(statement).first()

        if not process_def:
            raise ValueError(f"Process definition not found: {process_key}")

        # 创建流程实例
        instance = ProcessInstance(
            process_definition_id=process_def.id,
            process_key=process_key,
            process_version=process_def.version,
            business_key=business_key,
            workspace_id=workspace_id,
            started_by=started_by,
            variables=variables,
            status=ProcessStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)

        # 执行第一个节点
        await self._execute_next_node(instance, process_def)

        return instance

    async def _execute_next_node(self, instance: ProcessInstance, process_def: ProcessDefinition):
        """执行下一个节点"""
        nodes = process_def.nodes

        # 找到开始节点
        start_node = next((n for n in nodes if n.get("type") == "start"), None)
        if not start_node:
            raise ValueError("Start node not found")

        # 找到第一个用户任务
        first_task_node = next((n for n in nodes if n.get("type") == "user_task"), None)

        if first_task_node:
            # 创建任务
            await self._create_task(instance, first_task_node)
            instance.status = ProcessStatus.WAITING
            instance.current_node_id = first_task_node["id"]
        else:
            # 没有任务，直接完成
            instance.status = ProcessStatus.COMPLETED
            instance.completed_at = datetime.utcnow()

        self.session.add(instance)
        self.session.commit()

    async def _create_task(self, instance: ProcessInstance, node: dict):
        """创建任务"""
        task = Task(
            process_instance_id=instance.id,
            task_def_key=node["id"],
            task_name=node["name"],
            workspace_id=instance.workspace_id,
            status=TaskStatus.PENDING,
            variables=instance.variables,
        )

        self.session.add(task)
        self.session.commit()
        return task

    async def complete_task(
        self, task_id: UUID, user_id: UUID, result: dict, comment: Optional[str] = None
    ):
        """完成任务"""
        task = self.session.get(Task, task_id)
        if not task:
            raise ValueError("Task not found")

        # 更新任务状态
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.result = result
        task.comment = comment

        self.session.add(task)
        self.session.commit()

        # 继续流程
        await self._continue_process(task.process_instance_id, result)

    async def _continue_process(self, instance_id: UUID, task_result: dict):
        """继续执行流程"""
        instance = self.session.get(ProcessInstance, instance_id)
        if not instance:
            return

        # 检查是否所有任务完成
        statement = select(Task).where(
            Task.process_instance_id == instance_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
        )
        pending_tasks = self.session.exec(statement).all()

        if not pending_tasks:
            # 所有任务完成，流程结束
            instance.status = ProcessStatus.COMPLETED
            instance.completed_at = datetime.utcnow()
            instance.result = task_result

            self.session.add(instance)
            self.session.commit()
