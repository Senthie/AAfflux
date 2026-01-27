"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/engine/nodes/http/http_node.py
Description: Http Node引擎组件
HTTP Node Executor for making HTTP requests in workflows.

This module implements the HTTP node executor that can make various
types of HTTP requests (GET, POST, PUT, DELETE, etc.) to external APIs.
Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from collections.abc import Mapping
from typing import Any, Dict, List, Optional

import httpx
import json_repair

from app.engine.execution_context import ExecutionContext
from app.engine.nodes.base import (
    BaseNode,
    ErrorStrategy,
    NodeExecutionError,
    RetryConfig,
    register_node_executor,
)
from app.engine.nodes.base.emum import NodeExecutionTypeEnum, NodeTypeEnum
from app.engine.nodes.http.entities import HttpNodeData
from app.models.workflow.workflow import NodeModel
from app.utils.json_path import JsonPathUtil


@register_node_executor(NodeTypeEnum.HTTP)
class HTTPNodeExecutor(BaseNode):
    """Executor for HTTP nodes that make HTTP requests."""

    # Supported HTTP methods
    SUPPORTED_METHODS = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}
    _node_data: HttpNodeData
    execution_type = NodeExecutionTypeEnum.EXECUTABLE

    def __init__(self):
        """Initialize the HTTP node executor."""
        super().__init__()

    @classmethod
    def version(cls) -> str:
        return '1'

    def init_node_data(self, data: Mapping[str, Any]) -> None:
        self._node_data = HttpNodeData.model_validate(data)

    def _get_error_strategy(self) -> Optional[ErrorStrategy]:
        return None

    def _get_retry_config(self) -> RetryConfig:
        return RetryConfig()

    def _get_title(self) -> str:
        return 'HTTP'

    def _get_description(self) -> Optional[str]:
        return None

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate the node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Try to validate the config using the HttpNodeData model
            HttpNodeData.model_validate(config)
            return True
        except Exception:
            return False

    async def execute(self, node: NodeModel, context: ExecutionContext) -> Dict[str, Any]:
        """Execute HTTP node by making an HTTP request.

        Args:
            node: The HTTP node to execute
            context: The execution context

        Returns:
            Dictionary containing the HTTP response

        Raises:
            NodeExecutionError: If HTTP request fails
        """
        self.init_node_data(node.config)

        try:
            # Render URL with inputs
            url = self._render_template(self._node_data.url, {})

            # Render headers with inputs
            rendered_headers = self._render_dict_values(self._node_data.headers, {})

            # Render params with inputs
            rendered_params = self._render_dict_values(self._node_data.params, {})

            # Render body with inputs
            rendered_body = self._render_body(self._node_data.body, context)

            # Make the HTTP request
            response_data = await self._make_request(
                method=self._node_data.method,
                url=url,
                headers=rendered_headers,
                params=rendered_params,
                body=rendered_body,
                timeout=self._node_data.timeout,
                follow_redirects=self._node_data.follow_redirects,
            )

            return {
                'status_code': response_data['status_code'],
                'headers': response_data['headers'],
                'body': response_data['body'],
                'url': response_data['url'],
                'method': self._node_data.method,
                'success': 200 <= response_data['status_code'] < 300,
            }

        except Exception as e:
            raise NodeExecutionError(
                f'HTTP request failed: {str(e)}',
                node.id,
                {'config': node.config},
            ) from e

    def get_required_inputs(self) -> List[str]:
        """Get the list of required input parameters.

        Returns:
            List of required input parameter names
        """
        # HTTP nodes can work with any inputs for templating
        return []

    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for HTTP nodes.

        Returns:
            Dictionary describing the output schema
        """
        return {
            'status_code': {'type': 'integer', 'description': 'HTTP response status code'},
            'headers': {'type': 'object', 'description': 'HTTP response headers'},
            'body': {'type': 'any', 'description': 'HTTP response body (parsed if JSON)'},
            'url': {'type': 'string', 'description': 'Final URL that was requested'},
            'method': {'type': 'string', 'description': 'HTTP method used'},
            'success': {
                'type': 'boolean',
                'description': 'Whether request was successful (2xx status)',
            },
        }

    def _render_template(self, template: str, inputs: Dict[str, Any]) -> str:
        """Render a template string with input variables.

        Args:
            template: Template string with {{variable}} placeholders
            inputs: Dictionary of input variables

        Returns:
            Rendered string
        """
        result = template

        # Simple template rendering - replace {{variable}} with values
        for key, value in inputs.items():
            placeholder = f'{{{{{key}}}}}'
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        return result

    def _render_dict_values(self, data: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Render dictionary values with input variables recursively.

        Args:
            data: Dictionary with template values
            inputs: Dictionary of input variables

        Returns:
            Dictionary with rendered values
        """
        result = {}

        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._render_template(value, inputs)
            elif isinstance(value, dict):
                # Recursively render nested dictionaries
                result[key] = self._render_dict_values(value, inputs)
            elif isinstance(value, list):
                # Render list items
                result[key] = self._render_list_values(value, inputs)
            else:
                result[key] = value

        return result

    def _render_list_values(self, data: list, inputs: Dict[str, Any]) -> list:
        """Render list values with input variables recursively.

        Args:
            data: List with template values
            inputs: Dictionary of input variables

        Returns:
            List with rendered values
        """
        result = []

        for item in data:
            if isinstance(item, str):
                result.append(self._render_template(item, inputs))
            elif isinstance(item, dict):
                result.append(self._render_dict_values(item, inputs))
            elif isinstance(item, list):
                result.append(self._render_list_values(item, inputs))
            else:
                result.append(item)

        return result

    def _render_body(self, body: Any, context: ExecutionContext | None = None) -> Any:
        """Render request body with input variables.

        Args:
            body: Request body (can be dict, string, list, etc.)
            inputs: Dictionary of input variables

        Returns:
            Rendered body*
        """
        if (
            isinstance(body, dict)
            and self._node_data.body_is_expr
            and isinstance(context, ExecutionContext)
        ):
            body = f'{body}'
            exprs = JsonPathUtil.get_exprs(body)
            for expr in exprs:
                value = context.get_node_output(expr.expr)
                body = body.replace(expr.org_name, str(value), 1)
            return json_repair.loads(body)
        elif isinstance(body, list):
            return body
        elif isinstance(body, str):
            return body
        else:
            return body

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
        body: Any,
        timeout: float,
        follow_redirects: bool,
    ) -> Dict[str, Any]:
        """Make the actual HTTP request.

        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            params: Query parameters
            body: Request body
            timeout: Request timeout
            follow_redirects: Whether to follow redirects

        Returns:
            Dictionary with response data

        Raises:
            Exception: If request fails
        """
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=follow_redirects) as client:
            # Prepare request data
            request_kwargs = {'url': url, 'headers': headers, 'params': params}

            # Add body for methods that support it
            if method in {'POST', 'PUT', 'PATCH'}:
                if isinstance(body, dict):
                    # Send as JSON if body is a dict
                    request_kwargs['json'] = body
                elif isinstance(body, str):
                    # Send as text
                    request_kwargs['content'] = body
                elif body is not None:
                    # Send as-is
                    request_kwargs['content'] = body

            # Make the request
            response = await client.request(method, **request_kwargs)

            # Parse response body
            response_body = await self._parse_response_body(response)

            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response_body,
                'url': str(response.url),
            }

    async def _parse_response_body(self, response: httpx.Response) -> Any:
        """Parse HTTP response body.

        Args:
            response: HTTP response object

        Returns:
            Parsed response body
        """
        content_type = response.headers.get('content-type', '').lower()

        try:
            if 'application/json' in content_type:
                return response.json()
            elif 'text/' in content_type or 'application/xml' in content_type:
                return response.text
            else:
                # Return raw bytes for binary content
                return response.content
        except Exception:
            # If parsing fails, return raw text
            try:
                return response.text
            except Exception:
                return response.content
