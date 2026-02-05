"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-09 03:26:58
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-02-04 15:57:31
FilePath: /api/app/api/v1/workflows.py
Description:Workflow management API endpoints.

This module provides RESTful API endpoints for managing workflows, nodes, and connections.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import WorkflowError, WorkspaceException
from app.core.response import ResponseModel, ResponseSchemaModel, response_base
from app.enums.custom_response_code_enum import CustomResponseCodeEnum
from app.middleware.auth import get_current_user
from app.models.auth.user import UserEntity
from app.schemas.page_schemas import PageRequest, PageResponse
from app.schemas.workflow import (
    WorkflowCreateRequest,
    WorkflowDeleteResponse,
    WorkflowResponse,
    WorkflowUpdateRequest,
)
from app.services.workflow_service import (
    WorkflowService,
)

router = APIRouter(prefix='/workflows', tags=['Workflow Management'])

# Dependency injection definitions
DbSession = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[UserEntity, Depends(get_current_user)]


# ============================================================================
# Workflow Endpoints
# ============================================================================


@router.post(
    '/',
    summary='Create a new workflow',
)
async def create_workflow(
    workflow_data: WorkflowCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
    workspace_id: UUID,
) -> ResponseSchemaModel[WorkflowResponse] | ResponseModel:
    """
    Create a new workflow in the specified workspace.

    Args:
        workflow_data: Workflow creation data
        current_user: Current authenticated user
        session: Database session
        workspace_id: ID of the workspace to create workflow in

    Returns:
        Created workflow
    """
    service = WorkflowService(session)

    try:
        workflow = await service.create_workflow(
            workflow_data=workflow_data,
            workspace_id=workspace_id,
            user=current_user,
        )
        return response_base.success(data=WorkflowResponse.model_validate(workflow))
    except WorkspaceException as e:
        return response_base.fail(
            res=e.response_code,
            data=f'Failed to create workflow: {str(e)}',
        )

    except Exception as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.INTERNAL_SERVER_ERROR,
            data=f'Failed to create workflow: {str(e)}',
        )


@router.post(
    '/list',
    summary='List workflows in workspace',
)
async def list_workflows(
    workspace_id: UUID,
    page_req: PageRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[PageResponse[WorkflowResponse]]:
    """
    List all workflows in the specified workspace.

    Args:
        workspace_id: ID of the workspace
        current_user: Current authenticated user
        session: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of workflows and total count
    """
    service = WorkflowService(session)

    res = await service.list_workflows(workspace_id=workspace_id, page_req=page_req)

    return response_base.success(data=res)


@router.get(
    '/{workflow_id}',
    summary='Get workflow details',
)
async def get_workflow(
    workflow_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[WorkflowResponse] | ResponseModel:
    """
    Get detailed information about a workflow including nodes and connections.

    Args:
        workflow_id: ID of the workflow
        current_user: Current authenticated user
        session: Database session

    Returns:
        Workflow details with nodes and connections
    """
    service = WorkflowService(session)

    try:
        workflow = await service.get_workflow(workflow_id, current_user)

        return response_base.success(data=workflow)
    except WorkflowError as e:
        return response_base.fail(res=e.response_code, data=e.message)
    except WorkspaceException as e:
        return response_base.fail(
            res=e.response_code,
            data=f'Failed to create workflow: {str(e)}',
        )


@router.put(
    '/{workflow_id}',
    summary='Update workflow',
)
async def update_workflow(
    workflow_id: UUID,
    workflow_data: WorkflowUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel | ResponseModel:
    """
    Update a workflow's properties.

    Args:
        workflow_id: ID of the workflow
        workflow_data: Workflow update data
        current_user: Current authenticated user
        session: Database session

    Returns:
        Updated workflow
    """
    service = WorkflowService(session)

    try:
        await service.update_workflow(workflow_id, workflow_data, current_user)
        return response_base.success()
    except WorkflowError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )
    except Exception as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.INTERNAL_SERVER_ERROR,
            data=f'Failed to update workflow: {str(e)}',
        )


@router.delete(
    '/{workflow_id}',
    summary='Delete workflow',
)
async def delete_workflow(
    workflow_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[WorkflowDeleteResponse] | ResponseModel:
    """
    Delete a workflow and all its associated data.

    Args:
        workflow_id: ID of the workflow
        current_user: Current authenticated user
        session: Database session

    Returns:
        Deletion confirmation
    """
    service = WorkflowService(session)

    try:
        await service.delete_workflow(workflow_id, current_user)
        return response_base.success(
            data=WorkflowDeleteResponse(
                success=True,
                message='Workflow deleted successfully',
                workflow_id=workflow_id,
            )
        )
    except WorkspaceException as e:
        return response_base.fail(
            res=e.response_code,
            data=f'Failed to create workflow: {str(e)}',
        )
    except WorkflowError as e:
        return response_base.fail(
            res=e.response_code,
            data=str(e),
        )


# ============================================================================
# Workflow Testing Endpoints
# ============================================================================


@router.post(
    '/{workflow_id}/run',
    summary='Test workflow execution',
)
async def run_workflow(
    workflow_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel | ResponseModel:
    """
    Test a workflow with provided inputs without saving to production execution records.

    This endpoint allows users to test their workflows during development.
    The execution is performed in a sandbox environment and results are returned immediately.

    Args:
        workflow_id: ID of the workflow to test
        test_request: Test request containing inputs and options
        current_user: Current authenticated user
        session: Database session

    Returns:
        Test execution results including outputs, node results, and performance metrics
    """
    workflow_service = WorkflowService(session)

    try:
        # Verify user has access to the workflow
        record_id = await workflow_service.run_workflow(workflow_id, current_user)

        # Execute workflow test

        return response_base.success(data=record_id)

    except WorkflowError as e:
        return response_base.fail(res=e.response_code, data=e.message)
    except WorkspaceException as e:
        return response_base.fail(
            res=e.response_code,
            data=f'Failed to test workflow: {str(e)}',
        )
    except Exception as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.INTERNAL_SERVER_ERROR,
            data=f'Failed to test workflow: {str(e)}',
        )
