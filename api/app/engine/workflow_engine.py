"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-10 16:00:21
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-10 16:14:04
FilePath: /api/app/engine/workflow_engine.py
Description: Workflow execution engine.

This module provides the main workflow execution engine that orchestrates
the execution of workflow nodes in the correct order.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.engine.execution_context import ExecutionContext
from app.engine.node_executor import node_executor_registry
from app.engine.topological_sorter import TopologicalSorter
from app.models.workflow.workflow import (
    ConnectionModel,
    ExecutionRecordModel,
    NodeExecutionResultModel,
    NodeModel,
    WorkflowModel,
)
from app.utils.dag import CycleDetectedError


class WorkflowExecutionError(Exception):
    """Exception raised when workflow execution fails."""

    def __init__(
        self, message: str, execution_id: UUID, error_details: Optional[Dict[str, Any]] = None
    ):
        """Initialize workflow execution error.

        Args:
            message: Error message
            execution_id: ID of the execution record
            error_details: Additional error details
        """
        super().__init__(message)
        self.execution_id = execution_id
        self.error_details = error_details or {}


class WorkflowEngine:
    """Main workflow execution engine."""

    def __init__(self, db: AsyncSession):
        """Initialize the workflow engine.

        Args:
            db: Database session
        """
        self.db = db

    async def execute(self, workflow_id: UUID, inputs: Dict[str, Any]) -> ExecutionRecordModel:
        """Execute a workflow synchronously.

        Args:
            workflow_id: ID of the workflow to execute
            inputs: Input data for the workflow

        Returns:
            ExecutionRecord with execution results

        Raises:
            WorkflowExecutionError: If execution fails
        """
        # Load workflow and related data
        workflow = await self._load_workflow(workflow_id)
        nodes = await self._load_nodes(workflow_id)
        connections = await self._load_connections(workflow_id)

        # Validate inputs against workflow schema
        self._validate_inputs(workflow, inputs)

        # Create execution record
        execution_record = await self._create_execution_record(workflow, inputs)

        try:
            # Create execution context
            context = ExecutionContext(workflow, execution_record, inputs)

            # Execute the workflow
            await self._execute_workflow(workflow, nodes, connections, context)

            # Update execution record with results
            await self._finalize_execution_record(execution_record, context)

            return execution_record

        except Exception as e:
            # Mark execution as failed
            await self._mark_execution_failed(execution_record, str(e))
            raise WorkflowExecutionError(
                f'Workflow execution failed: {str(e)}',
                execution_record.id,
                {'workflow_id': workflow_id, 'original_error': str(e)},
            ) from e

    async def execute_async(self, workflow_id: UUID, inputs: Dict[str, Any]) -> UUID:
        """Execute a workflow asynchronously.

        Args:
            workflow_id: ID of the workflow to execute
            inputs: Input data for the workflow

        Returns:
            Execution record ID for tracking

        Note:
            This method starts the execution and returns immediately.
            Use get_execution_status() to check progress.
        """
        # Create execution record first
        workflow = await self._load_workflow(workflow_id)
        execution_record = await self._create_execution_record(workflow, inputs)

        # Start execution in background task
        # In a real implementation, this would use Celery
        asyncio.create_task(self._execute_async_task(workflow_id, inputs, execution_record.id))

        return execution_record.id

    async def get_execution_status(self, execution_id: UUID) -> ExecutionRecordModel:
        """Get the status of a workflow execution.

        Args:
            execution_id: ID of the execution record

        Returns:
            ExecutionRecord with current status

        Raises:
            ValueError: If execution record not found
        """
        execution_record = await self.db.get(ExecutionRecordModel, execution_id)
        if not execution_record:
            raise ValueError(f'Execution record {execution_id} not found')

        return execution_record

    async def _load_workflow(self, workflow_id: UUID) -> WorkflowModel:
        """Load workflow by ID.

        Args:
            workflow_id: ID of the workflow

        Returns:
            Workflow object

        Raises:
            ValueError: If workflow not found
        """
        workflow = await self.db.get(WorkflowModel, workflow_id)
        if not workflow or workflow.is_deleted:
            raise ValueError(f'Workflow {workflow_id} not found')

        return workflow

    async def _load_nodes(self, workflow_id: UUID) -> List[NodeModel]:
        """Load all nodes for a workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            List of nodes
        """
        statement = select(NodeModel).where(
            NodeModel.workflow_id == workflow_id, ~NodeModel.is_deleted
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def _load_connections(self, workflow_id: UUID) -> List[ConnectionModel]:
        """Load all connections for a workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            List of connections
        """
        statement = select(ConnectionModel).where(ConnectionModel.workflow_id == workflow_id)
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    def _validate_inputs(self, workflow: WorkflowModel, inputs: Dict[str, Any]) -> None:
        """Validate inputs against workflow schema.

        Args:
            workflow: The workflow
            inputs: Input data

        Raises:
            ValueError: If inputs are invalid
        """
        # Basic validation - in a real implementation, this would use JSON Schema
        if workflow.input_schema:
            required_fields = workflow.input_schema.get('required', [])
            missing_fields = [field for field in required_fields if field not in inputs]
            if missing_fields:
                raise ValueError(f'Missing required input fields: {missing_fields}')

    async def _create_execution_record(
        self, workflow: WorkflowModel, inputs: Dict[str, Any]
    ) -> ExecutionRecordModel:
        """Create an execution record.

        Args:
            workflow: The workflow being executed
            inputs: Input data

        Returns:
            Created ExecutionRecord
        """
        execution_record = ExecutionRecordModel(
            workflow_id=workflow.id,
            inputs=inputs,
            status='PENDING',
            started_at=datetime.utcnow(),
        )

        self.db.add(execution_record)
        await self.db.commit()
        await self.db.refresh(execution_record)

        return execution_record

    async def _execute_workflow(
        self,
        workflow: WorkflowModel,
        nodes: List[NodeModel],
        connections: List[ConnectionModel],
        context: ExecutionContext,
    ) -> None:
        """Execute the workflow nodes in topological order.

        Args:
            workflow: The workflow
            nodes: List of nodes
            connections: List of connections
            context: Execution context

        Raises:
            CycleDetectedError: If workflow contains cycles
            WorkflowExecutionError: If execution fails
        """
        # Update execution record status
        context.execution_record.status = 'RUNNING'
        await self.db.commit()

        try:
            # Create topological sorter
            sorter = TopologicalSorter(nodes, connections)

            # Get execution order
            sorted_nodes = sorter.sort()

            # Execute nodes in order
            for node in sorted_nodes:
                # Check if execution should continue
                if context.has_execution_failed():
                    break

                # Get executor for this node type
                if not node_executor_registry.is_registered(node.type):
                    raise WorkflowExecutionError(
                        f'No executor registered for node type: {node.type}',
                        context.execution_record.id,
                        {'node_id': str(node.id), 'node_type': node.type},
                    )

                executor = node_executor_registry.get_executor(node.type)

                # Execute the node
                context.current_node = node
                node_result = await executor.execute_with_result(node, context, connections)

                # Save node result
                self.db.add(node_result)
                context.set_node_result(node_result)

                # Commit after each node for progress tracking
                await self.db.commit()

        except CycleDetectedError as e:
            raise WorkflowExecutionError(
                f'Workflow contains cycles: {str(e)}',
                context.execution_record.id,
                {'workflow_id': str(workflow.id)},
            ) from e

    async def _finalize_execution_record(
        self, execution_record: ExecutionRecordModel, context: ExecutionContext
    ) -> None:
        """Finalize the execution record with results.

        Args:
            execution_record: The execution record
            context: Execution context
        """
        execution_record.completed_at = datetime.utcnow()
        execution_record.duration_ms = context._get_execution_time_ms()

        if context.has_execution_failed():
            execution_record.status = 'FAILED'
            execution_record.error = (
                f'Execution failed with {len(context.failed_nodes)} failed nodes'
            )
        else:
            execution_record.status = 'SUCCESS'
            execution_record.outputs = context.get_final_outputs()

        await self.db.commit()

    async def _mark_execution_failed(
        self, execution_record: ExecutionRecordModel, error_message: str
    ) -> None:
        """Mark execution as failed.

        Args:
            execution_record: The execution record
            error_message: Error message
        """
        execution_record.status = 'FAILED'
        execution_record.error = error_message
        execution_record.completed_at = datetime.utcnow()

        # Calculate duration if not set
        if execution_record.duration_ms is None:
            start_time = execution_record.started_at
            end_time = execution_record.completed_at
            if start_time and end_time:
                duration = end_time - start_time
                execution_record.duration_ms = int(duration.total_seconds() * 1000)

        await self.db.commit()

    async def _execute_async_task(
        self, workflow_id: UUID, inputs: Dict[str, Any], execution_id: UUID
    ) -> None:
        """Execute workflow asynchronously.

        This is a placeholder for async execution. In a real implementation,
        this would be handled by Celery tasks.

        Args:
            workflow_id: ID of the workflow
            inputs: Input data
            execution_id: ID of the execution record
        """
        try:
            # Load execution record
            execution_record = await self.db.get(ExecutionRecordModel, execution_id)
            if not execution_record:
                return

            # Execute workflow
            await self.execute(workflow_id, inputs)

        except Exception as e:
            # Mark as failed
            execution_record = await self.db.get(ExecutionRecordModel, execution_id)
            if execution_record:
                await self._mark_execution_failed(execution_record, str(e))

    async def cancel_execution(self, execution_id: UUID) -> bool:
        """Cancel a running workflow execution.

        Args:
            execution_id: ID of the execution to cancel

        Returns:
            True if cancellation was successful, False otherwise
        """
        execution_record = await self.db.get(ExecutionRecordModel, execution_id)
        if not execution_record:
            return False

        if execution_record.status in ['PENDING', 'RUNNING']:
            execution_record.status = 'CANCELLED'
            execution_record.completed_at = datetime.utcnow()
            execution_record.error = 'Execution cancelled by user'

            # Calculate duration
            if execution_record.started_at:
                duration = execution_record.completed_at - execution_record.started_at
                execution_record.duration_ms = int(duration.total_seconds() * 1000)

            await self.db.commit()
            return True

        return False

    async def get_execution_logs(self, execution_id: UUID) -> List[NodeExecutionResultModel]:
        """Get detailed execution logs for a workflow execution.

        Args:
            execution_id: ID of the execution record

        Returns:
            List of node execution results
        """
        statement = select(NodeExecutionResultModel).where(
            NodeExecutionResultModel.execution_record_id == execution_id
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())
