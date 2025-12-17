"""
OpenAI客户端实现

本模块实现了OpenAI API的客户端，支持GPT系列模型的调用。
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


class OpenAIClient(LLMClient):
    """OpenAI API客户端"""

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """初始化OpenAI客户端

        Args:
            api_key: OpenAI API密钥
            config: 客户端配置
        """
        super().__init__(api_key, config)

        # 合并默认配置
        default_config = self.get_default_config()
        self.config = {**default_config, **(config or {})}

        # 设置API基础URL
        self.base_url = self.config.get('base_url', 'https://api.openai.com/v1')

        # 创建HTTP客户端
        self.http_client = httpx.AsyncClient(
            timeout=self.config.get('timeout', 30),
            headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
        )

        # 设置重试配置
        retry_config = RetryConfig(
            max_retries=self.config.get('max_retries', 3),
            base_delay=self.config.get('retry_delay', 1.0),
        )
        self._call_with_retry = retry_on_error(retry_config)(self._call_api)

    def get_default_config(self) -> Dict[str, Any]:
        """获取OpenAI客户端的默认配置"""
        base_config = super().get_default_config()
        return {
            **base_config,
            'base_url': 'https://api.openai.com/v1',
            'default_model': 'gpt-3.5-turbo',
            'supported_models': [
                'gpt-4',
                'gpt-4-turbo',
                'gpt-4-turbo-preview',
                'gpt-3.5-turbo',
                'gpt-3.5-turbo-16k',
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
        """调用OpenAI API生成响应

        Args:
            model: 模型名称
            prompt: 输入提示词
            temperature: 温度参数
            max_tokens: 最大令牌数
            **kwargs: 其他OpenAI特定参数

        Returns:
            LLMResponse: 生成的响应
        """
        # 构建请求数据
        request_data = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': temperature,
        }

        if max_tokens is not None:
            request_data['max_tokens'] = max_tokens

        # 添加其他参数
        for key, value in kwargs.items():
            if key not in ['model', 'messages', 'temperature', 'max_tokens']:
                request_data[key] = value

        # 调用API
        response_data = await self._call_with_retry('/chat/completions', request_data)

        # 解析响应
        choice = response_data['choices'][0]
        content = choice['message']['content']

        return LLMResponse(
            content=content,
            model=response_data['model'],
            usage=response_data.get('usage', {}),
            finish_reason=choice.get('finish_reason'),
            response_id=response_data.get('id'),
            created=response_data.get('created'),
        )

    async def list_models(self) -> List[str]:
        """获取OpenAI支持的模型列表"""
        try:
            response_data = await self._call_with_retry('/models', method='GET')
            models = [model['id'] for model in response_data.get('data', [])]

            # 过滤出聊天模型
            chat_models = [
                model
                for model in models
                if any(prefix in model for prefix in ['gpt-', 'text-davinci'])
            ]

            return sorted(chat_models)
        except Exception as e:
            logger.warning(f'Failed to fetch models from OpenAI API: {e}')
            # 返回默认支持的模型列表
            return self.config['supported_models']

    async def validate_api_key(self) -> bool:
        """验证OpenAI API密钥是否有效"""
        try:
            await self._call_api('/models', method='GET')
            return True
        except LLMAuthenticationError:
            return False
        except Exception as e:
            logger.warning(f'Error validating OpenAI API key: {e}')
            return False

    async def _call_api(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, method: str = 'POST'
    ) -> Dict[str, Any]:
        """调用OpenAI API的内部方法

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
                raise LLMAuthenticationError('Invalid OpenAI API key')
            elif response.status_code == 429:
                error_data = response.json() if response.content else {}
                raise LLMRateLimitError(
                    'OpenAI API rate limit exceeded', error_code='rate_limit_exceeded', **error_data
                )
            elif response.status_code == 400:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('error', {}).get('message', 'Invalid request')
                raise LLMInvalidRequestError(
                    f'OpenAI API request error: {error_message}',
                    error_code='invalid_request',
                    **error_data,
                )
            else:
                error_data = response.json() if response.content else {}
                raise LLMError(
                    f'OpenAI API error: HTTP {response.status_code}',
                    error_code=f'http_{response.status_code}',
                    **error_data,
                )

        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f'OpenAI API timeout: {e}')
        except httpx.RequestError as e:
            raise LLMError(f'OpenAI API request error: {e}')
        except json.JSONDecodeError as e:
            raise LLMError(f'Failed to parse OpenAI API response: {e}')

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.http_client.aclose()
