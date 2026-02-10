"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-10 15:59:26
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-02-09 10:30:55
FilePath: /api/app/engine/nodes/base/node.py
Description: Node executor base class and registry.

This module provides the base class for node executors and a registry system
for managing different node types.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Dict, Optional

from app.engine.nodes.base.emum import ErrorStrategy, NodeTypeEnum
from app.engine.nodes.base.entities import BaseNode, RetryConfig
from app.engine.nodes.base.registry import register_node_executor
from app.models.workflow.workflow import NodeModel

if TYPE_CHECKING:
    from app.engine.execution_context import ExecutionContext


# Basic node executors for common types
@register_node_executor(NodeTypeEnum.ROOT)
class StartNodeExecutor(BaseNode):
    """Executor for START nodes that pass through initial inputs."""

    def __init__(self):
        """Initialize the start node executor."""
        super().__init__()

    @classmethod
    def version(cls) -> str:
        return '1'

    def init_node_data(self, data: Mapping[str, Any]) -> None:
        pass

    def _get_error_strategy(self) -> Optional['ErrorStrategy']:
        return None

    def _get_retry_config(self) -> 'RetryConfig':
        return RetryConfig()

    def _get_title(self) -> str:
        return 'Start'

    def _get_description(self) -> Optional[str]:
        return None

    async def execute(self, node: NodeModel, context: 'ExecutionContext') -> Dict[str, Any]:
        """Execute start node by returning initial inputs.

        Args:
            node: The start node
            context: The execution context

        Returns:
            Initial workflow inputs
        """
        return {}

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate start node configuration.

        Args:
            config: Node configuration

        Returns:
            Always True for start nodes
        """
        return True


@register_node_executor(NodeTypeEnum.END)
class EndNodeExecutor(BaseNode):
    """Executor for END nodes that collect final outputs."""

    def __init__(self):
        """Initialize the end node executor."""
        super().__init__()

    @classmethod
    def version(cls) -> str:
        return '1'

    def init_node_data(self, data: Mapping[str, Any]) -> None:
        pass

    def _get_error_strategy(self) -> Optional['ErrorStrategy']:
        return None

    def _get_retry_config(self) -> 'RetryConfig':
        return RetryConfig()

    def _get_title(self) -> str:
        return 'End'

    def _get_description(self) -> Optional[str]:
        return None

    async def execute(self, node: NodeModel, context: 'ExecutionContext'):
        """Execute end node by collecting inputs as final outputs.

        Args:
            node: The end node
            context: The execution context

        Returns:
            Collected inputs as final outputs
        """
        # Get all inputs to this node

        return {}

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate end node configuration.

        Args:
            config: Node configuration

        Returns:
            Always True for end nodes
        """
        return True


@register_node_executor(NodeTypeEnum.PASSTHROUGH)
class PassthroughNodeExecutor(BaseNode):
    """
    Executor for PASSTHROUGH nodes that pass inputs to outputs unchanged.
    用于将输入原样传递给输出的直通节点执行器。
    """

    def __init__(self):
        """Initialize the passthrough node executor."""
        super().__init__()

    @classmethod
    def version(cls) -> str:
        return '1'

    def init_node_data(self, data: Mapping[str, Any]) -> None:
        pass

    def _get_error_strategy(self) -> Optional['ErrorStrategy']:
        return None

    def _get_retry_config(self) -> 'RetryConfig':
        return RetryConfig()

    def _get_title(self) -> str:
        return 'Passthrough'

    def _get_description(self) -> Optional[str]:
        return None

    async def execute(self, node: NodeModel, context: 'ExecutionContext') -> Dict[str, Any]:
        """Execute passthrough node by returning inputs unchanged.

        Args:
            node: The passthrough node
            context: The execution context

        Returns:
            Input data unchanged
        """
        inputs = {}
        return inputs

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate passthrough node configuration.

        Args:
            config: Node configuration

        Returns:
            Always True for passthrough nodes
        """
        return True
