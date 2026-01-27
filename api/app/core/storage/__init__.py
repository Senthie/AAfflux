"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/core/storage/__init__.py
Description: 模块初始化

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""
"""存储模块

提供统一的文件存储接口，支持多种存储后端。
"""

from app.core.storage.base import StorageBackend
from app.core.storage.gridfs import GridFSBackend
from app.core.storage.exceptions import (
    StorageError,
    FileNotFoundError,
    FileUploadError,
    FileDownloadError,
    FileDeletionError,
    StorageConnectionError,
)

__all__ = [
    'StorageBackend',
    'GridFSBackend',
    'StorageError',
    'FileNotFoundError',
    'FileUploadError',
    'FileDownloadError',
    'FileDeletionError',
    'StorageConnectionError',
]
