"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/core/redis.py
Description: Redis连接管理

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

import json
from typing import Any, Optional

from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError

from app.core.config import settings


class RedisClient:
    """Redis client wrapper for caching."""

    def __init__(self) -> None:
        """Initialize Redis client."""
        self.pool: Optional[ConnectionPool] = None
        self.redis: Optional[Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.pool = ConnectionPool.from_url(
                settings.redis_url,
                db=settings.redis_db,
                max_connections=settings.redis_max_connections,
                decode_responses=True,
            )
            self.redis = Redis(connection_pool=self.pool)

            # Verify connection
            await self.redis.ping()
        except RedisError as e:
            raise ConnectionError(f'Failed to connect to Redis: {e}') from e

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None
        if self.pool:
            await self.pool.disconnect()
            self.pool = None

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.redis:
            raise RuntimeError('Redis not connected')
        return await self.redis.get(key)

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds

        Returns:
            True if successful
        """
        if not self.redis:
            raise RuntimeError('Redis not connected')
        return await self.redis.set(key, value, ex=expire)

    async def delete(self, key: str) -> int:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            Number of keys deleted
        """
        if not self.redis:
            raise RuntimeError('Redis not connected')
        return await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        if not self.redis:
            raise RuntimeError('Redis not connected')
        return await self.redis.exists(key) > 0

    async def get_json(self, key: str) -> Optional[Any]:
        """
        Get JSON value from cache.

        Args:
            key: Cache key

        Returns:
            Deserialized JSON value or None
        """
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Set JSON value in cache.

        Args:
            key: Cache key
            value: Value to serialize and cache
            expire: Expiration time in seconds

        Returns:
            True if successful
        """
        json_value = json.dumps(value)
        return await self.set(key, json_value, expire)

    async def incr(self, key: str) -> int:
        """
        Increment value in cache.

        Args:
            key: Cache key

        Returns:
            New value after increment
        """
        if not self.redis:
            raise RuntimeError('Redis not connected')
        return await self.redis.incr(key)

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for key.

        Args:
            key: Cache key
            seconds: Expiration time in seconds

        Returns:
            True if successful
        """
        if not self.redis:
            raise RuntimeError('Redis not connected')
        return await self.redis.expire(key, seconds)

    async def setex(self, key: str, seconds: int, value: str) -> bool:
        """
        Set value with expiration time.

        Args:
            key: Cache key
            seconds: Expiration time in seconds
            value: Value to set

        Returns:
            True if successful
        """
        if not self.redis:
            raise RuntimeError('Redis not connected')
        return await self.redis.setex(key, seconds, value)


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """
    Dependency for getting Redis client.

    Returns:
        RedisClient instance
    """
    return redis_client
