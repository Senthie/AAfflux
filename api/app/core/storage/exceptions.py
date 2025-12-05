"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-05 15:48:48
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-05 15:48:51
FilePath: : AAfflux: api: app: core: storage: exceptions.py
Description:存储系统自定义的异常
"""

"""存储系统自定义异常"""

from typing import Optional


class StorageError(Exception):
    """存储系统基础异常"""

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class FileNotFoundError(StorageError):
    """文件不存在异常"""

    def __init__(self, file_id: str):
        super().__init__(message=f'File not found: {file_id}', details={'file_id': file_id})


class FileUploadError(StorageError):
    """文件上传失败异常"""

    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f'Failed to upload file: {filename}',
            details={'filename': filename, 'reason': reason},
        )


class FileDownloadError(StorageError):
    """文件下载失败异常"""

    def __init__(self, file_id: str, reason: str):
        super().__init__(
            message=f'Failed to download file: {file_id}',
            details={'file_id': file_id, 'reason': reason},
        )


class FileDeletionError(StorageError):
    """文件删除失败异常"""

    def __init__(self, file_id: str, reason: str):
        super().__init__(
            message=f'Failed to delete file: {file_id}',
            details={'file_id': file_id, 'reason': reason},
        )


class StorageConnectionError(StorageError):
    """存储系统连接失败异常"""

    def __init__(self, backend: str, reason: str):
        super().__init__(
            message=f'Failed to connect to storage backend: {backend}',
            details={'backend': backend, 'reason': reason},
        )
