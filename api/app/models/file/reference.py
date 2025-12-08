"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-02 11:12:23
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-08 14:32:21
FilePath: : AAfflux: api: app: models: file: reference.py
Description:实现了softdelete软删除的基础类继承
"""

"""文件引用模型 - 1张表。

本模块定义了文件引用的数据模型。
在PostgreSQL中存储文件元数据，实际文件存储在MongoDB中。
"""

from uuid import UUID, uuid4
from sqlmodel import Field
from app.models.base import BaseModel, TimestampMixin, WorkspaceMixin, SoftDeleteMixin


class FileReference(BaseModel, WorkspaceMixin, TimestampMixin, SoftDeleteMixin, table=True):
    """文件引用表 - PostgreSQL中的文件引用。

    在PostgreSQL中存储文件的元数据和引用信息。
    实际文件内容存储在MongoDB中（使用GridFS处理大文件）。

    Attributes:
    已经继承
        id: 文件引用记录唯一标识符（UUID）
        workspace_id: 所属工作空间ID（逻辑外键，租户隔离）
        created_at: 创建时间
        deleted_at: Optional[datetime] = Field(default=None)
        is_deleted: bool = Field(default=False)

        file_id: 文件业务ID（UUID，关联到MongoDB）
        filename: 文件名
        content_type: 文件MIME类型
        size_bytes: 文件大小（字节）
        storage_type: 存储类型（MONGODB-小文件/GRIDFS-大文件）
        mongo_id: MongoDB文档ID或GridFS文件ID
        uploaded_by: 上传者用户ID（逻辑外键）

    业务规则：
        - 小文件（< 16MB）直接存储在MongoDB文档中
        - 大文件（>= 16MB）使用GridFS分块存储
        - 文件删除时同时清理PostgreSQL引用和MongoDB数据
        - 支持按工作空间隔离文件访问
    """

    __tablename__ = 'file_references'
    d: UUID = Field(default_factory=uuid4, primary_key=True)
    file_id: UUID = Field(unique=True, index=True)  # 关联到MongoDB

    filename: str = Field(max_length=255)
    content_type: str = Field(max_length=100)
    size_bytes: int
    storage_type: str = Field(max_length=20, index=True)  # MONGODB, GRIDFS
    mongo_id: str = Field(max_length=100)  # MongoDB _id 或 GridFS file_id
    uploaded_by: UUID = Field(index=True)  # Logical FK to users
