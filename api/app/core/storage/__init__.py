"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-05 15:20:01
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-05 15:47:56
FilePath: : AAfflux: api: app: core: storage: __init__.py
Description:统一的文件存储接口
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
