"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-09 03:26:58
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-14 11:21:35
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
from app.core.exceptions import WorkspaceException
from app.core.response import ResponseModel, ResponseSchemaModel, response_base
from app.enums.custom_response_code_enum import CustomResponseCodeEnum
from app.middleware.auth import get_current_user
from app.models.auth.user import UserEntity
from app.schemas.page_schemas import PageRequest, PageResponse
from app.schemas.workflow import (
    ConnectionCreateRequest,
    ConnectionResponse,
    NodeCreateRequest,
    NodeResponse,
    NodeUpdateRequest,
    ValidationErrorDetail,
    ValidationResultResponse,
    WorkflowCreateRequest,
    WorkflowDeleteResponse,
    WorkflowDetailResponse,
    WorkflowResponse,
    WorkflowUpdateRequest,
)
from app.services.workflow_service import (
    ConnectionNotFoundError,
    NodeNotFoundError,
    WorkflowNotFoundError,
    WorkflowService,
    WorkflowValidationError,
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
) -> ResponseSchemaModel[WorkflowDetailResponse] | ResponseModel:
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
        workflow = await service.get_workflow(workflow_id)
        nodes = await service.list_nodes(workflow_id)
        connections = await service.list_connections(workflow_id)

        return response_base.success(
            data=WorkflowDetailResponse(
                **workflow.model_dump(),
                nodes=[NodeResponse.model_validate(n) for n in nodes],
                connections=[ConnectionResponse.model_validate(c) for c in connections],
            )
        )
    except WorkflowNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
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
) -> ResponseSchemaModel[WorkflowResponse] | ResponseModel:
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
        workflow = await service.update_workflow(workflow_id, workflow_data)
        return response_base.success(data=WorkflowResponse.model_validate(workflow))
    except WorkflowNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
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
    except WorkflowNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )


@router.post(
    '/{workflow_id}/validate',
    summary='Validate workflow',
)
async def validate_workflow(
    workflow_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[ValidationResultResponse] | ResponseModel:
    """
    Validate a workflow's completeness and correctness.

    Args:
        workflow_id: ID of the workflow
        current_user: Current authenticated user
        session: Database session

    Returns:
        Validation result
    """
    service = WorkflowService(session)

    try:
        validation_result = await service.validate_workflow(workflow_id)
        return response_base.success(
            data=ValidationResultResponse(
                is_valid=validation_result.is_valid,
                errors=[ValidationErrorDetail(message=error) for error in validation_result.errors],
            )
        )
    except WorkflowNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )


@router.post(
    '/{workflow_id}/save',
    summary='Save and validate workflow',
)
async def save_workflow(
    workflow_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[WorkflowResponse] | ResponseModel:
    """
    Save a workflow after validating its completeness.

    Args:
        workflow_id: ID of the workflow
        current_user: Current authenticated user
        session: Database session

    Returns:
        Saved workflow

    Raises:
        HTTPException: If workflow validation fails
    """
    service = WorkflowService(session)

    try:
        workflow = await service.save_workflow(workflow_id)
        return response_base.success(data=WorkflowResponse.model_validate(workflow))
    except WorkflowNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )
    except WorkflowValidationError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.BAD_REQUEST,
            data={
                'message': 'Workflow validation failed',
                'errors': e.validation_result.errors,
            },
        )


# ============================================================================
# Node Endpoints
# ============================================================================


@router.post(
    '/{workflow_id}/nodes',
    summary='Add node to workflow',
)
async def add_node(
    workflow_id: UUID,
    node_data: NodeCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[NodeResponse] | ResponseModel:
    """
    Add a new node to a workflow.

    Args:
        workflow_id: ID of the workflow
        node_data: Node creation data
        current_user: Current authenticated user
        session: Database session

    Returns:
        Created node
    """
    service = WorkflowService(session)

    try:
        node = await service.add_node(workflow_id, node_data)
        return response_base.success(data=NodeResponse.model_validate(node))
    except WorkflowNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )
    except WorkflowValidationError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.BAD_REQUEST,
            data={
                'message': 'Node validation failed',
                'errors': e.validation_result.errors,
            },
        )


