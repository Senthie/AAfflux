"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:56:33
FilePath: /api/app/utils/llm/retry.py
Description: Retry工具
LLM调用重试机制
本模块实现了LLM调用的重试逻辑，支持指数退避和不同类型错误的重试策略。

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

import asyncio
from functools import wraps
import logging
from typing import Callable, List, Optional, Type

from .base_client import LLMRateLimitError, LLMTimeoutError

logger = logging.getLogger(__name__)


class RetryConfig:
    """重试配置类"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_errors: Optional[List[Type[Exception]]] = None,
    ):
        """初始化重试配置

        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            exponential_base: 指数退避的底数
            jitter: 是否添加随机抖动
            retryable_errors: 可重试的异常类型列表
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_errors = retryable_errors or [
            LLMRateLimitError,
            LLMTimeoutError,
            ConnectionError,
            TimeoutError,
        ]


def calculate_delay(
    attempt: int, base_delay: float, max_delay: float, exponential_base: float, jitter: bool = True
) -> float:
    """计算重试延迟时间

    Args:
        attempt: 当前重试次数（从1开始）
        base_delay: 基础延迟时间
        max_delay: 最大延迟时间
        exponential_base: 指数退避的底数
        jitter: 是否添加随机抖动

    Returns:
        float: 延迟时间（秒）
    """
    import random

    # 计算指数退避延迟
    delay = base_delay * (exponential_base ** (attempt - 1))

    # 限制最大延迟
    delay = min(delay, max_delay)

    # 添加随机抖动以避免雷群效应
    if jitter:
        delay = delay * (0.5 + random.random() * 0.5)

    return delay


def retry_on_error(config: Optional[RetryConfig] = None):
    """LLM调用重试装饰器

    Args:
        config: 重试配置，如果为None则使用默认配置

    Returns:
        装饰器函数
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # 检查是否为可重试的错误
                    if not any(isinstance(e, error_type) for error_type in config.retryable_errors):
                        logger.warning(f'Non-retryable error in {func.__name__}: {e}')
                        raise e

                    # 如果已达到最大重试次数，抛出异常
                    if attempt >= config.max_retries:
                        logger.error(
                            f'Max retries ({config.max_retries}) exceeded for {func.__name__}: {e}'
                        )
                        raise e

                    # 计算延迟时间并等待
                    delay = calculate_delay(
                        attempt + 1,
                        config.base_delay,
                        config.max_delay,
                        config.exponential_base,
                        config.jitter,
                    )

                    logger.info(
                        f'Retrying {func.__name__} (attempt {attempt + 1}/{config.max_retries}) '
                        f'after {delay:.2f}s due to: {e}'
                    )

                    await asyncio.sleep(delay)

            # 这里不应该到达，但为了类型安全
            if last_exception:
                raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time

            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # 检查是否为可重试的错误
                    if not any(isinstance(e, error_type) for error_type in config.retryable_errors):
                        logger.warning(f'Non-retryable error in {func.__name__}: {e}')
                        raise e

                    # 如果已达到最大重试次数，抛出异常
                    if attempt >= config.max_retries:
                        logger.error(
                            f'Max retries ({config.max_retries}) exceeded for {func.__name__}: {e}'
                        )
                        raise e

                    # 计算延迟时间并等待
                    delay = calculate_delay(
                        attempt + 1,
                        config.base_delay,
                        config.max_delay,
                        config.exponential_base,
                        config.jitter,
                    )

                    logger.info(
                        f'Retrying {func.__name__} (attempt {attempt + 1}/{config.max_retries}) '
                        f'after {delay:.2f}s due to: {e}'
                    )

                    time.sleep(delay)

            # 这里不应该到达，但为了类型安全
            if last_exception:
                raise last_exception

        # 根据函数是否为协程选择合适的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class RetryableClient:
    """带重试功能的客户端基类"""

    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """初始化可重试客户端

        Args:
            retry_config: 重试配置
        """
        self.retry_config = retry_config or RetryConfig()

    def with_retry(self, func: Callable) -> Callable:
        """为函数添加重试功能

        Args:
            func: 要添加重试功能的函数

        Returns:
            带重试功能的函数
        """
        return retry_on_error(self.retry_config)(func)
