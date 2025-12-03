"""审批服务"""

from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from api.app.models.bpm import Approval, ApprovalAction, Task


class ApprovalService:
    """审批服务"""

    def __init__(self, session: Session):
        self.session = session

    async def approve_task(
        self,
        task_id: UUID,
        user_id: UUID,
        user_name: str,
        comment: Optional[str] = None,
        workspace_id: UUID = None,
    ) -> Approval:
        """审批通过"""
        return await self._create_approval(
            task_id=task_id,
            user_id=user_id,
            user_name=user_name,
            action=ApprovalAction.APPROVE,
            comment=comment,
            workspace_id=workspace_id,
        )

    async def reject_task(
        self,
        task_id: UUID,
        user_id: UUID,
        user_name: str,
        comment: str,
        workspace_id: UUID,
    ) -> Approval:
        """审批拒绝"""
        return await self._create_approval(
            task_id=task_id,
            user_id=user_id,
            user_name=user_name,
            action=ApprovalAction.REJECT,
            comment=comment,
            workspace_id=workspace_id,
        )

    async def _create_approval(
        self,
        task_id: UUID,
        user_id: UUID,
        user_name: str,
        action: ApprovalAction,
        comment: Optional[str],
        workspace_id: UUID,
    ) -> Approval:
        """创建审批记录"""
        task = self.session.get(Task, task_id)
        if not task:
            raise ValueError("Task not found")

        approval = Approval(
            task_id=task_id,
            process_instance_id=task.process_instance_id,
            approver_id=user_id,
            approver_name=user_name,
            action=action,
            comment=comment,
            workspace_id=workspace_id,
        )
        
        self.session.add(approval)
        self.session.commit()
        self.session.refresh(approval)

        return approval
