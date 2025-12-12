"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-02 08:50:10
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-10 11:27:03
FilePath: : AAfflux: api: app: core: mongodb.py
Description:
"""

"""MongoDB connection and GridFS support."""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from pymongo.errors import ConnectionFailure

from app.core.config import settings


class MongoDBClient:
    """MongoDB client wrapper with GridFS support."""

    # 添加 db_name 属性
    @property
    def db_name(self) -> str:
        return settings.mongodb_database

    def __init__(self) -> None:
        """Initialize MongoDB client."""
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.gridfs_bucket: Optional[AsyncIOMotorGridFSBucket] = None

    async def connect(self) -> None:
        """Connect to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.database = self.client[settings.mongodb_database]
            self.gridfs_bucket = AsyncIOMotorGridFSBucket(self.database)

            # Verify connection
            await self.client.admin.command('ping')
        except ConnectionFailure as e:
            raise ConnectionError(f'Failed to connect to MongoDB: {e}') from e

    async def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            self.gridfs_bucket = None

    def get_collection(self, name: str):
        """
        Get a MongoDB collection.

        Args:
            name: Collection name

        Returns:
            Collection instance
        """
        if not self.database:
            raise RuntimeError('MongoDB not connected')
        return self.database[name]

    def get_gridfs(self) -> AsyncIOMotorGridFSBucket:
        """
        Get GridFS bucket for large file storage.

        Returns:
            GridFS bucket instance
        """
        if not self.gridfs_bucket:
            raise RuntimeError('MongoDB not connected')
        return self.gridfs_bucket


# Global MongoDB client instance
mongodb_client = MongoDBClient()


async def get_mongodb():
    """
    Dependency for getting MongoDB client.

    Returns:
        MongoDBClient instance
    """
    return mongodb_client
