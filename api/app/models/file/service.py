"""文件服务 - 使用 MongoDB GridFS 的统一文件管理接口。

本模块提供了完整的文件管理功能，包括：
- 文件上传到 GridFS
- 文件下载和检索
- 文件元数据管理
- 文件删除和清理
- 文件列表查询

所有文件内容存储在 MongoDB GridFS 中，元数据存储在 upload_files 集合中。
"""

from typing import Optional, BinaryIO
from uuid import UUID, uuid4
from datetime import datetime
import hashlib
from io import BytesIO

from app.core.mongodb import mongodb_client


class FileService:
    """
    Unified file service using MongoDB GridFS.
    
    Handles file upload, download, and metadata management.
    Files are stored in GridFS, metadata in upload_files collection.
    """
    
    def __init__(self):
        self.mongo = mongodb_client
    
    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        tenant_id: UUID,
        created_by: UUID,
        content_type: Optional[str] = None,
        extension: Optional[str] = None,
    ) -> dict:
        """
        Upload file to GridFS.
        
        Args:
            file_data: File binary data
            filename: Original filename
            tenant_id: Tenant ID
            created_by: User ID who uploaded the file
            content_type: MIME type
            extension: File extension
        
        Returns:
            dict: File metadata including file_id
        """
        # Calculate file hash
        file_hash = hashlib.sha256(file_data).hexdigest()
        file_size = len(file_data)
        file_id = str(uuid4())
        
        # Upload to GridFS
        gridfs_bucket = self.mongo.get_gridfs()
        gridfs_id = await gridfs_bucket.upload_from_stream(
            filename,
            BytesIO(file_data),
            metadata={
                "file_id": file_id,
                "tenant_id": str(tenant_id),
                "created_by": str(created_by),
                "content_type": content_type,
                "extension": extension,
                "hash": file_hash,
            }
        )
        
        # Store metadata in upload_files collection
        files_collection = self.mongo.get_collection("upload_files")
        file_doc = {
            "_id": file_id,
            "gridfs_id": str(gridfs_id),
            "tenant_id": str(tenant_id),
            "storage_type": "gridfs",
            "key": file_id,
            "name": filename,
            "size": file_size,
            "extension": extension or "",
            "mime_type": content_type or "application/octet-stream",
            "hash": file_hash,
            "created_by": str(created_by),
            "created_at": datetime.utcnow(),
            "used": False,
            "used_by": None,
            "used_at": None,
        }
        
        await files_collection.insert_one(file_doc)
        
        return {
            "id": file_id,
            "name": filename,
            "size": file_size,
            "extension": extension,
            "mime_type": content_type,
            "hash": file_hash,
            "created_at": file_doc["created_at"],
        }
    
    async def download_file(self, file_id: str) -> tuple[bytes, dict]:
        """
        Download file from GridFS.
        
        Args:
            file_id: File ID
        
        Returns:
            tuple: (file_data, metadata)
        
        Raises:
            FileNotFoundError: If file not found
        """
        # Get metadata from upload_files collection
        files_collection = self.mongo.get_collection("upload_files")
        file_doc = await files_collection.find_one({"_id": file_id})
        
        if not file_doc:
            raise FileNotFoundError(f"File {file_id} not found")
        
        # Download from GridFS
        from bson import ObjectId
        gridfs_bucket = self.mongo.get_gridfs()
        gridfs_id = ObjectId(file_doc["gridfs_id"])
        
        grid_out = await gridfs_bucket.open_download_stream(gridfs_id)
        file_data = await grid_out.read()
        
        metadata = {
            "id": file_doc["_id"],
            "name": file_doc["name"],
            "size": file_doc["size"],
            "extension": file_doc.get("extension", ""),
            "mime_type": file_doc.get("mime_type", "application/octet-stream"),
            "hash": file_doc.get("hash", ""),
            "created_at": file_doc.get("created_at"),
        }
        
        return file_data, metadata
    
    async def delete_file(self, file_id: str) -> bool:
        """
        Delete file from GridFS and metadata.
        
        Args:
            file_id: File ID
        
        Returns:
            bool: True if deleted successfully
        """
        # Get metadata
        files_collection = self.mongo.get_collection("upload_files")
        file_doc = await files_collection.find_one({"_id": file_id})
        
        if not file_doc:
            return False
        
        # Delete from GridFS
        from bson import ObjectId
        gridfs_bucket = self.mongo.get_gridfs()
        gridfs_id = ObjectId(file_doc["gridfs_id"])
        await gridfs_bucket.delete(gridfs_id)
        
        # Delete metadata
        await files_collection.delete_one({"_id": file_id})
        
        return True
    
    async def get_file_metadata(self, file_id: str) -> Optional[dict]:
        """
        Get file metadata without downloading the file.
        
        Args:
            file_id: File ID
        
        Returns:
            dict: File metadata or None if not found
        """
        files_collection = self.mongo.get_collection("upload_files")
        file_doc = await files_collection.find_one({"_id": file_id})
        
        if not file_doc:
            return None
        
        return {
            "id": file_doc["_id"],
            "name": file_doc["name"],
            "size": file_doc["size"],
            "extension": file_doc.get("extension", ""),
            "mime_type": file_doc.get("mime_type", "application/octet-stream"),
            "hash": file_doc.get("hash", ""),
            "created_by": file_doc.get("created_by"),
            "created_at": file_doc.get("created_at"),
            "used": file_doc.get("used", False),
        }
    
    async def mark_file_used(self, file_id: str, used_by: str) -> bool:
        """
        Mark file as used.
        
        Args:
            file_id: File ID
            used_by: Resource ID that uses this file
        
        Returns:
            bool: True if updated successfully
        """
        files_collection = self.mongo.get_collection("upload_files")
        result = await files_collection.update_one(
            {"_id": file_id},
            {
                "$set": {
                    "used": True,
                    "used_by": used_by,
                    "used_at": datetime.utcnow(),
                }
            }
        )
        
        return result.modified_count > 0
    
    async def list_files(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        """
        List files for a tenant.
        
        Args:
            tenant_id: Tenant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            list: List of file metadata
        """
        files_collection = self.mongo.get_collection("upload_files")
        cursor = files_collection.find(
            {"tenant_id": str(tenant_id)}
        ).skip(skip).limit(limit).sort("created_at", -1)
        
        files = []
        async for file_doc in cursor:
            files.append({
                "id": file_doc["_id"],
                "name": file_doc["name"],
                "size": file_doc["size"],
                "extension": file_doc.get("extension", ""),
                "mime_type": file_doc.get("mime_type", "application/octet-stream"),
                "created_at": file_doc.get("created_at"),
                "used": file_doc.get("used", False),
            })
        
        return files


# Global file service instance
file_service = FileService()
