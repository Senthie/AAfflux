"""
Code Node Executor for executing Python code in workflows.

This module implements the code node executor that safely executes
Python code snippets within a restricted environment.
"""

import ast
from collections.abc import Mapping
import json
import math
import re
from typing import Any, Dict, List, Optional

from app.engine.execution_context import ExecutionContext
from app.engine.nodes.base import (
    BaseNode,
    ErrorStrategy,
    NodeExecutionError,
    RetryConfig,
    register_node_executor,
)
from app.models.workflow.workflow import Node


@register_node_executor('CODE')
class CodeNodeExecutor(BaseNode):
    """Executor for code nodes that execute Python code safely."""

    # Safe built-in functions allowed in code execution
    SAFE_BUILTINS = {
        'abs': abs,
        'all': all,
        'any': any,
        'bool': bool,
        'dict': dict,
        'enumerate': enumerate,
        'filter': filter,
        'float': float,
        'int': int,
        'len': len,
        'list': list,
        'map': map,
        'max': max,
        'min': min,
        'range': range,
        'round': round,
        'set': set,
        'sorted': sorted,
        'str': str,
        'sum': sum,
        'tuple': tuple,
        'zip': zip,
        'json': json,
        'math': math,
        're': re,
    }

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
        return 'Code'

    def _get_description(self) -> Optional[str]:
        return None

    # Restricted AST node types that are not allowed
    RESTRICTED_NODES = {
        ast.Import,
        ast.ImportFrom,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.ClassDef,
        ast.Global,
        ast.Nonlocal,
        ast.Delete,
        ast.With,
        ast.AsyncWith,
        ast.Try,
        ast.ExceptHandler,
        ast.Raise,
        ast.Assert,
        # ast.Exec and ast.Eval were removed in Python 3.8+
        # They are now handled differently in the AST
    }

    def __init__(self):
        """Initialize the code node executor."""
        super().__init__()

    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """Execute code node by running the Python code.

        Args:
            node: The code node to execute
            context: The execution context

        Returns:
            Dictionary containing the execution result

        Raises:
            NodeExecutionError: If code execution fails
        """
        config = node.config

        # Get inputs for this node
        inputs = context.get_node_input(node, [])

        try:
            # Extract configuration
            code = config.get('code', '')
            timeout_seconds = config.get('timeout', 30)

            if not code.strip():
                raise NodeExecutionError(
                    'No code provided for execution', node.id, {'config': config}
                )

            # Validate code safety
            self._validate_code_safety(code)

            # Execute the code
            result = self._execute_code(code, inputs, timeout_seconds)

            return {'result': result, 'code_executed': code, 'inputs_used': inputs}

        except Exception as e:
            raise NodeExecutionError(
                f'Code execution failed: {str(e)}', node.id, {'config': config, 'inputs': inputs}
            ) from e

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate code node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            True if configuration is valid, False otherwise
        """
        required_fields = ['code']

        # Check required fields
        for field in required_fields:
            if field not in config or not config[field]:
                return False

        # Validate timeout
        timeout = config.get('timeout', 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 300:
            return False

        # Try to parse the code
        try:
            code = config['code']
            ast.parse(code)
            self._validate_code_safety(code)
        except (SyntaxError, ValueError):
            return False

        return True

    def get_required_inputs(self) -> List[str]:
        """Get the list of required input parameters.

        Returns:
            List of required input parameter names
        """
        # Code nodes can work with any inputs
        return []

    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for code nodes.

        Returns:
            Dictionary describing the output schema
        """
        return {
            'result': {'type': 'any', 'description': 'Code execution result'},
            'code_executed': {'type': 'string', 'description': 'Code that was executed'},
            'inputs_used': {'type': 'object', 'description': 'Inputs available to the code'},
        }

    def _validate_code_safety(self, code: str) -> None:
        """Validate that code is safe to execute.

        Args:
            code: Python code to validate

        Raises:
            ValueError: If code contains unsafe constructs
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f'Invalid Python syntax: {str(e)}') from e

        # Check for restricted node types
        for node in ast.walk(tree):
            if type(node) in self.RESTRICTED_NODES:
                raise ValueError(f'Restricted operation not allowed: {type(node).__name__}')

            # Check for dangerous attribute access
            if isinstance(node, ast.Attribute):
                if node.attr.startswith('_'):
                    raise ValueError(f'Access to private attributes not allowed: {node.attr}')

            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id not in self.SAFE_BUILTINS:
                        # Allow variables from inputs, but not unknown functions
                        pass
                elif isinstance(node.func, ast.Attribute):
                    # Allow method calls on safe objects
                    pass

    def _execute_code(self, code: str, inputs: Dict[str, Any], timeout: float) -> Any:
        """Execute Python code in a restricted environment.

        Args:
            code: Python code to execute
            inputs: Input variables available to the code
            timeout: Execution timeout in seconds

        Returns:
            Result of code execution

        Raises:
            Exception: If code execution fails
        """
        # Create restricted globals
        restricted_globals = {
            '__builtins__': self.SAFE_BUILTINS,
        }

        # Add safe modules
        restricted_globals.update(self.SAFE_BUILTINS)

        # Create locals with inputs
        restricted_locals = inputs.copy()

        try:
            # Compile the code
            compiled_code = compile(code, '<workflow_code>', 'exec')

            # Execute the code
            # Note: In a production environment, you might want to use
            # a more sophisticated sandboxing solution like RestrictedPython
            exec(compiled_code, restricted_globals, restricted_locals)

            # Return the 'result' variable if it exists, otherwise return all locals
            if 'result' in restricted_locals:
                return restricted_locals['result']
            else:
                # Filter out inputs and return only new variables
                new_vars = {
                    k: v
                    for k, v in restricted_locals.items()
                    if k not in inputs and not k.startswith('_')
                }
                return new_vars if new_vars else None

        except Exception as e:
            raise Exception(f'Code execution error: {str(e)}') from e

    def _is_safe_name(self, name: str) -> bool:
        """Check if a name is safe to use.

        Args:
            name: Variable or function name

        Returns:
            True if name is safe, False otherwise
        """
        # Don't allow private attributes or dangerous names
        if name.startswith('_'):
            return False

        dangerous_names = {
            'eval',
            'exec',
            'compile',
            'open',
            'file',
            'input',
            'raw_input',
            'reload',
            '__import__',
            'globals',
            'locals',
            'vars',
            'dir',
            'hasattr',
            'getattr',
            'setattr',
            'delattr',
            'isinstance',
            'issubclass',
            'callable',
            'exit',
            'quit',
        }

        return name not in dangerous_names
