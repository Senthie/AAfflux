"""
HTTP Node Executor for making HTTP requests in workflows.

This module implements the HTTP node executor that can make various
types of HTTP requests (GET, POST, PUT, DELETE, etc.) to external APIs.
"""

from typing import Any, Dict, List

import httpx

from app.engine.execution_context import ExecutionContext
from app.engine.node_executor import BaseNode, NodeExecutionError, register_node_executor
from app.models.workflow.workflow import Node


@register_node_executor('HTTP')
class HTTPNodeExecutor(BaseNode):
    """Executor for HTTP nodes that make HTTP requests."""

    # Supported HTTP methods
    SUPPORTED_METHODS = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}

    def __init__(self):
        """Initialize the HTTP node executor."""
        super().__init__()

    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """Execute HTTP node by making an HTTP request.

        Args:
            node: The HTTP node to execute
            context: The execution context

        Returns:
            Dictionary containing the HTTP response

        Raises:
            NodeExecutionError: If HTTP request fails
        """
        config = node.config

        # Get inputs for this node
        inputs = context.get_node_input(node, [])

        try:
            # Extract configuration
            method = config.get('method', 'GET').upper()
            url = config.get('url', '')
            headers = config.get('headers', {})
            params = config.get('params', {})
            body = config.get('body', {})
            timeout = config.get('timeout', 30)
            follow_redirects = config.get('follow_redirects', True)

            # Validate method
            if method not in self.SUPPORTED_METHODS:
                raise NodeExecutionError(
                    f'Unsupported HTTP method: {method}',
                    node.id,
                    {'method': method, 'supported': list(self.SUPPORTED_METHODS)},
                )

            # Render URL with inputs
            url = self._render_template(url, inputs)

            # Render headers with inputs
            rendered_headers = self._render_dict_values(headers, inputs)

            # Render params with inputs
            rendered_params = self._render_dict_values(params, inputs)

            # Render body with inputs
            rendered_body = self._render_body(body, inputs)

            # Make the HTTP request
            response_data = await self._make_request(
                method=method,
                url=url,
                headers=rendered_headers,
                params=rendered_params,
                body=rendered_body,
                timeout=timeout,
                follow_redirects=follow_redirects,
            )

            return {
                'status_code': response_data['status_code'],
                'headers': response_data['headers'],
                'body': response_data['body'],
                'url': response_data['url'],
                'method': method,
                'success': 200 <= response_data['status_code'] < 300,
            }

        except Exception as e:
            raise NodeExecutionError(
                f'HTTP request failed: {str(e)}', node.id, {'config': config, 'inputs': inputs}
            ) from e

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate HTTP node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            True if configuration is valid, False otherwise
        """
        required_fields = ['method', 'url']

        # Check required fields
        for field in required_fields:
            if field not in config or not config[field]:
                return False

        # Validate method
        method = config.get('method', '').upper()
        if method not in self.SUPPORTED_METHODS:
            return False

        # Validate URL format (basic check)
        url = config.get('url', '')
        if not url.startswith(('http://', 'https://')):
            return False

        # Validate timeout
        timeout = config.get('timeout', 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            return False

        # Validate headers format
        headers = config.get('headers', {})
        if not isinstance(headers, dict):
            return False

        # Validate params format
        params = config.get('params', {})
        if not isinstance(params, dict):
            return False

        return True

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
        """Render dictionary values with input variables.

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
            else:
                result[key] = value

        return result

    def _render_body(self, body: Any, inputs: Dict[str, Any]) -> Any:
        """Render request body with input variables.

        Args:
            body: Request body (can be dict, string, etc.)
            inputs: Dictionary of input variables

        Returns:
            Rendered body
        """
        if isinstance(body, dict):
            return self._render_dict_values(body, inputs)
        elif isinstance(body, str):
            return self._render_template(body, inputs)
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
