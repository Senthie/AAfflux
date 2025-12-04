"""审批 API"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api.app.schemas.bpm_approval_schemas import ApprovalRequest, ApprovalResponse
from api.app.services.bpm_approval_service import ApprovalService
from api.app.services.bpm_task_service import TaskService

router = APIRouter()


def get_session():
    """获取数据库会话（待实现）"""
    pass


def get_current_user():
    """获取当前用户（待实现）"""
    pass


@router.post("/{task_id}/approve", response_model=ApprovalResponse)
async def approve_task(
    task_id: UUID,
    request: ApprovalRequest,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """审批通过"""
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
        result={"approved": True},
        comment=request.comment,
    )

    return approval


@router.post("/{task_id}/reject", response_model=ApprovalResponse)
async def reject_task(
    task_id: UUID,
    request: ApprovalRequest,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """审批拒绝"""
    approval_service = ApprovalService(session)

    approval = await approval_service.reject_task(
        task_id=task_id,
        user_id=current_user.id,
        user_name=current_user.name,
        comment=request.comment or "拒绝",
        workspace_id=current_user.workspace_id,
    )

    # 完成任务
    task_service = TaskService(session)
    await task_service.complete_task(
        task_id=task_id,
        user_id=current_user.id,
        result={"approved": False},
        comment=request.comment,
    )

    return approval
