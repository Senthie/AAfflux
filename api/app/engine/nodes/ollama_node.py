"""
Ollama Node Executor for calling local Ollama models.

This module implements the Ollama node executor that handles calls to
user-provided Ollama API endpoints.
"""

from typing import Any, Dict, List

import httpx

from app.engine.execution_context import ExecutionContext
from app.engine.node_executor import BaseNode, NodeExecutionError, register_node_executor
from app.models.workflow.workflow import Node


@register_node_executor('OLLAMA')
class OllamaNodeExecutor(BaseNode):
    """
    Executor for Ollama nodes that call local Ollama models.
    用户可以自行提供 Ollama API 接口地址。
    支持三种API模式：
    1. openai_compatible: OpenAI兼容模式 (/v1/chat/completions)
    2. native_chat: 原生Ollama Chat模式 (/api/chat)
    3. native_generate: 原生Ollama Generate模式 (/api/generate)
    """

    def __init__(self):
        """Initialize the Ollama node executor."""
        super().__init__()

    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """Execute Ollama node by calling the configured Ollama API.

        Args:
            node: The Ollama node to execute
            context: The execution context

        Returns:
            Dictionary containing the Ollama response

        Raises:
            NodeExecutionError: If Ollama call fails
        """
        config = node.config
        inputs = context.get_node_input(node, [])

        try:
            # Extract configuration
            base_url = config.get('base_url', 'http://localhost:11434')
            model = config.get('model', 'llama2')
            prompt_template = config.get('prompt', '')
            system_prompt = config.get('system_prompt', '')
            temperature = config.get('temperature', 0.7)
            max_tokens = config.get('max_tokens', 1000)
            num_predict = config.get('num_predict', max_tokens)
            top_p = config.get('top_p', 0.9)
            top_k = config.get('top_k', 40)
            repeat_penalty = config.get('repeat_penalty', 1.1)
            stream = config.get('stream', False)
            timeout = config.get('timeout', 120)
            api_key = config.get('api_key', 'ollama')

            # Render prompt template with inputs
            prompt = self._render_prompt(prompt_template, inputs)

            # Determine API mode
            # openai_compatible: /v1/chat/completions (default, 兼容你的配置)
            # native_chat: /api/chat
            # native_generate: /api/generate
            api_mode = config.get('api_mode', 'openai_compatible')

            if api_mode == 'openai_compatible':
                response = await self._call_openai_compatible_api(
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    timeout=timeout,
                )
            elif api_mode == 'native_chat':
                response = await self._call_chat_api(
                    base_url=base_url,
                    model=model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    num_predict=num_predict,
                    top_p=top_p,
                    top_k=top_k,
                    repeat_penalty=repeat_penalty,
                    stream=stream,
                    timeout=timeout,
                )
            else:  # native_generate
                response = await self._call_generate_api(
                    base_url=base_url,
                    model=model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    num_predict=num_predict,
                    top_p=top_p,
                    top_k=top_k,
                    repeat_penalty=repeat_penalty,
                    stream=stream,
                    timeout=timeout,
                )

            return {
                'response': response,
                'model': model,
                'provider': 'ollama',
                'base_url': base_url,
                'prompt_used': prompt,
                'api_mode': api_mode,
            }

        except NodeExecutionError:
            raise
        except Exception as e:
            raise NodeExecutionError(
                f'Ollama execution failed: {str(e)}',
                node.id,
                {'config': config, 'inputs': inputs},
            ) from e

    async def _call_openai_compatible_api(
        self,
        base_url: str,
        api_key: str,
        model: str,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        timeout: int,
    ) -> str:
        """Call Ollama OpenAI-compatible API (/v1/chat/completions).

        Args:
            base_url: Ollama API base URL (e.g., http://localhost:11434/v1/)
            api_key: API key (usually 'ollama')
            model: Model name
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling
            timeout: Request timeout in seconds

        Returns:
            Generated text response
        """
        # 处理 base_url，确保正确拼接
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
            'top_p': top_p,
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Ollama node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            True if configuration is valid, False otherwise
        """
        # Required fields
        if 'model' not in config or not config['model']:
            return False

        # Validate base_url format
        base_url = config.get('base_url', 'http://localhost:11434')
        if not base_url.startswith(('http://', 'https://')):
            return False

        # Validate temperature
        temperature = config.get('temperature', 0.7)
        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
            return False

        # Validate num_predict
        num_predict = config.get('num_predict', 1000)
        if not isinstance(num_predict, int) or num_predict <= 0:
            return False

        # Validate top_p
        top_p = config.get('top_p', 0.9)
        if not isinstance(top_p, (int, float)) or top_p < 0 or top_p > 1:
            return False

        # Validate top_k
        top_k = config.get('top_k', 40)
        if not isinstance(top_k, int) or top_k < 0:
            return False

        return True

    def get_required_inputs(self) -> List[str]:
        """Get the list of required input parameters."""
        return []

    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for Ollama nodes."""
        return {
            'response': {'type': 'string', 'description': 'Ollama model response text'},
            'model': {'type': 'string', 'description': 'Model used for generation'},
            'provider': {'type': 'string', 'description': 'Provider name (ollama)'},
            'base_url': {'type': 'string', 'description': 'Ollama API base URL'},
            'prompt_used': {'type': 'string', 'description': 'Final prompt sent to Ollama'},
        }

    def _render_prompt(self, template: str, inputs: Dict[str, Any]) -> str:
        """Render prompt template with input variables."""
        prompt = template
        for key, value in inputs.items():
            placeholder = f'{{{{{key}}}}}'
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))
        return prompt

    async def _call_chat_api(
        self,
        base_url: str,
        model: str,
        prompt: str,
        system_prompt: str,
        temperature: float,
        num_predict: int,
        top_p: float,
        top_k: int,
        repeat_penalty: float,
        stream: bool,
        timeout: int,
    ) -> str:
        """Call Ollama Chat API (/api/chat).

        Args:
            base_url: Ollama API base URL
            model: Model name
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            num_predict: Maximum tokens to generate
            top_p: Top-p sampling
            top_k: Top-k sampling
            repeat_penalty: Repeat penalty
            stream: Whether to stream response
            timeout: Request timeout in seconds

        Returns:
            Generated text response
        """
        url = f'{base_url.rstrip("/")}/api/chat'

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        data = {
            'model': model,
            'messages': messages,
            'stream': stream,
            'options': {
                'temperature': temperature,
                'num_predict': num_predict,
                'top_p': top_p,
                'top_k': top_k,
                'repeat_penalty': repeat_penalty,
            },
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            if stream:
                return await self._handle_stream_response(client, url, data)
            else:
                response = await client.post(url, json=data)
                response.raise_for_status()
                result = response.json()
                return result['message']['content']

    async def _call_generate_api(
        self,
        base_url: str,
        model: str,
        prompt: str,
        system_prompt: str,
        temperature: float,
        num_predict: int,
        top_p: float,
        top_k: int,
        repeat_penalty: float,
        stream: bool,
        timeout: int,
    ) -> str:
        """Call Ollama Generate API (/api/generate).

        Args:
            base_url: Ollama API base URL
            model: Model name
            prompt: Prompt text
            system_prompt: System prompt
            temperature: Sampling temperature
            num_predict: Maximum tokens to generate
            top_p: Top-p sampling
            top_k: Top-k sampling
            repeat_penalty: Repeat penalty
            stream: Whether to stream response
            timeout: Request timeout in seconds

        Returns:
            Generated text response
        """
        url = f'{base_url.rstrip("/")}/api/generate'

        data = {
            'model': model,
            'prompt': prompt,
            'stream': stream,
            'options': {
                'temperature': temperature,
                'num_predict': num_predict,
                'top_p': top_p,
                'top_k': top_k,
                'repeat_penalty': repeat_penalty,
            },
        }

        if system_prompt:
            data['system'] = system_prompt

        async with httpx.AsyncClient(timeout=timeout) as client:
            if stream:
                return await self._handle_stream_response(client, url, data)
            else:
                response = await client.post(url, json=data)
                response.raise_for_status()
                result = response.json()
                return result['response']

    async def _handle_stream_response(
        self,
        client: httpx.AsyncClient,
        url: str,
        data: Dict[str, Any],
    ) -> str:
        """Handle streaming response from Ollama.

        Args:
            client: HTTP client
            url: API URL
            data: Request data

        Returns:
            Complete generated text
        """
        import json

        full_response = []

        async with client.stream('POST', url, json=data) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    # Chat API returns 'message.content', Generate API returns 'response'
                    if 'message' in chunk:
                        content = chunk['message'].get('content', '')
                    else:
                        content = chunk.get('response', '')
                    full_response.append(content)

        return ''.join(full_response)

    async def list_models(self, base_url: str = 'http://localhost:11434') -> List[str]:
        """List available models from Ollama server.

        Args:
            base_url: Ollama API base URL

        Returns:
            List of available model names
        """
        url = f'{base_url.rstrip("/")}/api/tags'

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            result = response.json()
            return [model['name'] for model in result.get('models', [])]

    async def check_connection(self, base_url: str = 'http://localhost:11434') -> bool:
        """Check if Ollama server is reachable.

        Args:
            base_url: Ollama API base URL

        Returns:
            True if server is reachable, False otherwise
        """
        try:
            url = f'{base_url.rstrip("/")}/api/tags'
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False
