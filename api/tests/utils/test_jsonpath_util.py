"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-26 16:24:26
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-29 10:41:15
FilePath: /api/tests/utils/test_jsonpath_util.py
Description:用于测试 jsonpath util 是否如期运行

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from random import randint

import pytest

from app.utils.json_path import JsonPathUtil


@pytest.fixture
def text1() -> str:
    """
    创建一个简单的文本数据
    """
    text = """标题 ：{{ $json['标题'] }} 内容：{{ $json['内容'] }} \n日期：{{ $json['日期'] }} 链接：{{ $json['链接'] }} 媒体：{{ $json['媒体'] }}"""
    return text


class TestJsonpathUtil:
    def test_jsonpath_util(self, text1):
        """
        测试 jsonpath_util 是否能正确解析文本中的 jsonpath
        """

        exprs = JsonPathUtil.get_exprs(text1)
        assert exprs != [], '解析不到数据'
        assert "$json['标题']" == exprs[0]['expr'], "$json['标题'] not exist"
        assert "$json['内容2']" not in exprs, "$json['内容2'] in list"
        assert len(exprs) == 5, '解析数量不正确'

    def test_jsonpath_replace(self, text1):
        """
        测试 jsonpath_util 是否能正确解析文本中的 jsonpath
        """

        exprs = JsonPathUtil.get_exprs(text1)
        assert len(exprs) == 5, '解析数量不正确'
        for expr in exprs:
            value = randint(0, 100)
            text1 = text1.replace(expr.get('org_name'), str(value), 1)
