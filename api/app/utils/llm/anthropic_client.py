"""
Anthropic客户端实现

本模块实现了Anthropic Claude API的客户端，支持Claude系列模型的调用。
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from .base_client import (
    LLMAuthenticationError,
    LLMClient,
    LLMError,
    LLMInvalidRequestError,
    LLMRateLimitError,
    LLMResponse,
    LLMTimeoutError,
)
from .retry import RetryConfig, retry_on_error

logger = logging.getLogger(__name__)


class AnthropicClient(LLMClient):
    """Anthropic Claude API客户端"""

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """初始化Anthropic客户端

        Args:
            api_key: Anthropic API密钥
            config: 客户端配置
        """
        super().__init__(api_key, config)

        # 合并默认配置
        default_config = self.get_default_config()
        self.config = {**default_config, **(config or {})}

        # 设置API基础URL
        self.base_url = self.config.get('base_url', 'https://api.anthropic.com')

        # 创建HTTP客户端
        self.http_client = httpx.AsyncClient(
            timeout=self.config.get('timeout', 30),
            headers={
                'x-api-key': self.api_key,
                'Content-Type': 'application/json',
                'anthropic-version': self.config.get('api_version', '2023-06-01'),
            },
        )

        # 设置重试配置
        retry_config = RetryConfig(
            max_retries=self.config.get('max_retries', 3),
            base_delay=self.config.get('retry_delay', 1.0),
        )
        self._call_with_retry = retry_on_error(retry_config)(self._call_api)

    def get_default_config(self) -> Dict[str, Any]:
        """获取Anthropic客户端的默认配置"""
        base_config = super().get_default_config()
        return {
            **base_config,
            'base_url': 'https://api.anthropic.com',
            'api_version': '2023-06-01',
            'default_model': 'claude-3-sonnet-20240229',
            'supported_models': [
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307',
                'claude-2.1',
                'claude-2.0',
                'claude-instant-1.2',
            ],
        }

    async def call(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """调用Anthropic API生成响应

        Args:
            model: 模型名称
            prompt: 输入提示词
            temperature: 温度参数
            max_tokens: 最大令牌数
            **kwargs: 其他Anthropic特定参数

        Returns:
            LLMResponse: 生成的响应
        """
        # 构建请求数据
        request_data = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': temperature,
            'max_tokens': max_tokens or 1024,  # Anthropic要求必须指定max_tokens
        }

        # 添加其他参数
        for key, value in kwargs.items():
            if key not in ['model', 'messages', 'temperature', 'max_tokens']:
                request_data[key] = value

        # 调用API
        response_data = await self._call_with_retry('/v1/messages', request_data)

        # 解析响应
        content_blocks = response_data.get('content', [])
        content = ''
        if content_blocks:
            # 提取文本内容
            for block in content_blocks:
                if block.get('type') == 'text':
                    content += block.get('text', '')

        return LLMResponse(
            content=content,
            model=response_data.get('model', model),
            usage=response_data.get('usage', {}),
            finish_reason=response_data.get('stop_reason'),
            response_id=response_data.get('id'),
            role=response_data.get('role'),
        )

    async def list_models(self) -> List[str]:
        """获取Anthropic支持的模型列表

        注意：Anthropic API目前不提供模型列表端点，返回预定义的模型列表
        """
        return self.config['supported_models']

    async def validate_api_key(self) -> bool:
        """验证Anthropic API密钥是否有效"""
        try:
            # 发送一个简单的测试请求
            test_data = {
                'model': self.config['default_model'],
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'max_tokens': 10,
            }
            await self._call_api('/v1/messages', test_data)
            return True
        except LLMAuthenticationError:
            return False
        except Exception as e:
            logger.warning(f'Error validating Anthropic API key: {e}')
            return False

    async def _call_api(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, method: str = 'POST'
    ) -> Dict[str, Any]:
        """调用Anthropic API的内部方法

        Args:
            endpoint: API端点
            data: 请求数据
            method: HTTP方法

        Returns:
            Dict[str, Any]: API响应数据

        Raises:
            LLMError: API调用失败时抛出相应的错误
        """
        url = f'{self.base_url}{endpoint}'

        try:
            if method.upper() == 'GET':
                response = await self.http_client.get(url)
            else:
                response = await self.http_client.post(url, json=data)

            # 检查HTTP状态码
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise LLMAuthenticationError('Invalid Anthropic API key')
            elif response.status_code == 429:
                error_data = response.json() if response.content else {}
                raise LLMRateLimitError(
                    'Anthropic API rate limit exceeded',
                    error_code='rate_limit_exceeded',
                    **error_data,
                )
            elif response.status_code == 400:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('error', {}).get('message', 'Invalid request')
                raise LLMInvalidRequestError(
                    f'Anthropic API request error: {error_message}',
                    error_code='invalid_request',
                    **error_data,
                )
            else:
                error_data = response.json() if response.content else {}
                raise LLMError(
                    f'Anthropic API error: HTTP {response.status_code}',
                    error_code=f'http_{response.status_code}',
                    **error_data,
                )

        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f'Anthropic API timeout: {e}') from e
        except httpx.RequestError as e:
            raise LLMError(f'Anthropic API request error: {e}') from e
        except json.JSONDecodeError as e:
            raise LLMError(f'Failed to parse Anthropic API response: {e}') from e

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.http_client.aclose()
