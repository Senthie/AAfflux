"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-12 16:06:37
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-12 16:09:42
FilePath: /api/examples/type_demo.py
Description: executor_class: Type[BaseNodeExecutor] 是 Python 类型注解，
它表示 executor_class 参数应该是一个 类（类型），而不是一个实例。让我详细解释：

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Type


class BaseNodeExecutor:
    pass


class MyExecutor(BaseNodeExecutor):
    pass


# 正确用法
my_clss = MyExecutor  # 类调用
my_instance = MyExecutor()  # 类示例


# 函数定义
def register_executor(cls: Type[BaseNodeExecutor]):
    print(f'注册类：{cls}')


# 调用示例
register_executor(MyExecutor)  # 正确：传递的是类本身
register_executor(MyExecutor())  # 错误：传递的是示例
register_executor(BaseNodeExecutor)  # 正确：基类
