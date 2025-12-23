"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-23 11:45:54
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-23 14:57:34
FilePath: /api/app/engine/nodes/llm_node.py
Description: LLM Node Executor for calling Large Language Models.

This module implements the LLM node executor that handles calls to various
LLM providers. Default provider is Ollama for local model inference.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from collections.abc import Mapping
from typing import Any, Dict, List, Optional

import httpx

from app.engine.execution_context import ExecutionContext
from app.engine.nodes.base.emum import ErrorStrategy, NodeTypeEnum
from app.engine.nodes.base.entities import RetryConfig
from app.engine.nodes.base.node import BaseNode, NodeExecutionError, register_node_executor
from app.models.workflow.workflow import Node


@register_node_executor(NodeTypeEnum.LLM)
class LLMNodeExecutor(BaseNode):
    """Executor for LLM nodes that call language models. Default provider is Ollama."""

    def __init__(self):
        """Initialize the LLM node executor."""
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
        return 'LLM'

    def _get_description(self) -> Optional[str]:
        return None

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
            # Extract configuration - default to Ollama
            provider = config.get('provider', 'ollama')
            model = config.get('model', 'llama2')
            prompt_template = config.get('prompt', '')
            system_prompt = config.get('system_prompt', '')
            temperature = config.get('temperature', 0.7)
            max_tokens = config.get('max_tokens', 1000)
            api_key = config.get('api_key', 'ollama')
            base_url = config.get('base_url', 'http://localhost:11434')
            timeout = config.get('timeout', 120)

            # Render prompt template with inputs
            prompt = self._render_prompt(prompt_template, inputs)

            # Call LLM based on provider
            if provider.lower() == 'ollama':
                response = await self._call_ollama(
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                )
            else:
                raise NodeExecutionError(
                    f'Unsupported LLM provider: {provider}. Use "ollama" provider.',
                    node.id,
                    {'provider': provider},
                )

            return {
                'response': response,
                'model': model,
                'provider': provider,
                'base_url': base_url,
                'prompt_used': prompt,
            }

        except NodeExecutionError:
            raise
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
        # Required fields - model and prompt are required
        if 'model' not in config or not config['model']:
            return False
        if 'prompt' not in config:
            return False

        # Validate provider - only ollama is supported
        provider = config.get('provider', 'ollama')
        if provider.lower() != 'ollama':
            return False

        # Validate base_url format
        base_url = config.get('base_url', 'http://localhost:11434')
        if not base_url.startswith(('http://', 'https://')):
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
            'base_url': {'type': 'string', 'description': 'Ollama API base URL'},
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

    async def _call_ollama(
        self,
        base_url: str,
        api_key: str,
        model: str,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        timeout: int,
    ) -> str:
        """Call Ollama API using OpenAI-compatible endpoint.

        Args:
            base_url: Ollama API base URL (e.g., http://localhost:11434)
            api_key: API key (usually 'ollama')
            model: Model name
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails
        """
        # Build URL for OpenAI-compatible endpoint
        base_url = base_url.rstrip('/')
        if base_url.endswith('/v1'):
            url = f'{base_url}/chat/completions'
        else:
            url = f'{base_url}/v1/chat/completions'

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        data = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            return result['choices'][0]['message']['content']
