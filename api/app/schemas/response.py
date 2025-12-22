"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-22 10:33:24
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-22 10:33:27
FilePath: : AAfflux: api: app: schemas: response.py
Description:统一响应格式
"""

from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """基础响应格式"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    code: int = Field(..., description="业务状态码")


class SuccessResponse(BaseResponse[T]):
    """成功响应"""
    success: bool = Field(default=True, description="请求成功")
    message: str = Field(default="操作成功", description="成功消息")
    code: int = Field(default=200, description="成功状态码")


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = Field(default=False, description="请求失败")
    message: str = Field(..., description="错误消息")
    error_code: str = Field(..., description="错误代码")
    details: Optional[Any] = Field(None, description="错误详情")
    timestamp: str = Field(..., description="错误时间戳")
    path: str = Field(..., description="请求路径")


class ValidationErrorResponse(BaseModel):
    """验证错误响应"""
    success: bool = Field(default=False, description="请求失败")
    message: str = Field(default="请求参数验证失败", description="错误消息")
    error_code: str = Field(default="VALIDATION_ERROR", description="错误代码")
    errors: list = Field(..., description="验证错误详情")
    timestamp: str = Field(..., description="错误时间戳")
    path: str = Field(..., description="请求路径")


class PaginationMeta(BaseModel):
    """分页元数据"""
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total: int = Field(..., description="总记录数")
    total_pages: int = Field(..., description="总页数")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    success: bool = Field(default=True, description="请求成功")
    message: str = Field(default="查询成功", description="响应消息")
    data: list[T] = Field(..., description="数据列表")
    meta: PaginationMeta = Field(..., description="分页信息")
    code: int = Field(default=200, description="状态码")


# 常用响应工厂函数
def success_response(
    data: Any = None,
    message: str = "操作成功",
    code: int = 200
) -> dict:
    """创建成功响应"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "code": code
    }


def error_response(
    message: str,
    error_code: str = "INTERNAL_ERROR",
    details: Any = None,
    timestamp: str = None,
    path: str = ""
) -> dict:
    """创建错误响应"""
    from datetime import datetime

    return {
        "success": False,
        "message": message,
        "error_code": error_code,
        "details": details,
        "timestamp": timestamp or datetime.utcnow().isoformat(),
        "path": path
    }


def validation_error_response(
    errors: list,
    message: str = "请求参数验证失败",
    timestamp: str = None,
    path: str = ""
) -> dict:
    """创建验证错误响应"""
    from datetime import datetime

    return {
        "success": False,
        "message": message,
        "error_code": "VALIDATION_ERROR",
        "errors": errors,
        "timestamp": timestamp or datetime.utcnow().isoformat(),
        "path": path
    }


def paginated_response(
    data: list,
    page: int,
    page_size: int,
    total: int,
    message: str = "查询成功"
) -> dict:
    """创建分页响应"""
    from math import ceil

    return {
        "success": True,
        "message": message,
        "data": data,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": ceil(total / page_size) if page_size > 0 else 0
        },
        "code": 200
    }
