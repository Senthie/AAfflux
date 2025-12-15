"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-10 15:59:26
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-10 16:14:14
FilePath: /api/app/engine/node_executor.py
Description: Node executor base class and registry.

This module provides the base class for node executors and a registry system
for managing different node types.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, Type
from uuid import UUID

from app.engine.execution_context import ExecutionContext
from app.models.workflow.workflow import Node, NodeExecutionResult


class NodeExecutionError(Exception):
    """Exception raised when node execution fails."""

    def __init__(self, message: str, node_id: UUID, error_details: Optional[Dict[str, Any]] = None):
        """Initialize node execution error.

        Args:
            message: Error message
            node_id: ID of the node that failed
            error_details: Additional error details
        """
        super().__init__(message)
        self.node_id = node_id
        self.error_details = error_details or {}


class BaseNodeExecutor(ABC):
    """Base class for all node executors.

    Each node type should implement this interface to define how it executes.
    """

    def __init__(self):
        """Initialize the node executor."""
        self._initialized = True

    @abstractmethod
    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """Execute a node and return its outputs.

        Args:
            node: The node to execute
            context: The execution context

        Returns:
            Dictionary of output values

        Raises:
            NodeExecutionError: If execution fails
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate the node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            True if configuration is valid, False otherwise
        """
        pass

    def get_required_inputs(self) -> list[str]:
        """Get the list of required input parameters.

        Returns:
            List of required input parameter names
        """
        return []

    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for this node type.

        Returns:
            Dictionary describing the output schema
        """
        return {}

    async def execute_with_result(
        self, node: Node, context: ExecutionContext, connections: list
    ) -> NodeExecutionResult:
        """Execute a node and create a NodeExecutionResult.

        This method wraps the execute method and handles timing, error handling,
        and result creation.

        Args:
            node: The node to execute
            context: The execution context
            connections: List of connections for input resolution

        Returns:
            NodeExecutionResult with execution details
        """
        start_time = datetime.utcnow()

        try:
            # Get inputs for this node
            inputs = context.get_node_input(node, connections)

            # Validate required inputs
            required_inputs = self.get_required_inputs()
            missing_inputs = [inp for inp in required_inputs if inp not in inputs]
            if missing_inputs:
                raise NodeExecutionError(
                    f'Missing required inputs: {missing_inputs}',
                    node.id,
                    {'missing_inputs': missing_inputs},
                )

            # Execute the node
            outputs = await self.execute(node, context)

            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Create successful result
            result = NodeExecutionResult(
                execution_record_id=context.execution_record.id,
                node_id=node.id,
                status='SUCCESS',
                inputs=inputs,
                outputs=outputs,
                error=None,
                duration_ms=duration_ms,
            )

            return result

        except Exception as e:
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Create failed result
            error_message = str(e)

            result = NodeExecutionResult(
                execution_record_id=context.execution_record.id,
                node_id=node.id,
                status='FAILED',
                inputs=context.get_node_input(node, connections),
                outputs=None,
                error=error_message,
                duration_ms=duration_ms,
            )

            return result


class NodeExecutorRegistry:
    """Registry for node executors.

    Manages the mapping between node types and their executor classes.
    """

    def __init__(self):
        """Initialize the registry."""
        self._executors: Dict[str, Type[BaseNodeExecutor]] = {}
        self._instances: Dict[str, BaseNodeExecutor] = {}

    def register(self, node_type: str, executor_class: Type[BaseNodeExecutor]) -> None:
        """Register a node executor for a specific node type.

        Args:
            node_type: The node type identifier (e.g., "LLM", "CONDITION")
            executor_class: The executor class for this node type
        """
        if not issubclass(executor_class, BaseNodeExecutor):
            raise ValueError('Executor class must inherit from BaseNodeExecutor')

        self._executors[node_type] = executor_class

    def get_executor(self, node_type: str) -> BaseNodeExecutor:
        """Get an executor instance for a node type.

        Args:
            node_type: The node type identifier

        Returns:
            Executor instance for the node type

        Raises:
            ValueError: If node type is not registered
        """
        if node_type not in self._executors:
            raise ValueError(f'No executor registered for node type: {node_type}')

        # Use singleton pattern for executor instances
        if node_type not in self._instances:
            executor_class = self._executors[node_type]
            # 创建一个实例 instances
            self._instances[node_type] = executor_class()

        return self._instances[node_type]

    def is_registered(self, node_type: str) -> bool:
        """Check if a node type is registered.

        Args:
            node_type: The node type identifier

        Returns:
            True if the node type is registered, False otherwise
        """
        return node_type in self._executors

    def get_registered_types(self) -> list[str]:
        """Get all registered node types.

        Returns:
            List of registered node type identifiers
        """
        return list(self._executors.keys())

    def validate_node_config(self, node_type: str, config: Dict[str, Any]) -> bool:
        """Validate configuration for a node type.

        Args:
            node_type: The node type identifier
            config: Node configuration dictionary

        Returns:
            True if configuration is valid, False otherwise

        Raises:
            ValueError: If node type is not registered
        """
        executor = self.get_executor(node_type)
        return executor.validate_config(config)


# Global registry instance
node_executor_registry = NodeExecutorRegistry()


# Decorator for easy registration
def register_node_executor(node_type: str):
    """Decorator to register a node executor.

    Args:
        node_type: The node type identifier

    Returns:
        Decorator function
    """

    def decorator(executor_class: Type[BaseNodeExecutor]):
        # 内层函数：接收要注册的类
        node_executor_registry.register(node_type, executor_class)
        return executor_class  # 返回原类，保持类定义不变

    return decorator


# Basic node executors for common types
@register_node_executor('START')
class StartNodeExecutor(BaseNodeExecutor):
    """Executor for START nodes that pass through initial inputs."""

    def __init__(self):
        """Initialize the start node executor."""
        super().__init__()

    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """Execute start node by returning initial inputs.

        Args:
            node: The start node
            context: The execution context

        Returns:
            Initial workflow inputs
        """
        return context.initial_inputs

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate start node configuration.

        Args:
            config: Node configuration

        Returns:
            Always True for start nodes
        """
        return True


@register_node_executor('END')
class EndNodeExecutor(BaseNodeExecutor):
    """Executor for END nodes that collect final outputs."""

    def __init__(self):
        """Initialize the end node executor."""
        super().__init__()

    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """Execute end node by collecting inputs as final outputs.

        Args:
            node: The end node
            context: The execution context

        Returns:
            Collected inputs as final outputs
        """
        # Get all inputs to this node
        inputs = context.get_node_input(node, [])
        return inputs

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate end node configuration.

        Args:
            config: Node configuration

        Returns:
            Always True for end nodes
        """
        return True


@register_node_executor('PASSTHROUGH')
class PassthroughNodeExecutor(BaseNodeExecutor):
    """
    Executor for PASSTHROUGH nodes that pass inputs to outputs unchanged.
    用于将输入原样传递给输出的直通节点执行器。
    """

    def __init__(self):
        """Initialize the passthrough node executor."""
        super().__init__()

    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """Execute passthrough node by returning inputs unchanged.

        Args:
            node: The passthrough node
            context: The execution context

        Returns:
            Input data unchanged
        """
        inputs = context.get_node_input(node, [])
        return inputs

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate passthrough node configuration.

        Args:
            config: Node configuration

        Returns:
            Always True for passthrough nodes
        """
        return True
