"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-24 16:42:24
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-30 17:04:47
FilePath: /api/app/engine/nodes/base/registry.py
Description: 注册节点

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Any, Dict, Type

from app.engine.nodes.base.emum import NodeTypeEnum

from .entities import BaseNode
from .exc import NodeRegistrationError


class NodeExecutorRegistry:
    """Registry for node executors.

    Manages the mapping between node types and their executor classes.
    """

    def __init__(self):
        """Initialize the registry."""
        self._executors: Dict[str, Type[BaseNode]] = {}
        self._instances: Dict[str, BaseNode] = {}

    def register(self, node_type: str, executor_class: Type[BaseNode]) -> None:
        """Register a node executor for a specific node type.

        Args:
            node_type: The node type identifier (e.g., "LLM", "CONDITION")
            executor_class: The executor class for this node type
        """
        if not issubclass(executor_class, BaseNode):
            raise ValueError('Executor class must inherit from BaseNodeExecutor')

        # 如果 node_type 已经存在，抛出异常
        if node_type in self._executors:
            existing_class = self._executors[node_type].__name__
            raise NodeRegistrationError(
                f'Node type "{node_type}" is already registered with executor: {existing_class}'
            )

        self._executors[node_type] = executor_class

    def get_executor(self, node_type: str) -> BaseNode:
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
def register_node_executor(node_type: NodeTypeEnum):
    """Decorator to register a node executor.

    Args:
        node_type: The node type identifier

    Returns:
        Decorator function
    """

    def decorator(executor_class: Type[BaseNode]):
        # 内层函数：接收要注册的类
        node_executor_registry.register(node_type, executor_class)
        return executor_class  # 返回原类，保持类定义不变

    return decorator
