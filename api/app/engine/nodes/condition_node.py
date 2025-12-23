"""
Condition Node Executor for conditional branching in workflows.

This module implements the condition node executor that evaluates expressions
and routes workflow execution based on the results.
"""

import ast
from collections.abc import Mapping
import operator
from typing import Any, Dict, List, Optional

from app.engine.execution_context import ExecutionContext
from app.engine.nodes.base.emum import ErrorStrategy
from app.engine.nodes.base.entities import RetryConfig
from app.engine.nodes.base.node import BaseNode, NodeExecutionError, register_node_executor
from app.models.workflow.workflow import Node


@register_node_executor('CONDITION')
class ConditionNodeExecutor(BaseNode):
    """Executor for condition nodes that perform conditional branching."""

    # Safe operators for expression evaluation
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.And: operator.and_,
        ast.Or: operator.or_,
        ast.Not: operator.not_,
        ast.In: lambda x, y: x in y,
        ast.NotIn: lambda x, y: x not in y,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
    }

    def __init__(self):
        """Initialize the condition node executor."""
        super().__init__()

    @classmethod
    def version(cls) -> str:
        return '1'

    def init_node_data(self, data: Mapping[str, Any]) -> None:
        pass

    def _get_error_strategy(self) -> Optional[ErrorStrategy]:
        return None

    def _get_retry_config(self) -> RetryConfig:
        return RetryConfig()

    def _get_title(self) -> str:
        return 'Condition'

    def _get_description(self) -> Optional[str]:
        return None

    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """Execute condition node by evaluating the condition expression.

        Args:
            node: The condition node to execute
            context: The execution context

        Returns:
            Dictionary containing the evaluation result and branch path

        Raises:
            NodeExecutionError: If condition evaluation fails
        """
        config = node.config

        # Get inputs for this node
        inputs = context.get_node_input(node, [])

        try:
            # Extract configuration
            condition_expression = config.get('condition', 'True')
            true_branch = config.get('true_branch', 'true')
            false_branch = config.get('false_branch', 'false')

            # Evaluate the condition
            result = self._evaluate_condition(condition_expression, inputs)

            # Determine branch path
            branch_path = true_branch if result else false_branch

            return {
                'result': result,
                'branch': branch_path,
                'condition': condition_expression,
                'inputs_used': inputs,
            }

        except Exception as e:
            raise NodeExecutionError(
                f'Condition evaluation failed: {str(e)}',
                node.id,
                {'config': config, 'inputs': inputs},
            ) from e

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate condition node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            True if configuration is valid, False otherwise
        """
        required_fields = ['condition']

        # Check required fields
        for field in required_fields:
            if field not in config or not config[field]:
                return False

        # Try to parse the condition expression
        try:
            condition = config['condition']
            ast.parse(condition, mode='eval')
        except SyntaxError:
            return False

        return True

    def get_required_inputs(self) -> List[str]:
        """Get the list of required input parameters.

        Returns:
            List of required input parameter names
        """
        # Condition nodes can work with any inputs for expression evaluation
        return []

    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for condition nodes.

        Returns:
            Dictionary describing the output schema
        """
        return {
            'result': {'type': 'boolean', 'description': 'Condition evaluation result'},
            'branch': {'type': 'string', 'description': 'Selected branch path'},
            'condition': {'type': 'string', 'description': 'Condition expression evaluated'},
            'inputs_used': {'type': 'object', 'description': 'Inputs used in evaluation'},
        }

    def _evaluate_condition(self, expression: str, variables: Dict[str, Any]) -> bool:
        """Safely evaluate a condition expression.

        Args:
            expression: The condition expression to evaluate
            variables: Dictionary of variables available for evaluation

        Returns:
            Boolean result of the condition evaluation

        Raises:
            ValueError: If expression is invalid or unsafe
            Exception: If evaluation fails
        """
        try:
            # Parse the expression
            tree = ast.parse(expression, mode='eval')

            # Evaluate the expression safely
            result = self._eval_node(tree.body, variables)

            # Ensure result is boolean
            return bool(result)

        except Exception as e:
            raise ValueError(f'Failed to evaluate condition "{expression}": {str(e)}') from e

    def _eval_node(self, node: ast.AST, variables: Dict[str, Any]) -> Any:
        """
        Recursively evaluate an AST node safely.
        安全地递归评估抽象语法树节点。

        Args:
            node: AST node to evaluate AST节点评估
            variables: Available variables 可用变量

        Returns:
            Evaluation result 评估结果

        Raises:
            ValueError: If node type is not supported
        """
        if isinstance(node, ast.Constant):
            return node.value

        # 返回对应的id 的值
        elif isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            else:
                raise ValueError(f'Variable "{node.id}" not found')

        # 二元运算符
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, variables)
            right = self._eval_node(node.right, variables)
            op_func = self.SAFE_OPERATORS.get(type(node.op))
            if op_func:
                return op_func(left, right)
            else:
                raise ValueError(f'Unsupported binary operator: {type(node.op)}')

        # 一元运算符
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, variables)
            op_func = self.SAFE_OPERATORS.get(type(node.op))
            if op_func:
                return op_func(operand)
            else:
                raise ValueError(f'Unsupported unary operator: {type(node.op)}')

        # 比较运算符
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, variables)
            result = True

            for op, comparator in zip(node.ops, node.comparators, strict=True):
                right = self._eval_node(comparator, variables)
                op_func = self.SAFE_OPERATORS.get(type(op))
                if op_func:
                    result = result and op_func(left, right)
                    left = right  # For chained comparisons
                else:
                    raise ValueError(f'Unsupported comparison operator: {type(op)}')

                if not result:
                    break

            return result

        # 布偶运算
        elif isinstance(node, ast.BoolOp):
            values = [self._eval_node(value, variables) for value in node.values]
            op_func = self.SAFE_OPERATORS.get(type(node.op))
            if op_func:
                if isinstance(node.op, ast.And):
                    return all(values)
                elif isinstance(node.op, ast.Or):
                    return any(values)
            raise ValueError(f'Unsupported boolean operator: {type(node.op)}')

        elif isinstance(node, ast.List):
            return [self._eval_node(item, variables) for item in node.elts]

        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_node(item, variables) for item in node.elts)

        elif isinstance(node, ast.Dict):
            result = {}
            for key_node, value_node in zip(node.keys, node.values, strict=True):
                key = self._eval_node(key_node, variables)
                value = self._eval_node(value_node, variables)
                result[key] = value
            return result

        elif isinstance(node, ast.Subscript):
            obj = self._eval_node(node.value, variables)
            key = self._eval_node(node.slice, variables)
            return obj[key]

        elif isinstance(node, ast.Attribute):
            obj = self._eval_node(node.value, variables)
            return getattr(obj, node.attr)

        else:
            raise ValueError(f'Unsupported AST node type: {type(node)}')
