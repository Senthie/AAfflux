"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-05 16:08:55
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-05 16:11:28
FilePath: : AAfflux: api: app: api: v1: file.py
Description: 提供文件上传、下载、删除、列表等功能。
"""

"""文件管理 API 端点

提供文件上传、下载、删除、列表等功能。
"""

from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.services.file_server import FileService
from app.schemas.file import (
    FileUploadResponse,
    FileMetadataResponse,
    FileListResponse,
    FileListItem,
    FileDeleteResponse,
)
from app.core.storage.exceptions import FileNotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# 依赖注入：获取文件服务
async def get_file_service(session: Annotated[AsyncSession, Depends(get_session)]) -> FileService:
    """获取文件服务实例"""
    return FileService(session)


@router.post(
    '/upload',
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary='上传文件',
    description='上传文件到系统，自动选择存储方式（小文件用 MongoDB，大文件用 GridFS）',
)
async def upload_file(
    file: Annotated[UploadFile, File(description='要上传的文件')],
    workspace_id: Annotated[UUID, Query(description='工作空间 ID')],
    uploaded_by: Annotated[UUID, Query(description='上传者用户 ID')],
    file_service: Annotated[FileService, Depends(get_file_service)],
) -> FileUploadResponse:
    """上传文件

    Args:
        file: 上传的文件对象
        workspace_id: 工作空间 ID（租户隔离）
        uploaded_by: 上传者用户 ID
        file_service: 文件服务实例

    Returns:
        FileUploadResponse: 文件上传响应

    Raises:
        HTTPException: 上传失败时抛出 500 错误
    """
    try:
        file_reference = await file_service.upload_file(
            file=file, workspace_id=workspace_id, uploaded_by=uploaded_by
        )

        return FileUploadResponse(
            file_id=file_reference.file_id,
            filename=file_reference.filename,
            content_type=file_reference.content_type,
            size_bytes=file_reference.size_bytes,
            storage_type=file_reference.storage_type,
            workspace_id=file_reference.workspace_id,
            uploaded_by=file_reference.uploaded_by,
            created_at=file_reference.created_at,
        )

    except Exception as e:
        logger.error('File upload failed', error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to upload file: {str(e)}',
        ) from e


@router.get(
    '/{file_id}/download',
    response_class=StreamingResponse,
    summary='下载文件',
    description='下载指定文件，支持流式传输',
)
async def download_file(
    file_id: Annotated[UUID, Query(description='文件 ID')],
    file_service: Annotated[FileService, Depends(get_file_service)],
) -> StreamingResponse:
    """下载文件

    Args:
        file_id: 文件 ID
        file_service: 文件服务实例

    Returns:
        StreamingResponse: 文件流响应

    Raises:
        HTTPException: 文件不存在时抛出 404 错误
    """
    try:
        file_reference, file_stream = await file_service.download_file(file_id)

        return StreamingResponse(
            content=file_stream,
            media_type=file_reference.content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{file_reference.filename}"',
                'Content-Length': str(file_reference.size_bytes),
            },
        )

    except FileNotFoundError as e:
        logger.warning('File not found for download', file_id=str(file_id))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'File not found: {file_id}',
        ) from e
    except Exception as e:
        logger.error('File download failed', file_id=str(file_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to download file: {str(e)}',
        ) from e


@router.delete(
    '/{file_id}',
    response_model=FileDeleteResponse,
    summary='删除文件',
    description='删除指定文件（同时删除元数据和文件内容）',
)
async def delete_file(
    file_id: Annotated[UUID, Query(description='文件 ID')],
    file_service: Annotated[FileService, Depends(get_file_service)],
) -> FileDeleteResponse:
    """删除文件

    Args:
        file_id: 文件 ID
        file_service: 文件服务实例

    Returns:
        FileDeleteResponse: 删除响应

    Raises:
        HTTPException: 文件不存在时抛出 404 错误
    """
    try:
        success = await file_service.delete_file(file_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'File not found: {file_id}',
            )

        return FileDeleteResponse(
            success=True, message='File deleted successfully', file_id=file_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error('File deletion failed', file_id=str(file_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to delete file: {str(e)}',
        ) from e


@router.get(
    '/{file_id}/metadata',
    response_model=FileMetadataResponse,
    summary='获取文件元数据',
    description='获取指定文件的元数据信息',
)
async def get_file_metadata(
    file_id: Annotated[UUID, Query(description='文件 ID')],
    file_service: Annotated[FileService, Depends(get_file_service)],
) -> FileMetadataResponse:
    """获取文件元数据

    Args:
        file_id: 文件 ID
        file_service: 文件服务实例

    Returns:
        FileMetadataResponse: 文件元数据

    Raises:
        HTTPException: 文件不存在时抛出 404 错误
    """
    file_reference = await file_service.get_file_metadata(file_id)

    if not file_reference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'File not found: {file_id}',
        )

    return FileMetadataResponse.model_validate(file_reference)


@router.get(
    '',
    response_model=FileListResponse,
    summary='列出文件',
    description='列出指定工作空间的文件列表',
)
async def list_files(
    workspace_id: Annotated[UUID, Query(description='工作空间 ID')],
    file_service: Annotated[FileService, Depends(get_file_service)],
    limit: Annotated[int, Query(ge=1, le=1000, description='每页数量')] = 100,
    offset: Annotated[int, Query(ge=0, description='偏移量')] = 0,
) -> FileListResponse:
    """列出文件

    Args:
        workspace_id: 工作空间 ID
        limit: 每页数量（1-1000）
        offset: 偏移量
        file_service: 文件服务实例

    Returns:
        FileListResponse: 文件列表响应
    """
    files = await file_service.list_files(workspace_id=workspace_id, limit=limit, offset=offset)

    items = [FileListItem.model_validate(f) for f in files]

    return FileListResponse(total=len(items), items=items, limit=limit, offset=offset)
