"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-23 15:29:15
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-29 11:59:10
FilePath: /api/app/engine/nodes/base/entities.py
Description: node 的简单的基类

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from abc import ABC, abstractmethod
from builtins import type as type_
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
import json
from typing import TYPE_CHECKING, Any, Dict, Union

from pydantic import BaseModel, model_validator

from app.engine.nodes.base.emum import ErrorStrategy, NodeExecutionTypeEnum
from app.engine.nodes.base.exc import DefaultValueTypeError, NodeExecutionError
from app.models.workflow.workflow import Node, NodeExecutionResult

if TYPE_CHECKING:
    from app.engine.execution_context import ExecutionContext

_NumberType = Union[int, float]


class RetryConfig(BaseModel):
    """node retry config"""

    max_retries: int = 0  # max retry times
    retry_interval: int = 0  # retry interval in milliseconds
    retry_enabled: bool = False  # whether retry is enabled

    @property
    def retry_interval_seconds(self) -> float:
        return self.retry_interval / 1000


class DefaultValueType(StrEnum):
    STRING = 'string'
    NUMBER = 'number'
    OBJECT = 'object'
    ARRAY_NUMBER = 'array[number]'
    ARRAY_STRING = 'array[string]'
    ARRAY_OBJECT = 'array[object]'
    ARRAY_FILES = 'array[file]'


class DefaultValue(BaseModel):
    value: Any = None
    type: DefaultValueType
    key: str

    @staticmethod
    def _parse_json(value: str):
        """
        Unified JSON parsing handler
        统一的JSON解析处理程序
        """
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise DefaultValueTypeError(f'Invalid JSON format for value: {value}') from e

    @staticmethod
    def _validate_array(value: Any, element_type: type_ | tuple[type_, ...]) -> bool:
        """Unified array type validation"""
        return isinstance(value, list) and all(isinstance(x, element_type) for x in value)

    @staticmethod
    def _convert_number(value: str) -> float:
        """Unified number conversion handler"""
        try:
            return float(value)
        except ValueError as e:
            raise DefaultValueTypeError(f'Cannot convert to number: {value}') from e

    @model_validator(mode='after')
    def validate_value_type(self) -> 'DefaultValue':
        # Type validation configuration
        type_validators = {
            DefaultValueType.STRING: {
                'type': str,
                'converter': lambda x: x,
            },
            DefaultValueType.NUMBER: {
                'type': _NumberType,
                'converter': self._convert_number,
            },
            DefaultValueType.OBJECT: {
                'type': dict,
                'converter': self._parse_json,
            },
            DefaultValueType.ARRAY_NUMBER: {
                'type': list,
                'element_type': _NumberType,
                'converter': self._parse_json,
            },
            DefaultValueType.ARRAY_STRING: {
                'type': list,
                'element_type': str,
                'converter': self._parse_json,
            },
            DefaultValueType.ARRAY_OBJECT: {
                'type': list,
                'element_type': dict,
                'converter': self._parse_json,
            },
        }

        validator: dict[str, Any] = type_validators.get(self.type, {})
        if not validator:
            if self.type == DefaultValueType.ARRAY_FILES:
                # Handle files type
                return self
            raise DefaultValueTypeError(f'Unsupported type: {self.type}')

        # Handle string input cases
        if isinstance(self.value, str) and self.type != DefaultValueType.STRING:
            self.value = validator['converter'](self.value)

        # Validate base type
        if not isinstance(self.value, validator['type']):
            raise DefaultValueTypeError(
                f'Value must be {validator["type"].__name__} type for {self.value}'
            )

        # Validate array element types
        if isinstance(validator['type'], list) and not self._validate_array(
            self.value, validator['element_type']
        ):
            raise DefaultValueTypeError(
                f'All elements must be {validator["element_type"].__name__} for {self.value}'
            )

        return self


class BaseNode(ABC):
    """Base class for all node executors.

    Each node type should implement this interface to define how it executes.
    """

    execution_type: NodeExecutionTypeEnum = NodeExecutionTypeEnum.EXECUTABLE

    def __init__(self):
        """Initialize the node executor."""
        self._initialized = True

    @classmethod
    @abstractmethod
    def version(cls) -> str:
        """`node_version` returns the version of current node type."""
        # NOTE(QuantumGhost): This should be in sync with `NODE_TYPE_CLASSES_MAPPING`.
        #
        # If you have introduced a new node type, please add it to `NODE_TYPE_CLASSES_MAPPING`
        # in `api/core/workflow/nodes/__init__.py`.
        raise NotImplementedError('subclasses of BaseNode must implement `version` method.')

    @abstractmethod
    def init_node_data(self, data: Mapping[str, Any]) -> None: ...

    # Abstract methods that subclasses must implement to provide access
    # to BaseNodeData properties in a type-safe way

    @abstractmethod
    def _get_error_strategy(self) -> ErrorStrategy | None:
        """Get the error strategy for this node."""
        ...

    @abstractmethod
    def _get_retry_config(self) -> RetryConfig:
        """Get the retry configuration for this node."""
        ...

    @abstractmethod
    def _get_title(self) -> str:
        """Get the node title."""
        ...

    @abstractmethod
    def _get_description(self) -> str | None:
        """Get the node description."""
        ...

    @abstractmethod
    async def execute(self, node: Node, context: 'ExecutionContext') -> Dict[str, Any]:
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
        self, node: Node, context: 'ExecutionContext', connections: list
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


class BaseNodeData(ABC, BaseModel):
    """
    节点数据基类，定义所有节点数据的通用属性和行为。

    所有具体节点的数据类都应继承此基类，并根据需要扩展特定属性。

    Attributes:
        title: 节点标题，用于显示和标识节点
        desc: 节点描述，可选，用于说明节点的用途或功能
        version: 节点版本号，默认为 '1'，用于版本控制和兼容性管理
        error_strategy: 错误处理策略，可选，定义节点执行出错时的处理方式
        default_value: 默认值列表，可选，用于设置节点的默认输出值
        retry_config: 重试配置，定义节点执行失败时的重试策略
    """

    title: str
    desc: str | None = None
    version: str = '1'
    error_strategy: ErrorStrategy | None = None
    default_value: list[DefaultValue] | None = None
    retry_config: RetryConfig = RetryConfig()

    @property
    def default_value_dict(self) -> dict[str, Any]:
        """
        将默认值列表转换为字典格式。

        Returns:
            dict[str, Any]: 以 key 为键、value 为值的字典；
                           如果 default_value 为空，则返回空字典
        """
        if self.default_value:
            return {item.key: item.value for item in self.default_value}
        return {}
