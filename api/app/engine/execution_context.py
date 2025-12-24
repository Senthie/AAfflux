"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-10 15:58:38
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-24 12:25:46
FilePath: /api/app/engine/execution_context.py
Description:Execution context management for workflow execution.

This module provides the execution context that maintains state during workflow execution,
including input/output data, node results, and execution metadata.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from app.models.workflow.workflow import ExecutionRecord, Node, NodeExecutionResult, Workflow


class ExecutionContext:
    """
    Context for workflow execution.
    Maintains state and data flow during workflow execution.

    工作流执行的上下文环境。
    在工作流执行过程中维护状态和数据流。
    """

    def __init__(
        self,
        workflow: Workflow,
        execution_record: ExecutionRecord,
        initial_inputs: Dict[str, Any],
    ):
        """
        Initialize execution context.

        Args:
            workflow: The workflow being executed
            execution_record: The execution record for this run
            initial_inputs: Initial input data for the workflow

        初始化执行上下文。

        参数：
            workflow：正在执行的工作流
            execution_record：本次运行的执行记录
            initial_inputs：工作流的初始输入数据
        """
        self.workflow = workflow
        self.execution_record = execution_record
        self.initial_inputs = initial_inputs.copy()

        # Node execution state
        self.node_outputs: Dict[UUID, Dict[str, Any]] = {}
        self.node_results: Dict[UUID, NodeExecutionResult] = {}
        self.completed_nodes: Set[UUID] = set()
        self.failed_nodes: Set[UUID] = set()

        # Global variables available to all nodes
        self.global_variables: Dict[str, Any] = initial_inputs.copy()

        # Execution metadata
        self.start_time = datetime.utcnow()
        self.current_node: Optional[Node] = None

        # workflow connect
        # TOOD: 正常情况下是根据 workflow id 获取，但是目前还没设计
        self.connections = []

    def set_node_output(self, node_id: UUID, outputs: Dict[str, Any]) -> None:
        """
        Set the output data for a node.
        Args:
            node_id: ID of the node
            outputs: Output data from the node

        设置节点的输出数据。
        Args:
            node_id：节点的ID
            outputs：节点的输出数据
        """
        self.node_outputs[node_id] = outputs.copy()

        # Update global variables with node outputs
        # Use node name as prefix to avoid conflicts
        node_result = self.node_results.get(node_id)
        if node_result:
            node_name = self._get_node_name(node_id)
            for key, value in outputs.items():
                self.global_variables[f'{node_name}.{key}'] = value

    def get_node_output(self, node_id: UUID) -> Dict[str, Any]:
        """Get the output data for a node.

        Args:
            node_id: ID of the node

        Returns:
            Output data from the node, or empty dict if not found
        """
        return self.node_outputs.get(node_id, {})

    def get_node_input(self, node: Node, connections: List[Any]) -> Dict[str, Any]:
        """Get input data for a node based on its connections.

        Args:
            node: The node to get inputs for
            connections: List of connections in the workflow

        Returns:
            Dictionary of input data for the node
        """
        inputs = {}

        # Find all connections targeting this node
        for connection in connections:
            if connection.target_node_id == node.id:
                source_outputs = self.get_node_output(connection.source_node_id)

                # Map source output to target input
                if connection.source_output in source_outputs:
                    inputs[connection.target_input] = source_outputs[connection.source_output]

        # If no connections, use global variables for root nodes
        if not inputs:
            inputs = self.global_variables.copy()

        return inputs

    def set_node_result(self, node_result: NodeExecutionResult) -> None:
        """Set the execution result for a node.

        Args:
            node_result: The node execution result
        """
        self.node_results[node_result.node_id] = node_result

        if node_result.status == 'SUCCESS':
            self.completed_nodes.add(node_result.node_id)
            # Set outputs if successful
            if node_result.outputs:
                self.set_node_output(node_result.node_id, node_result.outputs)
        elif node_result.status == 'FAILED':
            self.failed_nodes.add(node_result.node_id)

    def get_node_result(self, node_id: UUID) -> Optional[NodeExecutionResult]:
        """Get the execution result for a node.

        Args:
            node_id: ID of the node

        Returns:
            Node execution result, or None if not found
        """
        return self.node_results.get(node_id)

    def is_node_completed(self, node_id: UUID) -> bool:
        """Check if a node has completed successfully.

        Args:
            node_id: ID of the node

        Returns:
            True if the node completed successfully, False otherwise
        """
        return node_id in self.completed_nodes

    def is_node_failed(self, node_id: UUID) -> bool:
        """Check if a node has failed.

        Args:
            node_id: ID of the node

        Returns:
            True if the node failed, False otherwise
        """
        return node_id in self.failed_nodes

    def has_execution_failed(self) -> bool:
        """Check if the execution has failed.

        Returns:
            True if any node has failed, False otherwise
        """
        return len(self.failed_nodes) > 0

    def get_final_outputs(self) -> Dict[str, Any]:
        """Get the final outputs of the workflow.

        Collects outputs from all leaf nodes (nodes with no dependents).

        Returns:
            Dictionary of final workflow outputs
        """
        # For now, return all global variables as final output
        # In a more sophisticated implementation, this could be based on
        # the workflow's output schema or designated output nodes
        return self.global_variables.copy()

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of the execution.

        Returns:
            Dictionary containing execution statistics and status
        """
        total_nodes = len(self.node_results)
        completed_nodes = len(self.completed_nodes)
        failed_nodes = len(self.failed_nodes)

        return {
            'total_nodes': total_nodes,
            'completed_nodes': completed_nodes,
            'failed_nodes': failed_nodes,
            'success_rate': completed_nodes / total_nodes if total_nodes > 0 else 0,
            'has_failures': failed_nodes > 0,
            'execution_time_ms': self._get_execution_time_ms(),
        }

    def update_global_variable(self, key: str, value: Any) -> None:
        """Update a global variable.

        Args:
            key: Variable name
            value: Variable value
        """
        self.global_variables[key] = value

    def get_global_variable(self, key: str, default: Any = None) -> Any:
        """Get a global variable.

        Args:
            key: Variable name
            default: Default value if key not found

        Returns:
            Variable value or default
        """
        return self.global_variables.get(key, default)

    def _get_node_name(self, node_id: UUID) -> str:
        """Get the name of a node by its ID.

        Args:
            node_id: ID of the node

        Returns:
            Node name or string representation of ID if not found
        """
        # This would need to be populated with actual node data
        # For now, return a placeholder
        return f'node_{str(node_id)[:8]}'

    def _get_execution_time_ms(self) -> int:
        """Get the execution time in milliseconds.

        Returns:
            Execution time in milliseconds
        """
        current_time = datetime.utcnow()
        delta = current_time - self.start_time
        return int(delta.total_seconds() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary representation.

        Returns:
            Dictionary representation of the execution context
        """
        return {
            'workflow_id': str(self.workflow.id),
            'execution_record_id': str(self.execution_record.id),
            'initial_inputs': self.initial_inputs,
            'global_variables': self.global_variables,
            'completed_nodes': [str(node_id) for node_id in self.completed_nodes],
            'failed_nodes': [str(node_id) for node_id in self.failed_nodes],
            'execution_summary': self.get_execution_summary(),
        }
