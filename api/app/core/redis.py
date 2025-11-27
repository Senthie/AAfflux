"""Redis connection and cache management."""

from typing import Optional, Any
import json
from redis.asyncio import Redis, ConnectionPool
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
            raise ConnectionError(f"Failed to connect to Redis: {e}")

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
            raise RuntimeError("Redis not connected")
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
            raise RuntimeError("Redis not connected")
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
            raise RuntimeError("Redis not connected")
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
            raise RuntimeError("Redis not connected")
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


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """
    Dependency for getting Redis client.

    Returns:
        RedisClient instance
    """
    return redis_client
