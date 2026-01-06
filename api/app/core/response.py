"""
Author: Senthie seemoon2077@gmail.com
Date: 2026-01-05 11:12:55
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-05 17:53:40
FilePath: /api/app/core/response.py
Description: 返回的数据的 schema的通用型统一格式

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Any, Generic, TypeVar, overload

from pydantic import BaseModel, Field

from app.enums.custom_response_code_enum import CustomResponseCodeEnum
from app.utils.timezone_help import tz_helper

T = TypeVar('T')


class ResponseModel(BaseModel):
    """
    不包含返回数据 schema 的通用型统一返回模型

    示例::

        @router.get('/test', response_model=ResponseModel)
        def test():
            return ResponseModel(data={'test': 'test'})


        @router.get('/test')
        def test() -> ResponseModel:
            return ResponseModel(data={'test': 'test'})


        @router.get('/test')
        def test() -> ResponseModel:
            res = CustomResponseCode.HTTP_200
            return ResponseModel(code=res.code, msg=res.msg, data={'test': 'test'})
    """

    code: int = Field(CustomResponseCodeEnum.SUCCESS.code, description='返回状态码')
    msg: str = Field(CustomResponseCodeEnum.SUCCESS.msg, description='返回信息')
    data: Any | None = Field(None, description='返回数据')
    timestamp: str = Field(..., description='返回时间戳')

    def to_dict(self):
        return {
            'code': self.code,
            'msg': self.msg,
            'data': self.data,
            'timestamp': self.timestamp,
        }


class ResponseSchemaModel(ResponseModel, Generic[T]):
    """
    包含返回数据 schema 的通用型统一返回模型

    示例::

        @router.get('/test', response_model=ResponseSchemaModel[GetApiDetail])
        def test():
            return ResponseSchemaModel[GetApiDetail](data=GetApiDetail(...))


        @router.get('/test')
        def test() -> ResponseSchemaModel[GetApiDetail]:
            return ResponseSchemaModel[GetApiDetail](data=GetApiDetail(...))


        @router.get('/test')
        def test() -> ResponseSchemaModel[GetApiDetail]:
            res = CustomResponseCode.HTTP_200
            return ResponseSchemaModel[GetApiDetail](code=res.code, msg=res.msg, data=GetApiDetail(...))
    """

    data: T


class ResponseBase:
    """统一返回方法"""

    @staticmethod
    def __response(
        *,
        res: CustomResponseCodeEnum,
        data: Any | None,
    ) -> ResponseModel:
        """
        请求返回通用方法

        :param res: 返回信息
        :param data: 返回数据
        :return:
        """
        current_time = tz_helper.get_current_time()
        timestamp_str = tz_helper.format_time(current_time)
        return ResponseModel(code=res.code, msg=res.msg, data=data, timestamp=timestamp_str)

    @overload
    def success(
        self,
        *,
        res: CustomResponseCodeEnum = CustomResponseCodeEnum.SUCCESS,
        data: Any = None,
    ) -> ResponseModel: ...

    @overload
    def success(
        self,
        *,
        res: CustomResponseCodeEnum = CustomResponseCodeEnum.SUCCESS,
        data: T,
    ) -> ResponseSchemaModel[T]: ...

    def success(
        self,
        *,
        res: CustomResponseCodeEnum = CustomResponseCodeEnum.SUCCESS,
        data: Any | T = None,
    ) -> ResponseModel | ResponseSchemaModel[T]:
        """
        成功响应

        :param res: 返回信息
        :param data: 返回数据
        :return:
        """

        # if data is None:
        #     return ResponseModel(code=res.code, msg=res.msg, data=data)
        # return ResponseSchemaModel[Any](code=res.code, msg=res.msg, data=data)
        return self.__response(res=res, data=data)

    @overload
    def fail(
        self,
        *,
        res: CustomResponseCodeEnum = CustomResponseCodeEnum.NOT_FOUND,
        data: None = None,
    ) -> ResponseModel: ...

    @overload
    def fail(
        self,
        *,
        res: CustomResponseCodeEnum = CustomResponseCodeEnum.NOT_FOUND,
        data: T,
    ) -> ResponseSchemaModel[T]: ...

    def fail(
        self,
        *,
        res: CustomResponseCodeEnum = CustomResponseCodeEnum.NOT_FOUND,
        data: Any = None,
    ) -> ResponseModel:
        """
        失败响应

        :param res: 返回信息
        :param data: 返回数据
        :return:
        """
        return self.__response(res=res, data=data)


response_base: ResponseBase = ResponseBase()
