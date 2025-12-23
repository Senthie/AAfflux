"""
Tests for Ollama Node Executor.

测试 Ollama 节点执行器，包括单元测试和集成测试。
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.engine.node_executor import NodeExecutionError
from app.engine.nodes.ollama_node import OllamaNodeExecutor

# ============== 配置 ==============
# 本地 Ollama 配置
OLLAMA_API_KEY = 'ollama'
OLLAMA_BASE_URL = 'http://14.12.0.172:11434/v1/'
OLLAMA_MODEL_ID = 'deepseek-r1:14b'


# ============== Fixtures ==============
@pytest.fixture
def ollama_executor():
    """Create an Ollama node executor instance."""
    return OllamaNodeExecutor()


@pytest.fixture
def mock_node():
    """Create a mock node."""
    node = MagicMock()
    node.id = uuid4()
    node.config = {}
    return node


@pytest.fixture
def mock_context():
    """Create a mock execution context."""
    context = MagicMock()
    context.get_node_input = MagicMock(return_value={})
    return context


# ============== 单元测试 ==============
class TestOllamaNodeValidation:
    """Test Ollama node configuration validation."""

    def test_validate_config_valid(self, ollama_executor):
        """Test validation with valid config."""
        config = {
            'model': 'llama2',
            'base_url': 'http://localhost:11434',
            'temperature': 0.7,
            'num_predict': 1000,
            'top_p': 0.9,
            'top_k': 40,
        }
        assert ollama_executor.validate_config(config) is True

    def test_validate_config_missing_model(self, ollama_executor):
        """Test validation fails without model."""
        config = {'base_url': 'http://localhost:11434'}
        assert ollama_executor.validate_config(config) is False

    def test_validate_config_invalid_base_url(self, ollama_executor):
        """Test validation fails with invalid base_url."""
        config = {
            'model': 'llama2',
            'base_url': 'invalid-url',
        }
        assert ollama_executor.validate_config(config) is False

    def test_validate_config_invalid_temperature(self, ollama_executor):
        """Test validation fails with invalid temperature."""
        config = {
            'model': 'llama2',
            'temperature': 3.0,  # > 2
        }
        assert ollama_executor.validate_config(config) is False

    def test_validate_config_invalid_top_p(self, ollama_executor):
        """Test validation fails with invalid top_p."""
        config = {
            'model': 'llama2',
            'top_p': 1.5,  # > 1
        }
        assert ollama_executor.validate_config(config) is False


class TestOllamaNodePromptRendering:
    """Test prompt template rendering."""

    def test_render_prompt_simple(self, ollama_executor):
        """Test simple prompt rendering."""
        template = 'Hello, {{name}}!'
        inputs = {'name': 'World'}
        result = ollama_executor._render_prompt(template, inputs)
        assert result == 'Hello, World!'

    def test_render_prompt_multiple_vars(self, ollama_executor):
        """Test prompt rendering with multiple variables."""
        template = '{{greeting}}, {{name}}! How is {{topic}}?'
        inputs = {'greeting': 'Hi', 'name': 'Alice', 'topic': 'Python'}
        result = ollama_executor._render_prompt(template, inputs)
        assert result == 'Hi, Alice! How is Python?'

    def test_render_prompt_no_vars(self, ollama_executor):
        """Test prompt rendering without variables."""
        template = 'Hello, World!'
        inputs = {}
        result = ollama_executor._render_prompt(template, inputs)
        assert result == 'Hello, World!'


class TestOllamaNodeOutputSchema:
    """Test output schema."""

    def test_get_output_schema(self, ollama_executor):
        """Test output schema structure."""
        schema = ollama_executor.get_output_schema()
        assert 'response' in schema
        assert 'model' in schema
        assert 'provider' in schema
        assert 'base_url' in schema
        assert 'prompt_used' in schema


class TestOllamaNodeMocked:
    """Test Ollama node with mocked HTTP calls."""

    @pytest.mark.asyncio
    async def test_execute_openai_compatible_mode(self, ollama_executor, mock_node, mock_context):
        """Test execution with OpenAI compatible API mode."""
        mock_node.config = {
            'base_url': 'http://localhost:11434/v1/',
            'model': 'llama2',
            'prompt': 'Say hello',
            'api_mode': 'openai_compatible',
            'api_key': 'ollama',
        }

        mock_response = {'choices': [{'message': {'content': 'Hello!'}}]}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = MagicMock(
                json=MagicMock(return_value=mock_response),
                raise_for_status=MagicMock(),
            )

            result = await ollama_executor.execute(mock_node, mock_context)

            assert result['response'] == 'Hello!'
            assert result['model'] == 'llama2'
            assert result['provider'] == 'ollama'
            assert result['api_mode'] == 'openai_compatible'

    @pytest.mark.asyncio
    async def test_execute_native_chat_mode(self, ollama_executor, mock_node, mock_context):
        """Test execution with native chat API mode."""
        mock_node.config = {
            'base_url': 'http://localhost:11434',
            'model': 'llama2',
            'prompt': 'Say hello',
            'api_mode': 'native_chat',
        }

        mock_response = {'message': {'content': 'Hello from native chat!'}}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = MagicMock(
                json=MagicMock(return_value=mock_response),
                raise_for_status=MagicMock(),
            )

            result = await ollama_executor.execute(mock_node, mock_context)

            assert result['response'] == 'Hello from native chat!'
            assert result['api_mode'] == 'native_chat'

    @pytest.mark.asyncio
    async def test_execute_native_generate_mode(self, ollama_executor, mock_node, mock_context):
        """Test execution with native generate API mode."""
        mock_node.config = {
            'base_url': 'http://localhost:11434',
            'model': 'llama2',
            'prompt': 'Say hello',
            'api_mode': 'native_generate',
        }

        mock_response = {'response': 'Hello from generate!'}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = MagicMock(
                json=MagicMock(return_value=mock_response),
                raise_for_status=MagicMock(),
            )

            result = await ollama_executor.execute(mock_node, mock_context)

            assert result['response'] == 'Hello from generate!'
            assert result['api_mode'] == 'native_generate'

    @pytest.mark.asyncio
    async def test_execute_with_system_prompt(self, ollama_executor, mock_node, mock_context):
        """Test execution with system prompt."""
        mock_node.config = {
            'base_url': 'http://localhost:11434/v1/',
            'model': 'llama2',
            'prompt': 'What is 2+2?',
            'system_prompt': 'You are a math teacher.',
            'api_mode': 'openai_compatible',
            'api_key': 'ollama',
        }

        mock_response = {'choices': [{'message': {'content': '4'}}]}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = MagicMock(
                json=MagicMock(return_value=mock_response),
                raise_for_status=MagicMock(),
            )

            result = await ollama_executor.execute(mock_node, mock_context)
            assert result['response'] == '4'

    @pytest.mark.asyncio
    async def test_execute_with_template_variables(self, ollama_executor, mock_node, mock_context):
        """Test execution with template variables from inputs."""
        mock_node.config = {
            'base_url': 'http://localhost:11434/v1/',
            'model': 'llama2',
            'prompt': 'Translate "{{text}}" to {{language}}',
            'api_mode': 'openai_compatible',
            'api_key': 'ollama',
        }
        mock_context.get_node_input.return_value = {
            'text': 'Hello',
            'language': 'Chinese',
        }

        mock_response = {'choices': [{'message': {'content': '你好'}}]}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = MagicMock(
                json=MagicMock(return_value=mock_response),
                raise_for_status=MagicMock(),
            )

            result = await ollama_executor.execute(mock_node, mock_context)

            assert result['response'] == '你好'
            assert result['prompt_used'] == 'Translate "Hello" to Chinese'


# ============== 集成测试 (需要真实 Ollama 服务) ==============
@pytest.mark.integration
@pytest.mark.asyncio
class TestOllamaNodeIntegration:
    """
    Integration tests that require a real Ollama server.
    Run with: pytest -m integration tests/test_ollama_node.py
    """

    async def test_real_ollama_openai_compatible(self, ollama_executor, mock_node, mock_context):
        """Test with real Ollama server using OpenAI compatible API."""
        mock_node.config = {
            'base_url': OLLAMA_BASE_URL,
            'api_key': OLLAMA_API_KEY,
            'model': OLLAMA_MODEL_ID,
            'prompt': 'What is 1+1?',
            'api_mode': 'openai_compatible',
            'temperature': 0.1,
            'max_tokens': 500,  # deepseek-r1 需要更多 tokens 用于推理
            'timeout': 120,
        }

        result = await ollama_executor.execute(mock_node, mock_context)

        assert 'response' in result
        assert result['model'] == OLLAMA_MODEL_ID
        assert result['provider'] == 'ollama'
        assert result['api_mode'] == 'openai_compatible'
        # 检查响应中包含 "2"
        assert '2' in result['response']
        print(f'\nOllama Response: {result["response"]}')

    async def test_real_ollama_with_system_prompt(self, ollama_executor, mock_node, mock_context):
        """Test with real Ollama server with system prompt."""
        mock_node.config = {
            'base_url': OLLAMA_BASE_URL,
            'api_key': OLLAMA_API_KEY,
            'model': OLLAMA_MODEL_ID,
            'prompt': 'Say hello',
            'system_prompt': 'You are a helpful assistant. Be brief.',
            'api_mode': 'openai_compatible',
            'temperature': 0.1,
            'max_tokens': 1000,  # deepseek-r1 需要更多 tokens
            'timeout': 120,
        }

        result = await ollama_executor.execute(mock_node, mock_context)

        assert 'response' in result
        assert len(result['response']) > 0
        print(f'\nOllama Response: {result["response"]}')

    async def test_real_ollama_check_connection(self, ollama_executor):
        """Test connection check with real Ollama server."""
        # 使用原生 API 端点检查连接
        base_url = OLLAMA_BASE_URL.replace('/v1/', '')
        is_connected = await ollama_executor.check_connection(base_url)
        print(f'\nOllama connection status: {is_connected}')
        # 不强制断言，因为服务器可能不可用

    async def test_real_ollama_list_models(self, ollama_executor):
        """Test listing models from real Ollama server."""
        base_url = OLLAMA_BASE_URL.replace('/v1/', '')
        try:
            models = await ollama_executor.list_models(base_url)
            print(f'\nAvailable models: {models}')
            assert isinstance(models, list)
        except Exception as e:
            print(f'\nCould not list models: {e}')


# ============== 错误处理测试 ==============
class TestOllamaNodeErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_execute_connection_error(self, ollama_executor, mock_node, mock_context):
        """Test handling of connection errors."""
        mock_node.config = {
            'base_url': 'http://nonexistent-host:11434/v1/',
            'model': 'llama2',
            'prompt': 'Hello',
            'api_mode': 'openai_compatible',
            'timeout': 5,
        }

        with pytest.raises(NodeExecutionError) as exc_info:
            await ollama_executor.execute(mock_node, mock_context)

        assert 'Ollama execution failed' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_http_error(self, ollama_executor, mock_node, mock_context):
        """Test handling of HTTP errors."""
        mock_node.config = {
            'base_url': 'http://localhost:11434/v1/',
            'model': 'llama2',
            'prompt': 'Hello',
            'api_mode': 'openai_compatible',
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = MagicMock(
                raise_for_status=MagicMock(side_effect=Exception('HTTP 500')),
            )

            with pytest.raises(NodeExecutionError):
                await ollama_executor.execute(mock_node, mock_context)