@router.get(
    '/{workflow_id}/nodes',
    summary='List workflow nodes',
)
async def list_nodes(
    workflow_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[list[NodeResponse]] | ResponseModel:
    """
    List all nodes in a workflow.

    Args:
        workflow_id: ID of the workflow
        current_user: Current authenticated user
        session: Database session

    Returns:
        List of nodes
    """
    service = WorkflowService(session)

    nodes = await service.list_nodes(workflow_id)
    return response_base.success(data=[NodeResponse.model_validate(n) for n in nodes])


@router.get(
    '/{workflow_id}/nodes/{node_id}',
    summary='Get node details',
)
async def get_node(
    workflow_id: UUID,
    node_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[NodeResponse] | ResponseModel:
    """
    Get details of a specific node.

    Args:
        workflow_id: ID of the workflow
        node_id: ID of the node
        current_user: Current authenticated user
        session: Database session

    Returns:
        Node details
    """
    service = WorkflowService(session)

    try:
        node = await service.get_node(node_id)
        # Verify node belongs to the workflow
        if node.workflow_id != workflow_id:
            return response_base.fail(
                res=CustomResponseCodeEnum.NOT_FOUND,
                data=f'Node {node_id} not found in workflow {workflow_id}',
            )
        return response_base.success(data=NodeResponse.model_validate(node))
    except NodeNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )


@router.put(
    '/{workflow_id}/nodes/{node_id}',
    summary='Update node',
)
async def update_node(
    workflow_id: UUID,
    node_id: UUID,
    node_data: NodeUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[NodeResponse] | ResponseModel:
    """
    Update a node's properties.

    Args:
        workflow_id: ID of the workflow
        node_id: ID of the node
        node_data: Node update data
        current_user: Current authenticated user
        session: Database session

    Returns:
        Updated node
    """
    service = WorkflowService(session)

    try:
        node = await service.get_node(node_id)
        # Verify node belongs to the workflow
        if node.workflow_id != workflow_id:
            return response_base.fail(
                res=CustomResponseCodeEnum.NOT_FOUND,
                data=f'Node {node_id} not found in workflow {workflow_id}',
            )

        updated_node = await service.update_node(node_id, node_data)
        return response_base.success(data=NodeResponse.model_validate(updated_node))
    except NodeNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )
    except WorkflowValidationError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.BAD_REQUEST,
            data={
                'message': 'Node validation failed',
                'errors': e.validation_result.errors,
            },
        )


@router.delete(
    '/{workflow_id}/nodes/{node_id}',
    summary='Delete node',
)
async def delete_node(
    workflow_id: UUID,
    node_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseModel:
    """
    Delete a node from a workflow.

    Args:
        workflow_id: ID of the workflow
        node_id: ID of the node
        current_user: Current authenticated user
        session: Database session
    """
    service = WorkflowService(session)

    try:
        node = await service.get_node(node_id)
        # Verify node belongs to the workflow
        if node.workflow_id != workflow_id:
            return response_base.fail(
                res=CustomResponseCodeEnum.NOT_FOUND,
                data=f'Node {node_id} not found in workflow {workflow_id}',
            )

        await service.delete_node(node_id)
        return response_base.success()
    except NodeNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )


# ============================================================================
# Connection Endpoints
# ============================================================================


@router.post(
    '/{workflow_id}/connections',
    summary='Create connection between nodes',
)
async def create_connection(
    workflow_id: UUID,
    connection_data: ConnectionCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[ConnectionResponse] | ResponseModel:
    """
    Create a connection between two nodes in a workflow.

    Args:
        workflow_id: ID of the workflow
        connection_data: Connection creation data
        current_user: Current authenticated user
        session: Database session

    Returns:
        Created connection
    """
    service = WorkflowService(session)

    try:
        connection = await service.connect_nodes(workflow_id, connection_data)
        return response_base.success(data=ConnectionResponse.model_validate(connection))
    except (WorkflowNotFoundError, NodeNotFoundError) as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )
    except WorkflowValidationError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.BAD_REQUEST,
            data={
                'message': 'Connection validation failed',
                'errors': e.validation_result.errors,
            },
        )


@router.get(
    '/{workflow_id}/connections',
    summary='List workflow connections',
)
async def list_connections(
    workflow_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseSchemaModel[list[ConnectionResponse]] | ResponseModel:
    """
    List all connections in a workflow.

    Args:
        workflow_id: ID of the workflow
        current_user: Current authenticated user
        session: Database session

    Returns:
        List of connections
    """
    service = WorkflowService(session)

    connections = await service.list_connections(workflow_id)
    return response_base.success(data=[ConnectionResponse.model_validate(c) for c in connections])


@router.delete(
    '/{workflow_id}/connections/{connection_id}',
    summary='Delete connection',
)
async def delete_connection(
    workflow_id: UUID,
    connection_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ResponseModel:
    """
    Delete a connection between nodes.

    Args:
        workflow_id: ID of the workflow
        connection_id: ID of the connection
        current_user: Current authenticated user
        session: Database session
    """
    service = WorkflowService(session)

    try:
        connection = await service.get_connection(connection_id)
        # Verify connection belongs to the workflow
        if connection.workflow_id != workflow_id:
            return response_base.fail(
                res=CustomResponseCodeEnum.NOT_FOUND,
                data=f'Connection {connection_id} not found in workflow {workflow_id}',
            )

        await service.delete_connection(connection_id)
        return response_base.success()
    except ConnectionNotFoundError as e:
        return response_base.fail(
            res=CustomResponseCodeEnum.NOT_FOUND,
            data=str(e),
        )
