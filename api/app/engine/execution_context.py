"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-10 15:58:38
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-02-09 12:31:18
FilePath: /api/app/engine/execution_context.py
Description:Execution context management for workflow execution.

This module provides the execution context that maintains state during workflow execution,
including input/output data, node results, and execution metadata.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from jsonpath_ng import parse

from app.engine.nodes.base.emum import NodeExecutionResultStatusEnum
from app.models.workflow.workflow import (
    ConnectionModel,
    ExecutionRecordModel,
    NodeExecutionResultModel,
    NodeModel,
)
from app.schemas.workflow_engine_execution import WorkflowEngineModel


class ExecutionContext:
    """
    Context for workflow execution.
    Maintains state and data flow during workflow execution.

    工作流执行的上下文环境。
    在工作流执行过程中维护状态和数据流。
    """

    def __init__(
        self,
        workflow: WorkflowEngineModel,  # Can be WorkflowModel or WorkflowResponse
        execution_record: ExecutionRecordModel,
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
        # Global variables available to all nodes
        self.global_variables: Dict[str, Any] = {}

        # Node execution state
        self.node_outputs: Dict[str, Dict[str, Dict[str, Any]]] = {'outputs': {}}
        self.node_results: Dict[UUID, NodeExecutionResultModel] = {}

        self.completed_nodes: Set[UUID] = set()
        self.failed_nodes: Set[UUID] = set()

        # Execution metadata 执行元数据
        self.start_time = datetime.utcnow()
        self.current_node: Optional[NodeModel] = None

        self.adjacency_list: Dict[UUID, List[UUID]] = {}

    def set_node_output(self, node_result: NodeExecutionResultModel) -> None:
        """
        Set the output data for a node.
        Args:
            node_result: node result

        example:
        ```
            self.node_outputs = {
                'outputs': {
                    'node_title': {
                        'output': _node_outputs
                    }
                }
            }

        ```
        """
        node_title = ''
        _node_outputs = {}
        # 获取node 的原始数据
        if node_result.outputs is not None:
            node_title = node_result.outputs.get('title', str(node_result.node_id))
            _node_outputs = node_result.outputs.get('output', {})
        # 对 node_title 将空格替换为下划线
        node_title = node_title.replace(' ', '_')

        # 以 output 为根节点，设置返回值
        self.node_outputs['outputs'][node_title] = _node_outputs

    def get_node_output(self, expr: str) -> Dict[str, Any] | str | int | None:
        """Get the output data for a node.

        Args:
            expr: jsonpath 的语法格式

        Returns:
            返回对应的json path 解析后的数据

        example:
        """
        # 将空格替换为下划线
        expr = expr.replace(' ', '_')
        jsonpath_expr = parse(expr)
        for match in jsonpath_expr.find(self.node_outputs):
            return match.value
        return None

    def set_node_result(self, node_result: NodeExecutionResultModel) -> None:
        """Set the execution result for a node.

        Args:
            node_result: The node execution result
        """
        self.node_results[node_result.node_id] = node_result

        if node_result.status.lower() == NodeExecutionResultStatusEnum.SUCCESS.lower():
            self.completed_nodes.add(node_result.node_id)
            # Set outputs if successful
            if node_result.outputs:
                # 使用 node_id 构建一个简单的 node 字典
                self.set_node_output(node_result)
        elif node_result.status == 'FAILED':
            self.failed_nodes.add(node_result.node_id)

    def get_node_result(self, node_id: UUID) -> Optional[NodeExecutionResultModel]:
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
            Dictionary of final workflow outputs (JSON-serializable only)
        """
        # Return the node_outputs which contains only serializable data
        # instead of global_variables which may contain Node instances
        return self.node_outputs.copy()

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

    def _get_node_by_id(self, node_id: UUID) -> NodeModel:
        """Get the name of a node by its ID.

        Args:
            node_id: ID of the node

        Returns:
            Node or string representation of ID if not found
        """
        for node in self.workflow.graph.nodes:
            if node.id == node_id:
                return node

        raise ValueError(f'Node with id {node_id} not found')

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
            'global_variables': self.global_variables,
            'completed_nodes': [str(node_id) for node_id in self.completed_nodes],
            'failed_nodes': [str(node_id) for node_id in self.failed_nodes],
            'execution_summary': self.get_execution_summary(),
        }

    def get_connections(self) -> List[ConnectionModel]:
        """Get the connections in the workflow.

        Returns:
            List of connections
        """

        return self.workflow.graph.connections

    def get_adjacency_list(self) -> Dict[UUID, List[UUID]]:
        """Get the adjacency list of the workflow.

        Returns:
            Dictionary representing the adjacency list
        """
        return self.adjacency_list

    def set_adjacency_list(self, adjacency_list: Dict[UUID, List[UUID]]) -> None:
        """Set the adjacency list of the workflow.

        Args:
            adjacency_list: Dictionary representing the adjacency list
        """
        self.adjacency_list = adjacency_list
