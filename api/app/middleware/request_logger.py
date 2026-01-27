"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/middleware/request_logger.py
Description: Request Logger中间件

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    def __init__(self, app, log_body: bool = False, max_body_size: int = 1024):
        super().__init__(app)
        self.log_body = log_body
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """记录请求和响应信息"""
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录请求开始时间
        start_time = time.time()

        # 获取客户端信息
        client_ip = request.client.host if request.client else 'unknown'
        user_agent = request.headers.get('user-agent', 'unknown')

        # 记录请求信息
        request_info = {
            'request_id': request_id,
            'method': request.method,
            'url': str(request.url),
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'client_ip': client_ip,
            'user_agent': user_agent,
            'headers': dict(request.headers),
        }

        # 记录请求体（如果启用）
        if self.log_body and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if len(body) <= self.max_body_size:
                    request_info['body'] = body.decode('utf-8', errors='ignore')
                else:
                    request_info['body'] = f'[Body too large: {len(body)} bytes]'
            except Exception as e:
                request_info['body'] = f'[Error reading body: {str(e)}]'

        logger.info('Request started', **request_info)

        try:
            # 执行请求
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录响应信息
            response_info = {
                'request_id': request_id,
                'status_code': response.status_code,
                'process_time_ms': round(process_time * 1000, 2),
                'response_headers': dict(response.headers),
            }

            # 根据状态码选择日志级别
            if response.status_code >= 500:
                logger.error('Request completed with server error', **response_info)
            elif response.status_code >= 400:
                logger.warning('Request completed with client error', **response_info)
            else:
                logger.info('Request completed successfully', **response_info)

            # 添加请求ID到响应头
            response.headers['X-Request-ID'] = request_id

            return response

        except Exception as exc:
            # 记录异常
            process_time = time.time() - start_time
            logger.error(
                'Request failed with exception',
                request_id=request_id,
                error=str(exc),
                error_type=type(exc).__name__,
                process_time_ms=round(process_time * 1000, 2),
            )
            raise


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """性能日志中间件"""

    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """记录性能信息"""
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time

        # 记录慢请求
        if process_time > self.slow_request_threshold:
            logger.warning(
                'Slow request detected',
                method=request.method,
                url=str(request.url),
                process_time_ms=round(process_time * 1000, 2),
                threshold_ms=round(self.slow_request_threshold * 1000, 2),
            )

        # 添加性能头
        response.headers['X-Process-Time'] = f'{process_time:.3f}'

        return response


class APIUsageLoggingMiddleware(BaseHTTPMiddleware):
    """API使用统计中间件"""

    def __init__(self, app):
        super().__init__(app)
        self.usage_stats = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """记录API使用统计"""
        endpoint = f'{request.method} {request.url.path}'

        response = await call_next(request)

        # 更新统计信息
        if endpoint not in self.usage_stats:
            self.usage_stats[endpoint] = {'count': 0, 'status_codes': {}, 'total_time': 0.0}

        self.usage_stats[endpoint]['count'] += 1

        status_code = response.status_code
        if status_code not in self.usage_stats[endpoint]['status_codes']:
            self.usage_stats[endpoint]['status_codes'][status_code] = 0
        self.usage_stats[endpoint]['status_codes'][status_code] += 1

        # 每100次请求记录一次统计信息
        if self.usage_stats[endpoint]['count'] % 100 == 0:
            logger.info('API usage statistics', endpoint=endpoint, stats=self.usage_stats[endpoint])

        return response
