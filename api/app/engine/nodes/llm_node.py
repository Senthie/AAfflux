"""
LLM Node Executor for calling Large Language Models.

This module implements the LLM node executor that handles calls to various
LLM providers like OpenAI, Anthropic, etc.
"""

from typing import Any, Dict, List

import httpx

from app.engine.execution_context import ExecutionContext
from app.engine.node_executor import BaseNodeExecutor, NodeExecutionError, register_node_executor
from app.models.workflow.workflow import Node


@register_node_executor('LLM')
class LLMNodeExecutor(BaseNodeExecutor):
    """Executor for LLM nodes that call language models."""

    def __init__(self):
        """Initialize the LLM node executor."""
        super().__init__()

    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """Execute LLM node by calling the configured language model.

        Args:
            node: The LLM node to execute
            context: The execution context

        Returns:
            Dictionary containing the LLM response

        Raises:
            NodeExecutionError: If LLM call fails
        """
        config = node.config

        # Get inputs for this node
        inputs = context.get_node_input(node, [])

        try:
            # Extract configuration
            provider = config.get('provider', 'openai')
            model = config.get('model', 'gpt-3.5-turbo')
            prompt_template = config.get('prompt', '')
            temperature = config.get('temperature', 0.7)
            max_tokens = config.get('max_tokens', 1000)
            api_key = config.get('api_key', '')

            # Render prompt template with inputs
            prompt = self._render_prompt(prompt_template, inputs)

            # Call LLM based on provider
            if provider.lower() == 'openai':
                response = await self._call_openai(
                    api_key=api_key,
                    model=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            elif provider.lower() == 'anthropic':
                response = await self._call_anthropic(
                    api_key=api_key,
                    model=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            else:
                raise NodeExecutionError(
                    f'Unsupported LLM provider: {provider}', node.id, {'provider': provider}
                )

            return {
                'response': response,
                'model': model,
                'provider': provider,
                'prompt_used': prompt,
            }

        except Exception as e:
            raise NodeExecutionError(
                f'LLM execution failed: {str(e)}', node.id, {'config': config, 'inputs': inputs}
            ) from e

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate LLM node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            True if configuration is valid, False otherwise
        """
        required_fields = ['provider', 'model', 'prompt', 'api_key']

        # Check required fields
        for field in required_fields:
            if field not in config or not config[field]:
                return False

        # Validate provider
        supported_providers = ['openai', 'anthropic']
        if config['provider'].lower() not in supported_providers:
            return False

        # Validate temperature
        temperature = config.get('temperature', 0.7)
        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
            return False

        # Validate max_tokens
        max_tokens = config.get('max_tokens', 1000)
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            return False

        return True

    def get_required_inputs(self) -> List[str]:
        """Get the list of required input parameters.

        Returns:
            List of required input parameter names
        """
        # LLM nodes can work with any inputs for prompt templating
        return []

    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for LLM nodes.

        Returns:
            Dictionary describing the output schema
        """
        return {
            'response': {'type': 'string', 'description': 'LLM response text'},
            'model': {'type': 'string', 'description': 'Model used for generation'},
            'provider': {'type': 'string', 'description': 'LLM provider used'},
            'prompt_used': {'type': 'string', 'description': 'Final prompt sent to LLM'},
        }

    def _render_prompt(self, template: str, inputs: Dict[str, Any]) -> str:
        """
        Render prompt template with input variables.
        渲染包含输入变量的提示模板。

        Args:
            template: Prompt template string with {{variable}} placeholders
            inputs: Dictionary of input variables

        Returns:
            Rendered prompt string
        """
        prompt = template

        # Simple template rendering - replace {{variable}} with values
        for key, value in inputs.items():
            placeholder = f'{{{{{key}}}}}'
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))

        return prompt

    async def _call_openai(
        self, api_key: str, model: str, prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """Call OpenAI API.

        Args:
            api_key: OpenAI API key
            model: Model name
            prompt: Prompt text
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails
        """
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}

        data = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': temperature,
            'max_tokens': max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            return result['choices'][0]['message']['content']

    async def _call_anthropic(
        self, api_key: str, model: str, prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """Call Anthropic API.

        Args:
            api_key: Anthropic API key
            model: Model name
            prompt: Prompt text
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails
        """
        url = 'https://api.anthropic.com/v1/messages'
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01',
        }

        data = {
            'model': model,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': [{'role': 'user', 'content': prompt}],
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            return result['content'][0]['text']
