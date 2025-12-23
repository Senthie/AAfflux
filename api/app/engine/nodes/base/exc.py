"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-23 16:04:09
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-23 16:04:13
FilePath: /api/app/engine/nodes/base/exc.py
Description: 基本的节点Node错误提示

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""


class BaseNodeError(ValueError):
    """Base class for node errors."""

    pass


class DefaultValueTypeError(BaseNodeError):
    """Raised when the default value type is invalid."""

    pass
