"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-05 14:59:04
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-05 16:06:07
FilePath: : AAfflux: api: app: services: file_server.py
Description: "文件服务 - 协调 PostgreSQL 元数据和 MongoDB 文件存储
"""

"""文件服务 - 协调 PostgreSQL 元数据和 MongoDB 文件存储

职责：
1. 管理 PostgreSQL 中的文件元数据（FileReference）
2. 协调 MongoDB GridFS 的文件存储
3. 提供统一的文件上传、下载、删除接口
4. 处理事务一致性（元数据和文件内容同步）
"""

from typing import Optional, AsyncGenerator
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.file.reference import FileReference
from app.core.storage import GridFSBackend, FileNotFoundError as StorageFileNotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


class FileService:
    """文件服务

    协调 PostgreSQL 元数据和 MongoDB GridFS 存储。
    """

    def __init__(self, session: AsyncSession):
        """初始化文件服务

        Args:
            session: 数据库会话
        """
        self.session = session
        self.storage = GridFSBackend()

    async def upload_file(
        self,
        file: UploadFile,
        workspace_id: UUID,
        uploaded_by: UUID,
    ) -> FileReference:
        """上传文件

        流程：
        1. 上传文件到 GridFS
        2. 在 PostgreSQL 创建元数据记录
        3. 如果失败，回滚 GridFS 文件

        Args:
            file: 上传的文件对象
            workspace_id: 工作空间 ID
            uploaded_by: 上传者用户 ID

        Returns:
            FileReference: 文件引用记录

        Raises:
            FileUploadError: 上传失败
        """
        mongo_id = None

        try:
            # 1. 上传到 GridFS
            metadata = {
                'workspace_id': str(workspace_id),
                'uploaded_by': str(uploaded_by),
            }

            mongo_id = await self.storage.upload(file, metadata=metadata)

            # 2. 确定存储类型（根据文件大小）
            file_size = file.size or 0
            storage_type = 'GRIDFS' if file_size >= 16 * 1024 * 1024 else 'MONGODB'

            # 3. 创建 PostgreSQL 元数据记录
            file_reference = FileReference(
                file_id=uuid4(),
                workspace_id=workspace_id,
                filename=file.filename or 'unknown',
                content_type=file.content_type or 'application/octet-stream',
                size_bytes=file_size,
                storage_type=storage_type,
                mongo_id=mongo_id,
                uploaded_by=uploaded_by,
            )

            self.session.add(file_reference)
            await self.session.commit()
            await self.session.refresh(file_reference)

            logger.info(
                'File uploaded successfully',
                file_id=str(file_reference.file_id),
                filename=file.filename,
                size=file_size,
                storage_type=storage_type,
            )

            return file_reference

        except Exception as e:
            # 回滚：删除已上传的 GridFS 文件
            if mongo_id:
                try:
                    await self.storage.delete(mongo_id)
                    logger.info('Rolled back GridFS file', mongo_id=mongo_id)
                except Exception as rollback_error:
                    logger.error(
                        'Failed to rollback GridFS file',
                        mongo_id=mongo_id,
                        error=str(rollback_error),
                    )

            await self.session.rollback()

            logger.error(
                'Failed to upload file',
                filename=file.filename,
                error=str(e),
            )
            raise

    async def download_file(
        self, file_id: UUID
    ) -> tuple[FileReference, AsyncGenerator[bytes, None]]:
        """下载文件

        Args:
            file_id: 文件 ID

        Returns:
            tuple: (文件元数据, 文件内容流)

        Raises:
            FileNotFoundError: 文件不存在
        """
        # 1. 查询 PostgreSQL 元数据
        statement = select(FileReference).where(FileReference.file_id == file_id)
        result = await self.session.execute(statement)
        file_reference = result.scalar_one_or_none()

        if not file_reference:
            logger.warning('File not found in database', file_id=str(file_id))
            raise StorageFileNotFoundError(str(file_id))

        # 2. 从 GridFS 下载文件流
        file_stream = self.storage.download(file_reference.mongo_id)

        logger.info(
            'File download started',
            file_id=str(file_id),
            filename=file_reference.filename,
        )

        return file_reference, file_stream

    async def delete_file(self, file_id: UUID) -> bool:
        """删除文件

        流程：
        1. 删除 PostgreSQL 元数据
        2. 删除 GridFS 文件
        3. 如果 GridFS 删除失败，记录日志但不回滚

        Args:
            file_id: 文件 ID

        Returns:
            bool: 删除成功返回 True
        """
        # 1. 查询文件元数据
        statement = select(FileReference).where(FileReference.file_id == file_id)
        result = await self.session.execute(statement)
        file_reference = result.scalar_one_or_none()

        if not file_reference:
            logger.warning('File not found for deletion', file_id=str(file_id))
            return False

        mongo_id = file_reference.mongo_id

        try:
            # 2. 删除 PostgreSQL 记录
            await self.session.delete(file_reference)
            await self.session.commit()

            # 3. 删除 GridFS 文件（最佳努力，失败不回滚）
            try:
                await self.storage.delete(mongo_id)
                logger.info(
                    'File deleted successfully',
                    file_id=str(file_id),
                    mongo_id=mongo_id,
                )
            except Exception as storage_error:
                logger.error(
                    'Failed to delete GridFS file (metadata already deleted)',
                    file_id=str(file_id),
                    mongo_id=mongo_id,
                    error=str(storage_error),
                )

            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(
                'Failed to delete file',
                file_id=str(file_id),
                error=str(e),
            )
            raise

    async def get_file_metadata(self, file_id: UUID) -> Optional[FileReference]:
        """获取文件元数据

        Args:
            file_id: 文件 ID

        Returns:
            FileReference: 文件引用记录，不存在返回 None
        """
        statement = select(FileReference).where(FileReference.file_id == file_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_files(
        self,
        workspace_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FileReference]:
        """列出工作空间的文件

        Args:
            workspace_id: 工作空间 ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            list[FileReference]: 文件列表
        """
        statement = (
            select(FileReference)
            .where(FileReference.workspace_id == workspace_id)
            .order_by(FileReference.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def check_file_exists(self, file_id: UUID) -> bool:
        """检查文件是否存在

        Args:
            file_id: 文件 ID

        Returns:
            bool: 存在返回 True
        """
        statement = select(FileReference.file_id).where(FileReference.file_id == file_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None
