"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-30 15:53:04
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-30 16:48:33
FilePath: /api/app/engine/nodes/http/entities.py
Description: http node 的数据对象

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Dict

from pydantic import Field, field_validator
from pydantic_core import PydanticCustomError

from app.engine.nodes.base import BaseNodeData


class HttpNodeData(BaseNodeData):
    # 代理策略相关字段
    method: str = Field(frozen=True)
    url: str = Field(frozen=True)
    headers: Dict
    params: Dict
    body: Dict | None = None
    timeout: int
    follow_redirects: bool

    @field_validator('method', mode='before')
    @classmethod
    def validate_x(cls, method: str) -> str:
        SUPPORTED_METHODS = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}
        if method not in SUPPORTED_METHODS:
            raise PydanticCustomError(
                'method_error',
                'method must be one of {supported_methods}',
                {'supported_methods': SUPPORTED_METHODS},
            )
        return method

    @field_validator('url', mode='before')
    @classmethod
    def validate_url(cls, url: str) -> str:
        if not url.startswith(('http://', 'https://')):
            raise PydanticCustomError(
                'url_error',
                'url must start with http:// or https://',
            )
        return url

    @field_validator('headers', mode='before')
    @classmethod
    def validate_headers(cls, headers: Dict) -> Dict:
        if not isinstance(headers, dict):
            raise PydanticCustomError(
                'headers_error',
                'headers must be a dict',
            )
        return headers

    @field_validator('params', mode='before')
    @classmethod
    def validate_params(cls, params: Dict) -> Dict:
        if not isinstance(params, dict):
            raise PydanticCustomError(
                'params_error',
                'params must be a dict',
            )
        return params

    @field_validator('timeout', mode='before')
    @classmethod
    def validate_timeout(cls, timeout: int) -> int:
        if not isinstance(timeout, int):
            raise PydanticCustomError(
                'timeout_error',
                'timeout must be an int',
            )
        return timeout
