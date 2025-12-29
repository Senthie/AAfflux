"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-26 16:15:42
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-29 09:53:25
FilePath: /api/app/utils/json_path.py
Description: 与 json path 相关的工具

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

import re
from typing import List

from pydantic import BaseModel


class Expr(BaseModel):
    index: int
    org_name: str
    expr: str


class JsonPathUtil:
    @staticmethod
    def get_exprs(content: str) -> List[Expr]:
        """
        description: 提取文本中的表达式
        param {str} content: 文本内容
        return {*} Dict<`Expr`>
        """
        pattern = re.compile(r'\{\{(.*?)\}\}', re.DOTALL)
        if not isinstance(content, str):
            raise ValueError('输入必须是字符串')

        result = []

        for match in pattern.finditer(content):
            full_match = match.group(0)  # 完整的匹配字符串

            # 获取表达式内容
            expr_content = match.group(1)

            expr_content = expr_content.strip()

            # 构建结果项
            result.append({'index': match.start(), 'org_name': full_match, 'expr': expr_content})

        return result
