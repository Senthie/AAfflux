"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-10 16:01:36
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-10 16:13:50
FilePath: /api/app/tasks/workflow_tasks.py
Description: Celery tasks for workflow execution.

This module provides Celery tasks for asynchronous workflow execution,
allowing workflows to be executed in the background.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Any, Dict
from uuid import UUID

from app.core.celery import celery_app
from app.core.database import get_async_session
from app.engine.workflow_engine import WorkflowEngine
from app.models.workflow.workflow import ExecutionRecordModel


@celery_app.task(bind=True, name='execute_workflow')
def execute_workflow_task(self, workflow_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a workflow asynchronously.

    Args:
        workflow_id: ID of the workflow to execute
        inputs: Input data for the workflow

    Returns:
        Dictionary containing execution results
    """
    import asyncio

    # Convert string ID to UUID
    workflow_uuid = UUID(workflow_id)

    # Update task state
    self.update_state(
        state='PROGRESS', meta={'workflow_id': workflow_id, 'status': 'Starting execution'}
    )

    try:
        # Run the async workflow execution
        result = asyncio.run(_execute_workflow_async(workflow_uuid, inputs, self))

        return {
            'status': 'SUCCESS',
            'execution_id': str(result.id),
            'workflow_id': workflow_id,
            'outputs': result.outputs,
            'duration_ms': result.duration_ms,
        }

    except Exception as e:
        # Update task state with error
        self.update_state(
            state='FAILURE',
            meta={'workflow_id': workflow_id, 'error': str(e), 'error_type': type(e).__name__},
        )
        raise


@celery_app.task(bind=True, name='execute_workflow_with_callback')
def execute_workflow_with_callback_task(
    self, workflow_id: str, inputs: Dict[str, Any], callback_url: str = None
) -> Dict[str, Any]:
    """Execute a workflow with optional callback notification.

    Args:
        workflow_id: ID of the workflow to execute
        inputs: Input data for the workflow
        callback_url: Optional URL to notify when execution completes

    Returns:
        Dictionary containing execution results
    """
    import asyncio

    # Convert string ID to UUID
    workflow_uuid = UUID(workflow_id)

    # Update task state
    self.update_state(
        state='PROGRESS', meta={'workflow_id': workflow_id, 'status': 'Starting execution'}
    )

    try:
        # Run the async workflow execution
        result = asyncio.run(_execute_workflow_async(workflow_uuid, inputs, self))

        execution_result = {
            'status': 'SUCCESS',
            'execution_id': str(result.id),
            'workflow_id': workflow_id,
            'outputs': result.outputs,
            'duration_ms': result.duration_ms,
        }

        # Send callback notification if URL provided
        if callback_url:
            asyncio.run(_send_callback_notification(callback_url, execution_result))

        return execution_result

    except Exception as e:
        error_result = {
            'status': 'FAILURE',
            'workflow_id': workflow_id,
            'error': str(e),
            'error_type': type(e).__name__,
        }

        # Send callback notification for error if URL provided
        if callback_url:
            asyncio.run(_send_callback_notification(callback_url, error_result))

        # Update task state with error
        self.update_state(state='FAILURE', meta=error_result)
        raise


@celery_app.task(name='batch_execute_workflows')
def batch_execute_workflows_task(workflow_executions: list[Dict[str, Any]]) -> Dict[str, Any]:
    """Execute multiple workflows in batch.

    Args:
        workflow_executions: List of workflow execution requests, each containing:
            - workflow_id: ID of the workflow
            - inputs: Input data
            - execution_id: Optional execution ID for tracking

    Returns:
        Dictionary containing batch execution results
    """
    import asyncio

    results = []
    errors = []

    for execution_request in workflow_executions:
        try:
            workflow_id = UUID(execution_request['workflow_id'])
            inputs = execution_request['inputs']

            # Execute workflow
            result = asyncio.run(_execute_workflow_async(workflow_id, inputs))

            results.append(
                {
                    'workflow_id': execution_request['workflow_id'],
                    'execution_id': str(result.id),
                    'status': result.status,
                    'outputs': result.outputs,
                }
            )

        except Exception as e:
            errors.append(
                {
                    'workflow_id': execution_request.get('workflow_id', 'unknown'),
                    'error': str(e),
                    'error_type': type(e).__name__,
                }
            )

    return {
        'total_executions': len(workflow_executions),
        'successful_executions': len(results),
        'failed_executions': len(errors),
        'results': results,
        'errors': errors,
    }


async def _execute_workflow_async(
    workflow_id: UUID, inputs: Dict[str, Any], task=None
) -> ExecutionRecordModel:
    """Execute workflow asynchronously with database session.

    Args:
        workflow_id: ID of the workflow to execute
        inputs: Input data for the workflow
        task: Optional Celery task for progress updates

    Returns:
        ExecutionRecord with results
    """
    # Get database session
    async with get_async_session() as db:
        engine = WorkflowEngine(db)

        # Update task progress if available
        if task:
            task.update_state(
                state='PROGRESS',
                meta={'workflow_id': str(workflow_id), 'status': 'Loading workflow'},
            )

        # Execute workflow
        result = await engine.execute(workflow_id, inputs)

        # Update task progress
        if task:
            task.update_state(
                state='PROGRESS',
                meta={
                    'workflow_id': str(workflow_id),
                    'status': 'Execution completed',
                    'execution_id': str(result.id),
                },
            )

        return result


async def _send_callback_notification(callback_url: str, result: Dict[str, Any]) -> None:
    """Send callback notification to external URL.

    Args:
        callback_url: URL to send notification to
        result: Execution result data
    """
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                callback_url,
                json=result,
                headers={'Content-Type': 'application/json'},
                timeout=30.0,
            )
            response.raise_for_status()
    except Exception as e:
        # Log error but don't fail the task
        print(f'Failed to send callback notification to {callback_url}: {str(e)}')


# Task routing configuration
celery_app.conf.task_routes = {
    'execute_workflow': {'queue': 'workflow_execution'},
    'execute_workflow_with_callback': {'queue': 'workflow_execution'},
    'batch_execute_workflows': {'queue': 'batch_processing'},
}

# Task retry configuration
celery_app.conf.task_annotations = {
    'execute_workflow': {
        'rate_limit': '10/m',  # 10 executions per minute
        'max_retries': 3,
        'default_retry_delay': 60,  # 1 minute
    },
    'execute_workflow_with_callback': {
        'rate_limit': '10/m',
        'max_retries': 3,
        'default_retry_delay': 60,
    },
    'batch_execute_workflows': {
        'rate_limit': '2/m',  # 2 batch executions per minute
        'max_retries': 1,
        'default_retry_delay': 300,  # 5 minutes
    },
}
