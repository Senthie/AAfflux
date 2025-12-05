"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-05 16:08:34
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-05 16:10:25
FilePath: : AAfflux: api: app: schemas: file.py
Description: 定义文件上传、下载、列表等操作的数据传输对象。
"""

"""文件相关的 Pydantic Schemas

定义文件上传、下载、列表等操作的数据传输对象。
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """文件上传响应"""

    file_id: UUID = Field(..., description='文件唯一标识符')
    filename: str = Field(..., description='文件名')
    content_type: str = Field(..., description='文件 MIME 类型')
    size_bytes: int = Field(..., description='文件大小（字节）')
    storage_type: str = Field(..., description='存储类型（MONGODB/GRIDFS）')
    workspace_id: UUID = Field(..., description='所属工作空间 ID')
    uploaded_by: UUID = Field(..., description='上传者用户 ID')
    created_at: datetime = Field(..., description='上传时间')

    class Config:
        json_schema_extra = {
            'example': {
                'file_id': '550e8400-e29b-41d4-a716-446655440000',
                'filename': 'document.pdf',
                'content_type': 'application/pdf',
                'size_bytes': 1024000,
                'storage_type': 'MONGODB',
                'workspace_id': '660e8400-e29b-41d4-a716-446655440000',
                'uploaded_by': '770e8400-e29b-41d4-a716-446655440000',
                'created_at': '2025-12-05T10:30:00Z',
            }
        }


class FileMetadataResponse(BaseModel):
    """文件元数据响应"""

    file_id: UUID = Field(..., description='文件唯一标识符')
    filename: str = Field(..., description='文件名')
    content_type: str = Field(..., description='文件 MIME 类型')
    size_bytes: int = Field(..., description='文件大小（字节）')
    storage_type: str = Field(..., description='存储类型')
    workspace_id: UUID = Field(..., description='所属工作空间 ID')
    uploaded_by: UUID = Field(..., description='上传者用户 ID')
    created_at: datetime = Field(..., description='上传时间')
    updated_at: datetime = Field(..., description='更新时间')

    class Config:
        from_attributes = True
        json_schema_extra = {
            'example': {
                'file_id': '550e8400-e29b-41d4-a716-446655440000',
                'filename': 'report.xlsx',
                'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'size_bytes': 2048000,
                'storage_type': 'GRIDFS',
                'workspace_id': '660e8400-e29b-41d4-a716-446655440000',
                'uploaded_by': '770e8400-e29b-41d4-a716-446655440000',
                'created_at': '2025-12-05T10:30:00Z',
                'updated_at': '2025-12-05T10:30:00Z',
            }
        }


class FileListItem(BaseModel):
    """文件列表项"""

    file_id: UUID = Field(..., description='文件唯一标识符')
    filename: str = Field(..., description='文件名')
    content_type: str = Field(..., description='文件 MIME 类型')
    size_bytes: int = Field(..., description='文件大小（字节）')
    created_at: datetime = Field(..., description='上传时间')

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """文件列表响应"""

    total: int = Field(..., description='总文件数')
    items: list[FileListItem] = Field(..., description='文件列表')
    limit: int = Field(..., description='每页数量')
    offset: int = Field(..., description='偏移量')

    class Config:
        json_schema_extra = {
            'example': {
                'total': 42,
                'items': [
                    {
                        'file_id': '550e8400-e29b-41d4-a716-446655440000',
                        'filename': 'image.png',
                        'content_type': 'image/png',
                        'size_bytes': 512000,
                        'created_at': '2025-12-05T10:30:00Z',
                    }
                ],
                'limit': 100,
                'offset': 0,
            }
        }


class FileDeleteResponse(BaseModel):
    """文件删除响应"""

    success: bool = Field(..., description='删除是否成功')
    message: str = Field(..., description='响应消息')
    file_id: UUID = Field(..., description='被删除的文件 ID')

    class Config:
        json_schema_extra = {
            'example': {
                'success': True,
                'message': 'File deleted successfully',
                'file_id': '550e8400-e29b-41d4-a716-446655440000',
            }
        }
