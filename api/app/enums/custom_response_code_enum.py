"""
Author: Senthie seemoon2077@gmail.com
Date: 2026-01-05 11:21:54
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-05 15:24:07
FilePath: /api/app/enums/custom_response_code_enum.py
Description: 自定义响应代码和信息

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from enum import Enum


class CustomCodeBase(Enum):
    """自定义状态码基类"""

    @property
    def code(self) -> int:
        """获取状态码"""
        return self.value[0]

    @property
    def msg(self) -> str:
        """获取状态码信息"""
        message = self.value[1]
        return message


class CustomResponseCodeEnum(CustomCodeBase):
    # 通用状态码
    SUCCESS = (200, '请求成功')
    BAD_REQUEST = (400, '请求参数错误')
    UNAUTHORIZED = (401, '身份验证未通过')
    FORBIDDEN = (403, '客户端没有访问内容的权限')
    NOT_FOUND = (404, '请求的资源不存在')
    INTERNAL_SERVER_ERROR = (500, '服务器内部错误')

    # Auth
    EMAIL_ALREADY_EXISTS = (1001, '邮箱已存在')
    PASSWORD_TOO_SHORT = (1002, '密码长度至少8位')
    PASSWORD_MISSING_UPPERCASE = (1003, '密码必须包含至少一个大写字母')
    PASSWORD_MISSING_LOWERCASE = (1004, '密码必须包含至少一个小写字母')
    PASSWORD_MISSING_DIGIT = (1005, '密码必须包含至少一个数字')
