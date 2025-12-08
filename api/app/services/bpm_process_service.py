"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-04 09:50:20
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-08 03:16:16
FilePath: /api/app/services/bpm_process_service.py
Description: 流程服务

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Optional
from uuid import UUID

from sqlmodel import Session

from app.engine.bpm import ProcessExecutor
from app.models.bpm import ProcessInstance


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
        """
        description: 启动流程
        param {str} process_key
        param {UUID} workspace_id
        param {UUID} user_id
        param {dict} variables
        param {Optional} business_key
        param {Optional} business_type
        """
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
        """
        description: 取消流程
        param {*} self
        param {UUID} instance_id
        param {UUID} user_id
        param {str} reason
        return {*}
        """
        instance = self.session.get(ProcessInstance, instance_id)
        if not instance:
            raise ValueError('Process instance not found')

        from app.bpm.models import ProcessStatus

        instance.status = ProcessStatus.CANCELLED
        instance.error_message = reason

        self.session.add(instance)
        self.session.commit()

    async def get_process_instance(self, instance_id: UUID) -> Optional[ProcessInstance]:
        """
        description: 获取流程实例
        param {*} self
        param {UUID} instance_id
        return {*}
        """

        return self.session.get(ProcessInstance, instance_id)
