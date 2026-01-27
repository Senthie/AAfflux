"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:55:55
FilePath: /api/app/utils/llm/base_client.py
Description: Base Client工具
LLM客户端抽象基类
本模块定义了LLM客户端的抽象基类，为不同的LLM提供商提供统一的接口。

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMResponse:
    """LLM响应结果封装类"""

    def __init__(
        self,
        content: str,
        model: str,
        usage: Optional[Dict[str, Any]] = None,
        finish_reason: Optional[str] = None,
        **kwargs,
    ):
        self.content = content
        self.model = model
        self.usage = usage or {}
        self.finish_reason = finish_reason
        self.metadata = kwargs


class LLMClient(ABC):
    """LLM客户端抽象基类

    定义了所有LLM提供商客户端必须实现的接口方法。
    """

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """初始化LLM客户端

        Args:
            api_key: API密钥
            config: 提供商特定配置
        """
        self.api_key = api_key
        self.config = config or {}

    @abstractmethod
    async def call(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """调用LLM生成响应

        Args:
            model: 模型名称
            prompt: 输入提示词
            temperature: 温度参数，控制输出随机性
            max_tokens: 最大令牌数
            **kwargs: 其他提供商特定参数

        Returns:
            LLMResponse: 包含生成内容和元数据的响应对象

        Raises:
            LLMError: LLM调用失败时抛出
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """获取提供商支持的模型列表

        Returns:
            List[str]: 支持的模型名称列表

        Raises:
            LLMError: 获取模型列表失败时抛出
        """
        pass

    @abstractmethod
    async def validate_api_key(self) -> bool:
        """验证API密钥是否有效

        Returns:
            bool: API密钥是否有效
        """
        pass

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置

        Returns:
            Dict[str, Any]: 默认配置字典
        """
        return {'timeout': 30, 'max_retries': 3, 'retry_delay': 1.0}


class LLMError(Exception):
    """LLM相关错误的基类"""

    def __init__(self, message: str, error_code: Optional[str] = None, **kwargs):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.metadata = kwargs


class LLMAuthenticationError(LLMError):
    """LLM认证错误"""

    pass


class LLMRateLimitError(LLMError):
    """LLM速率限制错误"""

    pass


class LLMTimeoutError(LLMError):
    """LLM超时错误"""

    pass


class LLMInvalidRequestError(LLMError):
    """LLM无效请求错误"""

    pass
