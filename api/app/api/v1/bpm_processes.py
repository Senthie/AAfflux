"""流程 API"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from api.app.schemas.bpm_process_schemas import (
    ProcessInstanceCreate,
    ProcessInstanceResponse,
)
from api.app.services.bpm_process_service import ProcessService

router = APIRouter()


# TODO: 实现依赖注入
def get_session():
    """获取数据库会话（待实现）"""
    pass


def get_current_user():
    """获取当前用户（待实现）"""
    pass


@router.post("/start", response_model=ProcessInstanceResponse)
async def start_process(
    request: ProcessInstanceCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """启动流程实例"""
    service = ProcessService(session)

    instance = await service.start_process(
        process_key=request.process_key,
        workspace_id=current_user.workspace_id,
        user_id=current_user.id,
        variables=request.variables,
        business_key=request.business_key,
        business_type=request.business_type,
    )

    return instance


@router.get("/{instance_id}", response_model=ProcessInstanceResponse)
async def get_process_instance(
    instance_id: UUID,
    session: Session = Depends(get_session),
):
    """获取流程实例详情"""
    service = ProcessService(session)
    instance = await service.get_process_instance(instance_id)

    if not instance:
        raise HTTPException(status_code=404, detail="Process instance not found")

    return instance


@router.post("/{instance_id}/cancel")
async def cancel_process(
    instance_id: UUID,
    reason: str,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """取消流程"""
    service = ProcessService(session)
    await service.cancel_process(instance_id, current_user.id, reason)

    return {"message": "Process cancelled successfully"}
