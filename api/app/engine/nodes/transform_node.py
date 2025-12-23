"""
Transform Node Executor for data transformation in workflows.

This module implements the transform node executor that can extract,
transform, and manipulate data using JSON paths and various operations.
"""

import json
import re
from typing import Any, Dict, List, Union

import jsonpath_ng

from app.engine.execution_context import ExecutionContext
from app.engine.node_executor import BaseNode, NodeExecutionError, register_node_executor
from app.models.workflow.workflow import Node


@register_node_executor('TRANSFORM')
class TransformNodeExecutor(BaseNode):
    """
    Executor for transform nodes that manipulate and transform data.
    用于处理和转换数据的转换节点的执行器。
    """

    # Supported transformation operations
    SUPPORTED_OPERATIONS = {
        'extract',  # Extract data using JSON path 使用JSON路径提取数据
        'map',  # Map values using a mapping dictionary 使用映射字典映射值
        'filter',  # Filter array elements
        'format',  # Format string with variables
        'convert',  # Convert data types
        'merge',  # Merge multiple objects
        'split',  # Split strings
        'join',  # Join array elements
        'regex',  # Apply regex operations 应用正则表达式操作
        'math',  # Mathematical operations
    }

    def __init__(self):
        """Initialize the transform node executor."""
        super().__init__()

    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """
        Execute transform node by applying data transformations.
        通过应用数据转换来执行转换节点。

        Args:
            node: The transform node to execute
            context: The execution context

        Returns:
            Dictionary containing the transformed data

        Raises:
            NodeExecutionError: If transformation fails
        """
        config = node.config

        # Get inputs for this node
        inputs = context.get_node_input(node, [])

        try:
            # Extract configuration
            operation = config.get('operation', 'extract')
            transformations = config.get('transformations', [])

            if operation not in self.SUPPORTED_OPERATIONS:
                raise NodeExecutionError(
                    f'Unsupported transformation operation: {operation}',
                    node.id,
                    {'operation': operation, 'supported': list(self.SUPPORTED_OPERATIONS)},
                )

            # Apply transformations
            result = await self._apply_transformations(operation, transformations, inputs)

            return {
                'result': result,
                'operation': operation,
                'transformations_applied': transformations,
                'inputs_used': inputs,
            }

        except Exception as e:
            raise NodeExecutionError(
                f'Data transformation failed: {str(e)}',
                node.id,
                {'config': config, 'inputs': inputs},
            ) from e

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate transform node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            True if configuration is valid, False otherwise
        """
        required_fields = ['operation']

        # Check required fields
        for field in required_fields:
            if field not in config or not config[field]:
                return False

        # Validate operation
        operation = config.get('operation', '')
        if operation not in self.SUPPORTED_OPERATIONS:
            return False

        # Validate transformations format
        transformations = config.get('transformations', [])
        if not isinstance(transformations, list):
            return False

        return True

    def get_required_inputs(self) -> List[str]:
        """Get the list of required input parameters.

        Returns:
            List of required input parameter names
        """
        # Transform nodes can work with any inputs
        return []

    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for transform nodes.

        Returns:
            Dictionary describing the output schema
        """
        return {
            'result': {'type': 'any', 'description': 'Transformed data result'},
            'operation': {'type': 'string', 'description': 'Transformation operation applied'},
            'transformations_applied': {
                'type': 'array',
                'description': 'List of transformations applied',
            },
            'inputs_used': {'type': 'object', 'description': 'Input data used for transformation'},
        }

    async def _apply_transformations(
        self, operation: str, transformations: List[Dict[str, Any]], inputs: Dict[str, Any]
    ) -> Any:
        """Apply the specified transformations to the input data.

        Args:
            operation: The main transformation operation
            transformations: List of transformation configurations
            inputs: Input data to transform

        Returns:
            Transformed data

        Raises:
            Exception: If transformation fails
        """
        result = inputs

        for transformation in transformations:
            result = await self._apply_single_transformation(operation, transformation, result)

        return result

    async def _apply_single_transformation(
        self, operation: str, transformation: Dict[str, Any], data: Any
    ) -> Any:
        """Apply a single transformation to the data.

        Args:
            operation: The transformation operation type
            transformation: Transformation configuration
            data: Data to transform

        Returns:
            Transformed data

        Raises:
            Exception: If transformation fails
        """
        if operation == 'extract':
            return self._extract_data(transformation, data)
        elif operation == 'map':
            return self._map_data(transformation, data)
        elif operation == 'filter':
            return self._filter_data(transformation, data)
        elif operation == 'format':
            return self._format_data(transformation, data)
        elif operation == 'convert':
            return self._convert_data(transformation, data)
        elif operation == 'merge':
            return self._merge_data(transformation, data)
        elif operation == 'split':
            return self._split_data(transformation, data)
        elif operation == 'join':
            return self._join_data(transformation, data)
        elif operation == 'regex':
            return self._regex_data(transformation, data)
        elif operation == 'math':
            return self._math_data(transformation, data)
        else:
            raise ValueError(f'Unsupported operation: {operation}')

    def _extract_data(self, config: Dict[str, Any], data: Any) -> Any:
        """Extract data using JSON path.

        Args:
            config: Extraction configuration
            data: Data to extract from

        Returns:
            Extracted data
        """
        json_path = config.get('path', '$')
        default_value = config.get('default')

        try:
            # Parse JSON path
            jsonpath_expr = jsonpath_ng.parse(json_path)

            # Find matches
            matches = jsonpath_expr.find(data)

            if matches:
                # Return first match if single value expected
                if len(matches) == 1:
                    return matches[0].value
                else:
                    return [match.value for match in matches]
            else:
                return default_value

        except Exception as e:
            raise ValueError(f'JSON path extraction failed: {str(e)}') from e

    def _map_data(self, config: Dict[str, Any], data: Any) -> Any:
        """Map data values using a mapping dictionary.

        Args:
            config: Mapping configuration
            data: Data to map

        Returns:
            Mapped data
        """
        mapping = config.get('mapping', {})
        default_value = config.get('default')

        if isinstance(data, list):
            return [mapping.get(item, default_value) for item in data]
        else:
            return mapping.get(data, default_value)

    def _filter_data(self, config: Dict[str, Any], data: Any) -> Any:
        """Filter array elements based on conditions.

        Args:
            config: Filter configuration
            data: Data to filter

        Returns:
            Filtered data
        """
        if not isinstance(data, list):
            raise ValueError('Filter operation requires array input')

        condition = config.get('condition', '')
        field = config.get('field')
        value = config.get('value')

        if condition == 'equals':
            if field:
                return [item for item in data if item.get(field) == value]
            else:
                return [item for item in data if item == value]
        elif condition == 'not_equals':
            if field:
                return [item for item in data if item.get(field) != value]
            else:
                return [item for item in data if item != value]
        elif condition == 'contains':
            if field:
                return [item for item in data if value in str(item.get(field, ''))]
            else:
                return [item for item in data if value in str(item)]
        elif condition == 'greater_than':
            if field:
                return [item for item in data if item.get(field, 0) > value]
            else:
                return [item for item in data if item > value]
        elif condition == 'less_than':
            if field:
                return [item for item in data if item.get(field, 0) < value]
            else:
                return [item for item in data if item < value]
        else:
            raise ValueError(f'Unsupported filter condition: {condition}')

    def _format_data(self, config: Dict[str, Any], data: Any) -> str:
        """Format string with variables.

        Args:
            config: Format configuration
            data: Data to use for formatting

        Returns:
            Formatted string
        """
        template = config.get('template', '')

        if isinstance(data, dict):
            return template.format(**data)
        else:
            return template.format(data)

    def _convert_data(self, config: Dict[str, Any], data: Any) -> Any:
        """Convert data types.

        Args:
            config: Conversion configuration
            data: Data to convert

        Returns:
            Converted data
        """
        target_type = config.get('type', 'string')

        try:
            if target_type == 'string':
                return str(data)
            elif target_type == 'integer':
                return int(data)
            elif target_type == 'float':
                return float(data)
            elif target_type == 'boolean':
                return bool(data)
            elif target_type == 'json':
                if isinstance(data, str):
                    return json.loads(data)
                else:
                    return data
            elif target_type == 'json_string':
                return json.dumps(data)
            else:
                raise ValueError(f'Unsupported conversion type: {target_type}')
        except Exception as e:
            raise ValueError(f'Type conversion failed: {str(e)}') from e

    def _merge_data(self, config: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """Merge multiple objects.

        Args:
            config: Merge configuration
            data: Data to merge

        Returns:
            Merged data
        """
        if not isinstance(data, dict):
            raise ValueError('Merge operation requires dictionary input')

        merge_with = config.get('merge_with', {})
        strategy = config.get('strategy', 'overwrite')  # overwrite, keep_original

        result = data.copy()

        if strategy == 'overwrite':
            result.update(merge_with)
        elif strategy == 'keep_original':
            for key, value in merge_with.items():
                if key not in result:
                    result[key] = value

        return result

    def _split_data(self, config: Dict[str, Any], data: Any) -> List[str]:
        """Split strings.

        Args:
            config: Split configuration
            data: Data to split

        Returns:
            Split data
        """
        if not isinstance(data, str):
            data = str(data)

        delimiter = config.get('delimiter', ',')
        max_splits = config.get('max_splits', -1)

        if max_splits == -1:
            return data.split(delimiter)
        else:
            return data.split(delimiter, max_splits)

    def _join_data(self, config: Dict[str, Any], data: Any) -> str:
        """Join array elements.

        Args:
            config: Join configuration
            data: Data to join

        Returns:
            Joined string
        """
        if not isinstance(data, list):
            raise ValueError('Join operation requires array input')

        delimiter = config.get('delimiter', ',')

        return delimiter.join(str(item) for item in data)

    def _regex_data(self, config: Dict[str, Any], data: Any) -> Any:
        """Apply regex operations.

        Args:
            config: Regex configuration
            data: Data to process

        Returns:
            Processed data
        """
        if not isinstance(data, str):
            data = str(data)

        pattern = config.get('pattern', '')
        operation = config.get('operation', 'match')  # match, search, findall, sub
        replacement = config.get('replacement', '')

        try:
            if operation == 'match':
                match = re.match(pattern, data)
                return match.groups() if match else None
            elif operation == 'search':
                match = re.search(pattern, data)
                return match.groups() if match else None
            elif operation == 'findall':
                return re.findall(pattern, data)
            elif operation == 'sub':
                return re.sub(pattern, replacement, data)
            else:
                raise ValueError(f'Unsupported regex operation: {operation}')
        except Exception as e:
            raise ValueError(f'Regex operation failed: {str(e)}') from e

    def _math_data(self, config: Dict[str, Any], data: Any) -> Union[int, float]:
        """Apply mathematical operations.

        Args:
            config: Math configuration
            data: Data to process

        Returns:
            Calculated result
        """
        operation = config.get('operation', 'add')
        operand = config.get('operand', 0)

        try:
            if not isinstance(data, (int, float)):
                data = float(data)

            if operation == 'add':
                return data + operand
            elif operation == 'subtract':
                return data - operand
            elif operation == 'multiply':
                return data * operand
            elif operation == 'divide':
                return data / operand
            elif operation == 'power':
                return data**operand
            elif operation == 'modulo':
                return data % operand
            elif operation == 'abs':
                return abs(data)
            elif operation == 'round':
                return round(data, operand)
            else:
                raise ValueError(f'Unsupported math operation: {operation}')
        except Exception as e:
            raise ValueError(f'Math operation failed: {str(e)}') from e
