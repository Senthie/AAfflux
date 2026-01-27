"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/middleware/error_handler.py
Description: Error Handler中间件

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

import time
import traceback
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger
from app.schemas.response import error_response

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """统一错误处理中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并捕获异常"""
        start_time = time.time()

        try:
            # 执行请求
            response = await call_next(request)

            # 记录请求信息
            process_time = time.time() - start_time
            logger.info(
                'Request completed',
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=f'{process_time:.3f}s',
            )

            return response

        except Exception as exc:
            # 记录异常信息
            process_time = time.time() - start_time
            logger.error(
                'Unhandled exception in middleware',
                method=request.method,
                url=str(request.url),
                error=str(exc),
                error_type=type(exc).__name__,
                process_time=f'{process_time:.3f}s',
                traceback=traceback.format_exc(),
            )

            # 返回统一的错误响应
            return JSONResponse(
                status_code=500,
                content=error_response(
                    message='服务器内部错误',
                    error_code='INTERNAL_SERVER_ERROR',
                    path=str(request.url),
                ),
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """添加安全头"""
        response = await call_next(request)

        # 添加安全头
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的速率限制中间件"""

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """检查速率限制"""
        client_ip = request.client.host if request.client else 'unknown'
        current_time = time.time()

        # 清理过期的记录
        self.clients = {
            ip: timestamps
            for ip, timestamps in self.clients.items()
            if any(t > current_time - self.period for t in timestamps)
        }

        # 检查当前客户端的请求次数
        if client_ip in self.clients:
            # 过滤出时间窗口内的请求
            recent_calls = [t for t in self.clients[client_ip] if t > current_time - self.period]

            if len(recent_calls) >= self.calls:
                logger.warning(
                    'Rate limit exceeded',
                    client_ip=client_ip,
                    calls=len(recent_calls),
                    limit=self.calls,
                )

                return JSONResponse(
                    status_code=429,
                    content=error_response(
                        message='请求过于频繁，请稍后再试',
                        error_code='RATE_LIMIT_EXCEEDED',
                        path=str(request.url),
                    ),
                )

            self.clients[client_ip] = recent_calls + [current_time]
        else:
            self.clients[client_ip] = [current_time]

        return await call_next(request)


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """请求大小限制中间件"""

    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """检查请求大小"""
        content_length = request.headers.get('content-length')

        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    logger.warning(
                        'Request size too large',
                        size=size,
                        max_size=self.max_size,
                        url=str(request.url),
                    )

                    return JSONResponse(
                        status_code=413,
                        content=error_response(
                            message='请求体过大',
                            error_code='REQUEST_TOO_LARGE',
                            path=str(request.url),
                        ),
                    )
            except ValueError:
                pass

        return await call_next(request)
