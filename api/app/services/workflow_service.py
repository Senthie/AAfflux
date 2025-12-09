"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-09 03:25:28
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-09 06:15:52
FilePath: /api/app/services/workflow_service.py
Description:Workflow management service.

This module provides CRUD operations for workflows, nodes, and connections,
including validation and serialization functionality.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.workflow.workflow import Connection, ExecutionRecord, Node, Workflow
from app.schemas.workflow import (
    ConnectionCreateRequest,
    NodeCreateRequest,
    NodeUpdateRequest,
    WorkflowCreateRequest,
    WorkflowUpdateRequest,
)
from app.services.workflow_validator import ValidationResult, WorkflowValidator


class WorkflowNotFoundError(Exception):
    """Exception raised when workflow is not found."""

    pass


class NodeNotFoundError(Exception):
    """Exception raised when node is not found."""

    pass


class ConnectionNotFoundError(Exception):
    """Exception raised when connection is not found."""

    pass


class WorkflowValidationError(Exception):
    """Exception raised when workflow validation fails."""

    def __init__(self, validation_result: ValidationResult):
        """Initialize with validation result.

        Args:
            validation_result: The validation result containing errors
        """
        self.validation_result = validation_result
        super().__init__(str(validation_result))


class WorkflowService:
    """Service for managing workflows, nodes, and connections."""

    def __init__(self, db: AsyncSession):
        """Initialize workflow service.

        Args:
            db: Async database session
        """
        self.db = db
        self.validator = WorkflowValidator(db)

    # ========================================================================
    # Workflow CRUD Operations
    # ========================================================================

    async def create_workflow(
        self, workflow_data: WorkflowCreateRequest, workspace_id: UUID, created_by: UUID
    ) -> Workflow:
        """Create a new workflow.

        Args:
            workflow_data: Workflow creation data
            workspace_id: ID of the workspace
            created_by: ID of the user creating the workflow

        Returns:
            Created Workflow object
        """
        workflow = Workflow(
            name=workflow_data.name,
            description=workflow_data.description,
            workspace_id=workspace_id,
            input_schema=workflow_data.input_schema,
            output_schema=workflow_data.output_schema,
            created_by=created_by,
        )

        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)

        return workflow

    async def get_workflow(self, workflow_id: UUID) -> Workflow:
        """Get a workflow by ID.

        Args:
            workflow_id: ID of the workflow

        Returns:
            Workflow object

        Raises:
            WorkflowNotFoundError: If workflow is not found
        """
        workflow = await self.db.get(Workflow, workflow_id)
        if not workflow or workflow.is_deleted:
            raise WorkflowNotFoundError(f'Workflow {workflow_id} not found')

        return workflow

    async def list_workflows(
        self, workspace_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[List[Workflow], int]:
        """List workflows in a workspace.

        Args:
            workspace_id: ID of the workspace
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of workflows, total count)
        """
        # Query workflows
        statement = (
            select(Workflow)
            .where(Workflow.workspace_id == workspace_id)
            .where(~Workflow.is_deleted)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(statement)
        workflows = result.scalars().all()

        # Count total
        count_statement = (
            select(Workflow)
            .where(Workflow.workspace_id == workspace_id)
            .where(~Workflow.is_deleted)
        )
        count_result = await self.db.execute(count_statement)
        total = len(count_result.scalars().all())

        return list(workflows), total

    async def update_workflow(
        self, workflow_id: UUID, workflow_data: WorkflowUpdateRequest
    ) -> Workflow:
        """Update a workflow.

        Args:
            workflow_id: ID of the workflow
            workflow_data: Workflow update data

        Returns:
            Updated Workflow object

        Raises:
            WorkflowNotFoundError: If workflow is not found
        """
        workflow = await self.get_workflow(workflow_id)

        # Update fields
        if workflow_data.name is not None:
            workflow.name = workflow_data.name
        if workflow_data.description is not None:
            workflow.description = workflow_data.description
        if workflow_data.input_schema is not None:
            workflow.input_schema = workflow_data.input_schema
        if workflow_data.output_schema is not None:
            workflow.output_schema = workflow_data.output_schema

        workflow.touch()

        await self.db.commit()
        await self.db.refresh(workflow)

        return workflow

    async def delete_workflow(self, workflow_id: UUID) -> None:
        """Delete a workflow and all its associated data.

        This performs a soft delete on the workflow and cascades to:
        - All nodes in the workflow
        - All connections in the workflow
        - All execution records (hard delete)

        Args:
            workflow_id: ID of the workflow

        Raises:
            WorkflowNotFoundError: If workflow is not found
        """
        workflow = await self.get_workflow(workflow_id)

        # Soft delete the workflow
        workflow.soft_delete()

        # Soft delete all nodes
        nodes_statement = select(Node).where(Node.workflow_id == workflow_id)
        nodes_result = await self.db.execute(nodes_statement)
        nodes = nodes_result.scalars().all()

        for node in nodes:
            if not node.is_deleted:
                node.soft_delete()

        # Delete all execution records (hard delete)
        exec_statement = select(ExecutionRecord).where(ExecutionRecord.workflow_id == workflow_id)
        exec_result = await self.db.execute(exec_statement)
        exec_records = exec_result.scalars().all()

        for record in exec_records:
            await self.db.delete(record)

        await self.db.commit()

    # ========================================================================
    # Node Management Operations
    # ========================================================================

    async def add_node(self, workflow_id: UUID, node_data: NodeCreateRequest) -> Node:
        """Add a node to a workflow.

        Args:
            workflow_id: ID of the workflow
            node_data: Node creation data

        Returns:
            Created Node object

        Raises:
            WorkflowNotFoundError: If workflow is not found
            WorkflowValidationError: If node configuration is invalid
        """
        # Verify workflow exists
        await self.get_workflow(workflow_id)

        # Create node
        node = Node(
            workflow_id=workflow_id,
            type=node_data.type,
            name=node_data.name,
            config=node_data.config,
            position=node_data.position,
        )

        # Validate node configuration
        validation_result = self.validator.validate_node_config(node)
        if not validation_result.is_valid:
            raise WorkflowValidationError(validation_result)

        self.db.add(node)
        await self.db.commit()
        await self.db.refresh(node)

        return node

    async def get_node(self, node_id: UUID) -> Node:
        """Get a node by ID.

        Args:
            node_id: ID of the node

        Returns:
            Node object

        Raises:
            NodeNotFoundError: If node is not found
        """
        node = await self.db.get(Node, node_id)
        if not node or node.is_deleted:
            raise NodeNotFoundError(f'Node {node_id} not found')

        return node

    async def list_nodes(self, workflow_id: UUID) -> List[Node]:
        """List all nodes in a workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            List of Node objects
        """
        statement = select(Node).where(Node.workflow_id == workflow_id).where(~Node.is_deleted)
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def update_node(self, node_id: UUID, node_data: NodeUpdateRequest) -> Node:
        """Update a node.

        Args:
            node_id: ID of the node
            node_data: Node update data

        Returns:
            Updated Node object

        Raises:
            NodeNotFoundError: If node is not found
            WorkflowValidationError: If updated configuration is invalid
        """
        node = await self.get_node(node_id)

        # Update fields
        if node_data.name is not None:
            node.name = node_data.name
        if node_data.config is not None:
            node.config = node_data.config
        if node_data.position is not None:
            node.position = node_data.position

        # Validate updated configuration
        validation_result = self.validator.validate_node_config(node)
        if not validation_result.is_valid:
            raise WorkflowValidationError(validation_result)

        await self.db.commit()
        await self.db.refresh(node)

        return node

    async def delete_node(self, node_id: UUID) -> None:
        """Delete a node from a workflow.

        This performs a soft delete on the node and removes all connections
        involving this node.

        Args:
            node_id: ID of the node

        Raises:
            NodeNotFoundError: If node is not found
        """
        node = await self.get_node(node_id)

        # Soft delete the node
        node.soft_delete()

        # Delete all connections involving this node
        connections_statement = select(Connection).where(
            (Connection.source_node_id == node_id) | (Connection.target_node_id == node_id)
        )
        connections_result = await self.db.execute(connections_statement)
        connections = connections_result.scalars().all()

        for connection in connections:
            await self.db.delete(connection)

        await self.db.commit()

    # ========================================================================
    # Connection Management Operations
    # ========================================================================

    async def connect_nodes(
        self, workflow_id: UUID, connection_data: ConnectionCreateRequest
    ) -> Connection:
        """Create a connection between two nodes.

        Args:
            workflow_id: ID of the workflow
            connection_data: Connection creation data

        Returns:
            Created Connection object

        Raises:
            WorkflowNotFoundError: If workflow is not found
            NodeNotFoundError: If either node is not found
            WorkflowValidationError: If connection would create a cycle
        """
        # Verify workflow exists
        await self.get_workflow(workflow_id)

        # Verify nodes exist
        await self.get_node(connection_data.source_node_id)
        await self.get_node(connection_data.target_node_id)

        # Validate connection
        validation_result = await self.validator.validate_connection(
            connection_data.source_node_id, connection_data.target_node_id, workflow_id
        )
        if not validation_result.is_valid:
            raise WorkflowValidationError(validation_result)

        # Create connection
        connection = Connection(
            workflow_id=workflow_id,
            source_node_id=connection_data.source_node_id,
            target_node_id=connection_data.target_node_id,
            source_output=connection_data.source_output,
            target_input=connection_data.target_input,
        )

        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)

        return connection

    async def get_connection(self, connection_id: UUID) -> Connection:
        """Get a connection by ID.

        Args:
            connection_id: ID of the connection

        Returns:
            Connection object

        Raises:
            ConnectionNotFoundError: If connection is not found
        """
        connection = await self.db.get(Connection, connection_id)
        if not connection:
            raise ConnectionNotFoundError(f'Connection {connection_id} not found')

        return connection

    async def list_connections(self, workflow_id: UUID) -> List[Connection]:
        """List all connections in a workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            List of Connection objects
        """
        statement = select(Connection).where(Connection.workflow_id == workflow_id)
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def delete_connection(self, connection_id: UUID) -> None:
        """Delete a connection.

        Args:
            connection_id: ID of the connection

        Raises:
            ConnectionNotFoundError: If connection is not found
        """
        connection = await self.get_connection(connection_id)

        await self.db.delete(connection)
        await self.db.commit()

    # ========================================================================
    # Workflow Validation Operations
    # ========================================================================

    async def validate_workflow(self, workflow_id: UUID) -> ValidationResult:
        """Validate a complete workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            ValidationResult indicating if workflow is valid
        """
        return await self.validator.validate_workflow(workflow_id)

    async def save_workflow(self, workflow_id: UUID) -> Workflow:
        """Save and validate a workflow.

        This method validates the workflow before saving to ensure it's in a
        consistent state.

        Args:
            workflow_id: ID of the workflow

        Returns:
            Workflow object

        Raises:
            WorkflowNotFoundError: If workflow is not found
            WorkflowValidationError: If workflow validation fails
        """
        workflow = await self.get_workflow(workflow_id)

        # Validate workflow
        validation_result = await self.validate_workflow(workflow_id)
        if not validation_result.is_valid:
            raise WorkflowValidationError(validation_result)

        # Update timestamp
        workflow.touch()
        await self.db.commit()
        await self.db.refresh(workflow)

        return workflow
