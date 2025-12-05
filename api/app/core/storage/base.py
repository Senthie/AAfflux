"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-05 15:23:17
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-05 15:45:21
FilePath: : AAfflux: api: app: core: storage: base.py
Description: 抽象接口实现
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Optional
from fastapi import UploadFile


class StorageBackend(ABC):
    """存储后端抽象基类

    定义文件存储的标准接口，支持多种存储后端实现。
    """

    @abstractmethod
    async def upload(self, file: UploadFile, metadata: Optional[dict[str, Any]] = None) -> str:
        """上传文件到存储系统

        Args:
            file: FastAPI 上传文件对象
            metadata: 可选的元数据（如 workspace_id, user_id 等）

        Returns:
            str: 存储系统返回的文件 ID（MongoDB ObjectId 或 GridFS file_id）

        Raises:
            StorageError: 上传失败时抛出
        """
        pass

    @abstractmethod
    async def download(self, file_id: str) -> AsyncGenerator[bytes, None]:
        """从存储系统下载文件

        Args:
            file_id: 存储系统的文件 ID

        Yields:
            bytes: 文件内容的二进制流（分块传输）
        Raises:
            FileNotFoundError: 文件不存在
            StorageError: 下载失败
        """
        pass

    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """从存储系统删除文件

        Args:
            file_id: 存储系统的文件 ID

        Returns:
            bool: 删除成功返回 True，文件不存在返回 False

        Raises:
            StorageError: 删除失败时抛出
        """
        pass

    @abstractmethod
    async def exists(self, file_id: str) -> bool:
        """检查文件是否存在

        Args:
            file_id: 存储系统的文件 ID

        Returns:
            bool: 文件存在返回 True，否则返回 False
        """
        pass
