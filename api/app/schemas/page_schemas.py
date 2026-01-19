"""
Author: Senthie seemoon2077@gmail.com
Date: 2026-01-12 14:56:18
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-19 11:02:37
FilePath: /api/app/schemas/page_schemas.py
Description:

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar('T')


class PageRequest(BaseModel):
    """
    Request list by page create a page list schema
    """

    total: int = Field(default=0, description='查询列表总记录数')
    size: int = Field(default=10, description='每页显示条数，默认 10')
    current: int = Field(default=1, description='当前页')
    orders: Optional[List[str]] = Field(default=[], description='排序字段信息')
    maxLimit: Optional[int] = Field(default=None, description='限制每页最大条数，默认无限制')


class PageResponse(BaseModel, Generic[T]):
    """
    response page list
    """

    records: List[T] = Field(default=[], description='记录列表')
    total: int = Field(default=0, description='查询列表总记录数')
    size: int = Field(default=10, description='每页显示条数，默认 10')
    current: int = Field(default=1, description='当前页')
    orders: Optional[List[str]] = Field(default=[], description='排序字段信息')
    maxLimit: Optional[int] = Field(default=None, description='限制每页最大条数，默认无限制')
