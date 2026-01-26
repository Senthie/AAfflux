"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-09 03:25:28
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-26 14:06:21
FilePath: /api/app/services/workflow_service.py
Description:Workflow management service.

This module provides CRUD operations for workflows, nodes, and connections,
including validation and serialization functionality.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

import hashlib
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.exceptions import WorkflowError, WorkspaceException
from app.enums.custom_response_code_enum import CustomResponseCodeEnum
from app.models.auth.user import UserEntity
from app.models.tenant.organization import TenantAccountRole, WorkspaceAccountUser
from app.models.workflow.workflow import (
    ExecutionRecordModel,
    WorkflowModel,
)
from app.schemas.page_schemas import PageRequest, PageResponse
from app.schemas.workflow import (
    GraphModel,
    WorkflowCreateRequest,
    WorkflowDetailResponse,
    WorkflowResponse,
    WorkflowUpdateRequest,
)
from app.utils.json_serializer import json_dumps_sorted, serialize_for_db


class WorkflowService:
    """Service for managing workflows, nodes, and connections."""

    def __init__(self, db: AsyncSession):
        """Initialize workflow service.

        Args:
            db: Async database session
        """
        self.db = db

    def _calculate_data_hash(self, graph: dict) -> str:
        """Calculate hash for workflow graph data."""
        graph_json = json_dumps_sorted(graph)
        return hashlib.sha256(graph_json.encode()).hexdigest()

    def _get_workflow_graph(self, workflow: WorkflowModel | WorkflowUpdateRequest) -> GraphModel:
        """Get the graph model from workflow."""
        if not workflow.graph:
            return GraphModel(nodes=[], connections=[])
        return GraphModel.model_validate(workflow.graph)

    def _serialize_graph_for_db(self, graph: GraphModel) -> dict:
        """Serialize graph model for database storage, handling UUID conversion."""
        return serialize_for_db(graph.model_dump())

    def _update_workflow_graph(self, workflow: WorkflowModel, graph: GraphModel) -> None:
        """Update workflow graph and increment version."""
        workflow.graph = self._serialize_graph_for_db(graph)
        workflow.data_hash = self._calculate_data_hash(workflow.graph)
        workflow.version += 1
        workflow.touch()

    # ========================================================================
    # Workflow CRUD Operations
    # ========================================================================

    async def create_workflow(
        self, workflow_data: WorkflowCreateRequest, workspace_id: UUID, user: UserEntity
    ) -> WorkflowModel:
        """Create a new workflow.

        Args:
            workflow_data: Workflow creation data
            workspace_id: ID of the workspace
            user: User creating the workflow

        Returns:
            Created Workflow object
        """
        # 1. get workspace
        result = await self.db.execute(
            select(WorkspaceAccountUser).where(
                WorkspaceAccountUser.user_id == user.id,  # type: ignore
                WorkspaceAccountUser.workspace_id == workspace_id,  # type: ignore
                WorkspaceAccountUser.is_deleted.is_(False),  # type: ignore
            )
        )
        workspace_account = result.scalars().first()
        # 2. Validate workspace 的权限
        if workspace_account is None:
            raise WorkspaceException(CustomResponseCodeEnum.WORKSPACE_NOT_EXISTS)

        if TenantAccountRole.is_editing_role(workspace_account.role) is False:
            raise WorkspaceException(CustomResponseCodeEnum.FORBIDDEN)

        # 3. ceate workflow
        workflow = WorkflowModel(
            name=workflow_data.name,
            description=workflow_data.description,
            workspace_id=workspace_id,  # type: ignore
            input_schema=workflow_data.input_schema,
            output_schema=workflow_data.output_schema,
            created_by=user.id,  # type: ignore
        )

        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)

        return workflow

    async def get_workflow(self, workflow_id: UUID, user: UserEntity) -> WorkflowDetailResponse:
        """Get a workflow by ID.

        Args:
            workflow_id: ID of the workflow
            user: Current user

        Returns:
            Workflow object

        Raises:
            WorkflowNotFoundError: If workflow is not found
        """
        # 1. get workflow
        workflow = await self.db.get(WorkflowModel, workflow_id)
        if not workflow or workflow.is_deleted:
            raise WorkflowError(CustomResponseCodeEnum.WORKFLOW_NOT_EXISTS)
        # 2. get workspace by workflow_id
        result = await self.db.execute(
            select(WorkspaceAccountUser).where(
                WorkspaceAccountUser.user_id == user.id,  # type: ignore
                WorkspaceAccountUser.workspace_id == workflow.workspace_id,  # type: ignore
                WorkspaceAccountUser.is_deleted.is_(False),  # type: ignore
            )
        )
        workspace_account = result.scalars().first()
        # 2. Validate workspace 的权限
        if workspace_account is None:
            raise WorkspaceException(CustomResponseCodeEnum.WORKSPACE_NOT_EXISTS)

        if TenantAccountRole.is_editing_role(workspace_account.role) is False:
            raise WorkspaceException(CustomResponseCodeEnum.FORBIDDEN)

        return WorkflowDetailResponse.model_validate(workflow)

    async def list_workflows(
        self, workspace_id: UUID, page_req: PageRequest
    ) -> PageResponse[WorkflowResponse]:
        """List workflows in a workspace.

        Args:
            workspace_id: ID of the workspace
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of workflows, total count)
        """
        # Query workflows
        # 计算跳过值
        skip = (page_req.current - 1) * page_req.size
        statement = (
            select(WorkflowModel)
            .where(WorkflowModel.workspace_id == workspace_id)
            .where(WorkflowModel.is_deleted == False)
            .offset(skip)
            .limit(page_req.size)
        )
        result = await self.db.execute(statement)
        workflows = result.scalars().all()
        workflows = [WorkflowResponse.model_validate(workflow) for workflow in workflows]
        # Count total
        count_statement = (
            select(WorkflowModel)
            .where(WorkflowModel.workspace_id == workspace_id)
            .where(WorkflowModel.is_deleted == False)
        )
        count_result = await self.db.execute(count_statement)
        total = len(count_result.scalars().all())
        page_res = PageResponse.model_validate(page_req.model_dump())
        page_res.records = workflows
        page_res.total = total
        return page_res

    async def update_workflow(
        self, workflow_id: UUID, workflow_data: WorkflowUpdateRequest, user: UserEntity
    ) -> None:
        """Update a workflow.

        Args:
            workflow_id: ID of the workflow
            workflow_data: Workflow update data

        Returns:
            Updated Workflow object

        Raises:
            WorkflowNotFoundError: If workflow is not found

        TOOD：Lacking about Group validation
        """
        # 1. get workflow
        workflow = await self._get_workflow_internal(workflow_id)
        # 2. get workspace by workflow_id
        result = await self.db.execute(
            select(WorkspaceAccountUser).where(
                WorkspaceAccountUser.user_id == user.id,  # type: ignore
                WorkspaceAccountUser.workspace_id == workflow.workspace_id,  # type: ignore
                WorkspaceAccountUser.is_deleted.is_(False),  # type: ignore
            )
        )
        workspace_account = result.scalars().first()
        # 2. Validate workspace 的权限
        if workspace_account is None:
            raise WorkspaceException(CustomResponseCodeEnum.WORKSPACE_NOT_EXISTS)

        if TenantAccountRole.is_editing_role(workspace_account.role) is False:
            raise WorkspaceException(CustomResponseCodeEnum.FORBIDDEN)

        # Update fields
        if workflow_data.name is not None:
            workflow.name = workflow_data.name
        if workflow_data.description is not None:
            workflow.description = workflow_data.description
        if workflow_data.input_schema is not None:
            workflow.input_schema = workflow_data.input_schema
        if workflow_data.output_schema is not None:
            workflow.output_schema = workflow_data.output_schema

        # 验证 grap
        graph = self._get_workflow_graph(workflow_data)
        self._update_workflow_graph(workflow, graph)
        workflow.touch()

        await self.db.commit()
        await self.db.refresh(workflow)

    async def delete_workflow(self, workflow_id: UUID, user: UserEntity) -> None:
        """Delete a workflow and all its associated data.

        This performs a soft delete on the workflow.

        Args:
            workflow_id: ID of the workflow

        Raises:
            WorkflowNotFoundError: If workflow is not found
        """
        workflow_response = await self.get_workflow(workflow_id, user)
        workflow = await self._get_workflow_internal(workflow_id)

        # 1. get workspace
        result = await self.db.execute(
            select(WorkspaceAccountUser).where(
                WorkspaceAccountUser.user_id == user.id,  # type: ignore
                WorkspaceAccountUser.workspace_id == workflow_response.workspace_id,
                WorkspaceAccountUser.is_deleted.is_(False),  # type: ignore
            )
        )
        workspace_account = result.scalars().first()
        # 2. Validate workspace 的权限
        if workspace_account is None:
            raise WorkspaceException(CustomResponseCodeEnum.WORKSPACE_NOT_EXISTS)

        if TenantAccountRole.is_editing_role(workspace_account.role) is False:
            raise WorkspaceException(CustomResponseCodeEnum.FORBIDDEN)

        # Soft delete the workflow
        workflow.soft_delete()

        # Delete all execution records (hard delete)
        exec_statement = select(ExecutionRecordModel).where(
            ExecutionRecordModel.workflow_id == workflow_id
        )
        exec_result = await self.db.execute(exec_statement)
        exec_records = exec_result.scalars().all()

        for record in exec_records:
            await self.db.delete(record)

        await self.db.commit()

    async def _get_workflow_internal(self, workflow_id: UUID) -> WorkflowModel:
        """Internal method to get workflow without permission checks."""
        workflow = await self.db.get(WorkflowModel, workflow_id)
        if not workflow or workflow.is_deleted:
            raise WorkflowError(CustomResponseCodeEnum.WORKFLOW_NOT_EXISTS)
        return workflow
