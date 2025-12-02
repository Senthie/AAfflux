"""File storage data models."""

from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID, uuid4


class FileReference(SQLModel, table=True):
    """File reference model for PostgreSQL file metadata."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    file_id: UUID = Field(unique=True, index=True)  # 关联到 MongoDB 中的文件
    workspace_id: UUID = Field(foreign_key="workspace.id", index=True)  # 租户隔离
    filename: str
    content_type: str
    size_bytes: int
    storage_type: str  # MONGODB, GRIDFS
    uploaded_by: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
