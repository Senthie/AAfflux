"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-05 15:23:34
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-05 15:59:48
FilePath: : AAfflux: api: app: core: storage: gridfs.py
Description: gridfs 实现
"""

"""MongoDB GridFS 存储后端实现

使用 MongoDB GridFS 存储大文件（>= 16MB）和小文件（< 16MB）。
GridFS 自动将大文件分块存储，支持流式读写。
"""

from typing import AsyncGenerator, Any, Optional
from datetime import datetime
from bson import ObjectId
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from app.core.mongodb import mongodb_client
from app.core.storage.base import StorageBackend
from app.core.storage.exceptions import (
    FileNotFoundError,
    FileUploadError,
    FileDownloadError,
    FileDeletionError,
    StorageConnectionError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class GridFSBackend(StorageBackend):
    """MongoDB GridFS 存储后端
    特点：
    - 自动分块存储（默认 255KB/块）
    - 支持大文件（无大小限制）
    - 支持流式上传/下载
    - 自动处理文件元数据
    """

    def __init__(self, bucket_name: str = 'fs'):
        """初始化 GridFS 存储后端

        Args:
            bucket_name: GridFS bucket 名称（默认 "fs"）
        """
        self.bucket_name = bucket_name
        self._bucket: Optional[AsyncIOMotorGridFSBucket] = None

    @property
    def bucket(self) -> AsyncIOMotorGridFSBucket:
        """获取 GridFS bucket 实例

        Returns:
            AsyncIOMotorGridFSBucket: GridFS bucket

        Raises:
            StorageConnectionError: MongoDB 未连接
        """
        if self._bucket is None:
            if mongodb_client.client is None:
                raise StorageConnectionError(
                    backend='GridFS', reason='MongoDB client is not connected'
                )

            db = mongodb_client.client[mongodb_client.db_name]
            self._bucket = AsyncIOMotorGridFSBucket(db, bucket_name=self.bucket_name)

        return self._bucket

    async def upload(self, file: UploadFile, metadata: Optional[dict[str, Any]] = None) -> str:
        """上传文件到 GridFS

        Args:
            file: FastAPI 上传文件对象
            metadata: 可选的元数据

        Returns:
            str: GridFS file_id（ObjectId 字符串）
        """
        try:
            # 准备元数据
            file_metadata = {
                'filename': file.filename,
                'content_type': file.content_type,
                'upload_date': datetime.utcnow(),
                **(metadata or {}),
            }

            # 流式上传到 GridFS
            file_id = await self.bucket.upload_from_stream(
                filename=file.filename or 'unknown', source=file.file, metadata=file_metadata
            )

            logger.info(
                'File uploaded to GridFS',
                file_id=str(file_id),
                filename=file.filename,
                size=file.size,
            )

            return str(file_id)

        except Exception as e:
            logger.error('Failed to upload file to GridFS', filename=file.filename, error=str(e))
            raise FileUploadError(filename=file.filename or 'unknown', reason=str(e)) from e

    async def download(self, file_id: str) -> AsyncGenerator[bytes, None]:
        """从 GridFS 下载文件（流式）

        Args:
            file_id: GridFS file_id

        Yields:
            bytes: 文件内容分块
        """
        try:
            # 验证 ObjectId 格式
            if not ObjectId.is_valid(file_id):
                raise FileNotFoundError(file_id)

            # 打开 GridFS 文件流
            grid_out = await self.bucket.open_download_stream(ObjectId(file_id))

            # 分块读取（每次 1MB）
            chunk_size = 1024 * 1024
            while True:
                chunk: bytes = await grid_out.read(chunk_size)
                if not chunk:
                    break
                yield chunk

            logger.info('File downloaded from GridFS', file_id=file_id)

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error('Failed to download file from GridFS', file_id=file_id, error=str(e))
            raise FileDownloadError(file_id=file_id, reason=str(e)) from e

    async def delete(self, file_id: str) -> bool:
        """从 GridFS 删除文件

        Args:
            file_id: GridFS file_id

        Returns:
            bool: 删除成功返回 True
        """
        try:
            # 验证 ObjectId 格式
            if not ObjectId.is_valid(file_id):
                return False

            # 检查文件是否存在
            if not await self.exists(file_id):
                return False

            # 删除文件
            await self.bucket.delete(ObjectId(file_id))

            logger.info('File deleted from GridFS', file_id=file_id)
            return True

        except Exception as e:
            logger.error('Failed to delete file from GridFS', file_id=file_id, error=str(e))
            raise FileDeletionError(file_id=file_id, reason=str(e)) from e

    async def exists(self, file_id: str) -> bool:
        """检查文件是否存在于 GridFS

        Args:
            file_id: GridFS file_id

        Returns:
            bool: 文件存在返回 True
        """
        try:
            if not ObjectId.is_valid(file_id):
                return False

            # 尝试查找文件
            file_doc = await self.bucket.find({'_id': ObjectId(file_id)}).to_list(length=1)
            return len(file_doc) > 0

        except Exception as e:
            logger.error('Failed to check file existence in GridFS', file_id=file_id, error=str(e))
            return False

    async def get_metadata(self, file_id: str) -> dict[str, Any]:
        """获取文件元数据

        Args:
            file_id: GridFS file_id

        Returns:
            dict: 文件元数据
        """
        try:
            if not ObjectId.is_valid(file_id):
                raise FileNotFoundError(file_id)

            # 查找文件
            files = await self.bucket.find({'_id': ObjectId(file_id)}).to_list(length=1)

            if not files:
                raise FileNotFoundError(file_id)

            file_doc = files[0]

            return {
                'file_id': str(file_doc['_id']),
                'filename': file_doc.get('filename'),
                'length': file_doc.get('length'),
                'chunk_size': file_doc.get('chunkSize'),
                'upload_date': file_doc.get('uploadDate'),
                'metadata': file_doc.get('metadata', {}),
            }

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error('Failed to get file metadata from GridFS', file_id=file_id, error=str(e))
            raise StorageConnectionError(backend='GridFS', reason=str(e)) from e
