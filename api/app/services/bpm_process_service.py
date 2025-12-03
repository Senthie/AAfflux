"""流程服务"""

from typing import Optional
from uuid import UUID

from sqlmodel import Session

from api.app.engine.bpm import ProcessExecutor
from api.app.models.bpm import ProcessInstance


class ProcessService:
    """流程服务 - 业务逻辑层"""

    def __init__(self, session: Session):
        self.session = session
        self.executor = ProcessExecutor(session)

    async def start_process(
        self,
        process_key: str,
        workspace_id: UUID,
        user_id: UUID,
        variables: dict,
        business_key: Optional[str] = None,
        business_type: Optional[str] = None,
    ) -> ProcessInstance:
        """启动流程"""
        instance = await self.executor.start_process(
            process_key=process_key,
            workspace_id=workspace_id,
            started_by=user_id,
            variables=variables,
            business_key=business_key,
        )
        
        if business_type:
            instance.business_type = business_type
            self.session.add(instance)
            self.session.commit()

        return instance

    async def cancel_process(self, instance_id: UUID, user_id: UUID, reason: str):
        """取消流程"""
        instance = self.session.get(ProcessInstance, instance_id)
        if not instance:
            raise ValueError("Process instance not found")

        from api.app.bpm.models import ProcessStatus
        instance.status = ProcessStatus.CANCELLED
        instance.error_message = reason
        
        self.session.add(instance)
        self.session.commit()

    async def get_process_instance(self, instance_id: UUID) -> Optional[ProcessInstance]:
        """获取流程实例"""
        return self.session.get(ProcessInstance, instance_id)
