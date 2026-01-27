"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/api/errors.py
Description: 错误处理

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AuthException
from app.core.logging import get_logger
from app.core.response import response_base
from app.schemas.response import error_response, validation_error_response

logger = get_logger(__name__)


class BusinessException(Exception):
    """业务异常"""

    def __init__(self, message: str, error_code: str = 'BUSINESS_ERROR', details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(message)


class AuthenticationException(Exception):
    """认证异常"""

    def __init__(self, message: str = '认证失败'):
        self.message = message
        super().__init__(message)


class AuthorizationException(Exception):
    """授权异常"""

    def __init__(self, message: str = '权限不足'):
        self.message = message
        super().__init__(message)


class ResourceNotFoundException(Exception):
    """资源不存在异常"""

    def __init__(self, message: str = '资源不存在'):
        self.message = message
        super().__init__(message)


async def auth_exception_handler(request: Request, exc: AuthException):
    """认证/授权异常处理器"""
    logger.warning(
        'Auth exception occurred',
        response_code=exc.response_code.code,
        message=exc.message,
        path=str(request.url),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_base.fail(
            res=exc.response_code, data={'path': str(request.url)}
        ).to_dict(),
    )


async def business_exception_handler(request: Request, exc: BusinessException):
    """业务异常处理器"""
    logger.warning(
        'Business exception occurred',
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        path=str(request.url),
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response(
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details,
            path=str(request.url),
        ),
    )


async def authentication_exception_handler(request: Request, exc: AuthenticationException):
    """认证异常处理器"""
    logger.warning('Authentication failed', message=exc.message, path=str(request.url))

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response(
            message=exc.message,
            error_code='AUTHENTICATION_ERROR',
            path=str(request.url),
        ),
    )


async def authorization_exception_handler(request: Request, exc: AuthorizationException):
    """授权异常处理器"""
    logger.warning('Authorization failed', message=exc.message, path=str(request.url))

    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=error_response(
            message=exc.message, error_code='AUTHORIZATION_ERROR', path=str(request.url)
        ),
    )


async def resource_not_found_exception_handler(request: Request, exc: ResourceNotFoundException):
    """资源不存在异常处理器"""
    logger.info('Resource not found', message=exc.message, path=str(request.url))

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_response(
            message=exc.message, error_code='RESOURCE_NOT_FOUND', path=str(request.url)
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(
        'HTTP exception occurred',
        status_code=exc.status_code,
        detail=exc.detail,
        path=str(request.url),
    )

    # 根据状态码确定错误代码
    error_code_map = {
        400: 'BAD_REQUEST',
        401: 'UNAUTHORIZED',
        403: 'FORBIDDEN',
        404: 'NOT_FOUND',
        405: 'METHOD_NOT_ALLOWED',
        409: 'CONFLICT',
        422: 'UNPROCESSABLE_ENTITY',
        429: 'TOO_MANY_REQUESTS',
        500: 'INTERNAL_SERVER_ERROR',
        502: 'BAD_GATEWAY',
        503: 'SERVICE_UNAVAILABLE',
        504: 'GATEWAY_TIMEOUT',
    }

    error_code = error_code_map.get(exc.status_code, 'HTTP_ERROR')

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=str(exc.detail), error_code=error_code, path=str(request.url)
        ),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    logger.warning('Validation error occurred', errors=exc.errors(), path=str(request.url))

    # 格式化验证错误
    formatted_errors = []
    for error in exc.errors():
        formatted_errors.append(
            {
                'field': '.'.join(str(loc) for loc in error['loc']),
                'message': error['msg'],
                'type': error['type'],
                'input': error.get('input'),
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=validation_error_response(errors=formatted_errors, path=str(request.url)),
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """数据库完整性错误处理器"""
    logger.error('Database integrity error', error=str(exc), path=str(request.url))

    # 解析常见的完整性错误
    error_message = '数据操作失败'
    if 'UNIQUE constraint failed' in str(exc) or 'duplicate key' in str(exc):
        error_message = '数据已存在，请检查唯一性约束'
    elif 'FOREIGN KEY constraint failed' in str(exc):
        error_message = '关联数据不存在，请检查外键约束'
    elif 'NOT NULL constraint failed' in str(exc):
        error_message = '必填字段不能为空'

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=error_response(
            message=error_message,
            error_code='DATABASE_INTEGRITY_ERROR',
            details={'original_error': str(exc.orig) if hasattr(exc, 'orig') else str(exc)},
            path=str(request.url),
        ),
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """SQLAlchemy错误处理器"""
    logger.error('Database error occurred', error=str(exc), path=str(request.url))

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            message='数据库操作失败', error_code='DATABASE_ERROR', path=str(request.url)
        ),
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(
        'Unexpected error occurred',
        error=str(exc),
        error_type=type(exc).__name__,
        path=str(request.url),
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            message='服务器内部错误',
            error_code='INTERNAL_SERVER_ERROR',
            path=str(request.url),
        ),
    )


def register_exception_handlers(app: FastAPI):
    """注册异常处理器"""
    app.add_exception_handler(AuthException, auth_exception_handler)
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(AuthenticationException, authentication_exception_handler)
    app.add_exception_handler(AuthorizationException, authorization_exception_handler)
    app.add_exception_handler(ResourceNotFoundException, resource_not_found_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
