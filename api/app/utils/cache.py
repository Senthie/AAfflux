"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-22 10:27:08
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-22 11:54:16
FilePath: : AAfflux: api: app: utils: cache.py
Description:缓存装饰器和工具函数
"""

import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """缓存管理器"""

    def __init__(self, redis_client=None):
        self.redis = redis_client or redis_client
        self.default_ttl = 3600  # 默认1小时过期

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 创建一个包含所有参数的字符串
        key_data = f'{prefix}:{args}:{sorted(kwargs.items())}'
        # 使用MD5哈希来创建固定长度的键
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f'cache:{prefix}:{key_hash}'

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            if not self.redis:
                return None

            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f'Cache get error for key {key}: {e}')
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            if not self.redis:
                return False

            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.warning(f'Cache set error for key {key}: {e}')
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            if not self.redis:
                return False

            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f'Cache delete error for key {key}: {e}')
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的缓存键"""
        try:
            if not self.redis:
                return 0

            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.warning(f'Cache delete pattern error for pattern {pattern}: {e}')
            return 0

    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在"""
        try:
            if not self.redis:
                return False

            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.warning(f'Cache exists error for key {key}: {e}')
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """设置缓存键的过期时间"""
        try:
            if not self.redis:
                return False

            await self.redis.expire(key, ttl)
            return True
        except Exception as e:
            logger.warning(f'Cache expire error for key {key}: {e}')
            return False


# 全局缓存管理器实例
cache_manager = CacheManager()


def cache(prefix: str, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """缓存装饰器

    Args:
        prefix: 缓存键前缀
        ttl: 过期时间（秒）
        key_func: 自定义键生成函数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_key(prefix, *args, **kwargs)

            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f'Cache hit for key: {cache_key}')
                return cached_result

            # 执行原函数
            logger.debug(f'Cache miss for key: {cache_key}')
            result = await func(*args, **kwargs)

            # 存储到缓存
            await cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def cache_invalidate(pattern: str):
    """缓存失效装饰器"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # 删除匹配的缓存
            deleted_count = await cache_manager.delete_pattern(pattern)
            if deleted_count > 0:
                logger.info(f'Invalidated {deleted_count} cache entries with pattern: {pattern}')

            return result

        return wrapper

    return decorator


class UserSessionCache:
    """用户会话缓存"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.prefix = 'user_session'
        self.ttl = 3600 * 24  # 24小时

    async def get_user_session(self, user_id: str) -> Optional[dict]:
        """获取用户会话信息"""
        key = f'{self.prefix}:{user_id}'
        return await self.cache.get(key)

    async def set_user_session(self, user_id: str, session_data: dict) -> bool:
        """设置用户会话信息"""
        key = f'{self.prefix}:{user_id}'
        return await self.cache.set(key, session_data, self.ttl)

    async def delete_user_session(self, user_id: str) -> bool:
        """删除用户会话信息"""
        key = f'{self.prefix}:{user_id}'
        return await self.cache.delete(key)


class WorkflowCache:
    """工作流缓存"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.prefix = 'workflow'
        self.ttl = 3600 * 2  # 2小时

    async def get_workflow_definition(self, workflow_id: str) -> Optional[dict]:
        """获取工作流定义"""
        key = f'{self.prefix}:definition:{workflow_id}'
        return await self.cache.get(key)

    async def set_workflow_definition(self, workflow_id: str, definition: dict) -> bool:
        """设置工作流定义"""
        key = f'{self.prefix}:definition:{workflow_id}'
        return await self.cache.set(key, definition, self.ttl)

    async def invalidate_workflow_cache(self, workflow_id: str) -> int:
        """失效工作流相关缓存"""
        pattern = f'{self.prefix}:*:{workflow_id}'
        return await self.cache.delete_pattern(pattern)


class PermissionCache:
    """权限缓存"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.prefix = 'permission'
        self.ttl = 3600  # 1小时

    async def get_user_permissions(self, user_id: str, resource_type: str) -> Optional[list]:
        """获取用户权限"""
        key = f'{self.prefix}:{user_id}:{resource_type}'
        return await self.cache.get(key)

    async def set_user_permissions(
        self, user_id: str, resource_type: str, permissions: list
    ) -> bool:
        """设置用户权限"""
        key = f'{self.prefix}:{user_id}:{resource_type}'
        return await self.cache.set(key, permissions, self.ttl)

    async def invalidate_user_permissions(self, user_id: str) -> int:
        """失效用户权限缓存"""
        pattern = f'{self.prefix}:{user_id}:*'
        return await self.cache.delete_pattern(pattern)


# 创建缓存实例
user_session_cache = UserSessionCache(cache_manager)
workflow_cache = WorkflowCache(cache_manager)
permission_cache = PermissionCache(cache_manager)


# 添加缺失的方法到CacheManager
async def invalidate_pattern(self, pattern: str) -> int:
    """失效匹配模式的缓存键"""
    return await self.delete_pattern(pattern)


async def set_with_notification(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """设置缓存值并发送通知"""
    result = await self.set(key, value, ttl)
    if result:
        # 这里可以添加通知逻辑，比如发布Redis消息
        logger.info(f'Cache updated with notification: {key}')
    return result


async def get_statistics(self) -> Optional[dict]:
    """获取缓存统计信息"""
    try:
        if not self.redis:
            return None

        # 模拟统计信息
        return {'hits': 0, 'misses': 0, 'total_keys': 0}
    except Exception as e:
        logger.warning(f'Cache statistics error: {e}')
        return None


async def get_memory_info(self) -> Optional[dict]:
    """获取内存信息"""
    try:
        if not self.redis:
            return None

        # 模拟内存信息
        return {'used_memory': 0, 'max_memory': 0}
    except Exception as e:
        logger.warning(f'Cache memory info error: {e}')
        return None


# 将这些方法添加到CacheManager类
CacheManager.invalidate_pattern = invalidate_pattern
CacheManager.set_with_notification = set_with_notification
CacheManager.get_statistics = get_statistics
CacheManager.get_memory_info = get_memory_info


# 添加cache_result装饰器
def cache_result(ttl: Optional[int] = None, key_prefix: str = 'result'):
    """缓存结果装饰器"""
    return cache(key_prefix, ttl)


# 常用缓存装饰器
def cache_user_data(ttl: int = 3600):
    """用户数据缓存装饰器"""
    return cache('user_data', ttl)


def cache_workflow_data(ttl: int = 7200):
    """工作流数据缓存装饰器"""
    return cache('workflow_data', ttl)


def cache_execution_stats(ttl: int = 1800):
    """执行统计缓存装饰器"""
    return cache('execution_stats', ttl)


def invalidate_user_cache(user_id: str):
    """失效用户相关缓存"""
    return cache_invalidate(f'cache:user_*:{user_id}*')


def invalidate_workflow_cache(workflow_id: str):
    """失效工作流相关缓存"""
    return cache_invalidate(f'cache:workflow_*:{workflow_id}*')
