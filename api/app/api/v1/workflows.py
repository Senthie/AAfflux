"""
Workflow management API endpoints.

This module provides RESTful API endpoints for managing workflows, nodes, and connections.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.middleware.auth import get_current_user
from app.models.auth.user import User
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
    WorkflowListResponse,
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
CurrentUser = Annotated[User, Depends(get_current_user)]


# ============================================================================
# Workflow Endpoints
# ============================================================================


@router.post(
    '/',
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Create a new workflow',
)
async def create_workflow(
    workflow_data: WorkflowCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
    workspace_id: UUID,
) -> WorkflowResponse:
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
            created_by=current_user.id,
        )
        return WorkflowResponse.model_validate(workflow)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to create workflow: {str(e)}',
        ) from e


@router.get(
    '/',
    response_model=WorkflowListResponse,
    summary='List workflows in workspace',
)
async def list_workflows(
    workspace_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    skip: int = 0,
    limit: int = 100,
) -> WorkflowListResponse:
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

    workflows, total = await service.list_workflows(
        workspace_id=workspace_id, skip=skip, limit=limit
    )

    return WorkflowListResponse(
        workflows=[WorkflowResponse.model_validate(w) for w in workflows],
        total=total,
    )


@router.get(
    '/{workflow_id}',
    response_model=WorkflowDetailResponse,
    summary='Get workflow details',
)
async def get_workflow(
    workflow_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> WorkflowDetailResponse:
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

        return WorkflowDetailResponse(
            **workflow.model_dump(),
            nodes=[NodeResponse.model_validate(n) for n in nodes],
            connections=[ConnectionResponse.model_validate(c) for c in connections],
        )
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.put(
    '/{workflow_id}',
    response_model=WorkflowResponse,
    summary='Update workflow',
)
async def update_workflow(
    workflow_id: UUID,
    workflow_data: WorkflowUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> WorkflowResponse:
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
        return WorkflowResponse.model_validate(workflow)
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.delete(
    '/{workflow_id}',
    response_model=WorkflowDeleteResponse,
    summary='Delete workflow',
)
async def delete_workflow(
    workflow_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> WorkflowDeleteResponse:
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
        await service.delete_workflow(workflow_id)
        return WorkflowDeleteResponse(
            success=True,
            message='Workflow deleted successfully',
            workflow_id=workflow_id,
        )
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    '/{workflow_id}/validate',
    response_model=ValidationResultResponse,
    summary='Validate workflow',
)
async def validate_workflow(
    workflow_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> ValidationResultResponse:
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
        return ValidationResultResponse(
            is_valid=validation_result.is_valid,
            errors=[ValidationErrorDetail(message=error) for error in validation_result.errors],
        )
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    '/{workflow_id}/save',
    response_model=WorkflowResponse,
    summary='Save and validate workflow',
)
async def save_workflow(
    workflow_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> WorkflowResponse:
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
        return WorkflowResponse.model_validate(workflow)
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except WorkflowValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                'message': 'Workflow validation failed',
                'errors': e.validation_result.errors,
            },
        ) from e


# ============================================================================
# Node Endpoints
# ============================================================================


@router.post(
    '/{workflow_id}/nodes',
    response_model=NodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Add node to workflow',
)
async def add_node(
    workflow_id: UUID,
    node_data: NodeCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> NodeResponse:
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
        return NodeResponse.model_validate(node)
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except WorkflowValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                'message': 'Node validation failed',
                'errors': e.validation_result.errors,
            },
        ) from e


@router.get(
    '/{workflow_id}/nodes',
    response_model=list[NodeResponse],
    summary='List workflow nodes',
)
async def list_nodes(
    workflow_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> list[NodeResponse]:
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
    return [NodeResponse.model_validate(n) for n in nodes]


@router.get(
    '/{workflow_id}/nodes/{node_id}',
    response_model=NodeResponse,
    summary='Get node details',
)
async def get_node(
    workflow_id: UUID,
    node_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> NodeResponse:
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Node {node_id} not found in workflow {workflow_id}',
            )
        return NodeResponse.model_validate(node)
    except NodeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.put(
    '/{workflow_id}/nodes/{node_id}',
    response_model=NodeResponse,
    summary='Update node',
)
async def update_node(
    workflow_id: UUID,
    node_id: UUID,
    node_data: NodeUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> NodeResponse:
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Node {node_id} not found in workflow {workflow_id}',
            )

        updated_node = await service.update_node(node_id, node_data)
        return NodeResponse.model_validate(updated_node)
    except NodeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except WorkflowValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                'message': 'Node validation failed',
                'errors': e.validation_result.errors,
            },
        ) from e


@router.delete(
    '/{workflow_id}/nodes/{node_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete node',
)
async def delete_node(
    workflow_id: UUID,
    node_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> None:
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Node {node_id} not found in workflow {workflow_id}',
            )

        await service.delete_node(node_id)
    except NodeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


# ============================================================================
# Connection Endpoints
# ============================================================================


@router.post(
    '/{workflow_id}/connections',
    response_model=ConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Create connection between nodes',
)
async def create_connection(
    workflow_id: UUID,
    connection_data: ConnectionCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> ConnectionResponse:
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
        return ConnectionResponse.model_validate(connection)
    except (WorkflowNotFoundError, NodeNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except WorkflowValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                'message': 'Connection validation failed',
                'errors': e.validation_result.errors,
            },
        ) from e


@router.get(
    '/{workflow_id}/connections',
    response_model=list[ConnectionResponse],
    summary='List workflow connections',
)
async def list_connections(
    workflow_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> list[ConnectionResponse]:
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
    return [ConnectionResponse.model_validate(c) for c in connections]


@router.delete(
    '/{workflow_id}/connections/{connection_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete connection',
)
async def delete_connection(
    workflow_id: UUID,
    connection_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> None:
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Connection {connection_id} not found in workflow {workflow_id}',
            )

        await service.delete_connection(connection_id)
    except ConnectionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
