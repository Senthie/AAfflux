"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-23 16:04:09
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-24 17:03:39
FilePath: /api/app/engine/nodes/base/exc.py
Description: 基本的节点Node错误提示

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Any, Dict, Optional


class NodeExecutionError(Exception):
    """Exception raised when node execution fails."""

    def __init__(self, message: str, node_id: str, error_details: Optional[Dict[str, Any]] = None):
        """Initialize node execution error.

        Args:
            message: Error message
            node_id: ID of the node that failed (string)
            error_details: Additional error details
        """
        super().__init__(message)
        self.node_id = node_id
        self.error_details = error_details or {}


class BaseNodeError(ValueError):
    """Base class for node errors."""

    pass


class DefaultValueTypeError(BaseNodeError):
    """Raised when the default value type is invalid."""

    pass


class NodeRegistrationError(Exception):
    """节点注册相关异常"""

    pass
