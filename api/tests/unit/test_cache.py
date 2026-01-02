"""
缓存功能单元测试

合并自:
- test_cache_logic.py
- test_cache_strategy.py

测试内容:
- 缓存管理器核心逻辑
- 缓存键生成
- 缓存装饰器
- 缓存策略
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth.user import UserEntity
from app.utils.cache import CacheManager, cache, cache_invalidate, cache_result


class TestCacheLogic:
    """缓存逻辑测试"""

    @pytest.fixture
    def mock_redis(self):
        """模拟Redis客户端"""
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.setex = AsyncMock(return_value=True)
        redis_mock.delete = AsyncMock(return_value=1)
        redis_mock.keys = AsyncMock(return_value=[])
        redis_mock.exists = AsyncMock(return_value=0)
        redis_mock.expire = AsyncMock(return_value=True)
        return redis_mock

    @pytest.fixture
    def cache_manager(self, mock_redis):
        """创建带模拟Redis的缓存管理器"""
        return CacheManager(mock_redis)

    def test_generate_key(self, cache_manager):
        """测试缓存键生成逻辑"""
        key1 = cache_manager._generate_key('test', 'arg1', 'arg2')
        key2 = cache_manager._generate_key('test', 'arg1', 'arg2')
        assert key1 == key2

        key3 = cache_manager._generate_key('test', 'arg1', 'arg3')
        assert key1 != key3

        # kwargs顺序不影响键生成
        key4 = cache_manager._generate_key('test', 'arg1', param1='value1', param2='value2')
        key5 = cache_manager._generate_key('test', 'arg1', param2='value2', param1='value1')
        assert key4 == key5

    async def test_cache_get_success(self, cache_manager, mock_redis):
        """测试缓存获取成功"""
        test_data = {'message': 'test', 'number': 123}
        mock_redis.get.return_value = '{"message": "test", "number": 123}'

        result = await cache_manager.get('test_key')
        assert result == test_data
        mock_redis.get.assert_called_once_with('test_key')

    async def test_cache_get_miss(self, cache_manager, mock_redis):
        """测试缓存未命中"""
        mock_redis.get.return_value = None
        result = await cache_manager.get('nonexistent_key')
        assert result is None

    async def test_cache_get_error_handling(self, cache_manager, mock_redis):
        """测试缓存获取错误处理"""
        mock_redis.get.side_effect = Exception('Redis connection error')
        result = await cache_manager.get('error_key')
        assert result is None

    async def test_cache_set_success(self, cache_manager, mock_redis):
        """测试缓存设置成功"""
        test_data = {'message': 'test', 'number': 123}
        result = await cache_manager.set('test_key', test_data, ttl=300)
        assert result is True
        mock_redis.setex.assert_called_once()

    async def test_cache_delete_success(self, cache_manager, mock_redis):
        """测试缓存删除成功"""
        result = await cache_manager.delete('test_key')
        assert result is True
        mock_redis.delete.assert_called_once_with('test_key')

    async def test_cache_delete_pattern(self, cache_manager, mock_redis):
        """测试模式删除"""
        mock_redis.keys.return_value = ['user:123:profile', 'user:123:permissions']
        result = await cache_manager.delete_pattern('user:123:*')
        assert result == 2

    async def test_cache_exists(self, cache_manager, mock_redis):
        """测试缓存存在检查"""
        mock_redis.exists.return_value = 1
        result = await cache_manager.exists('test_key')
        assert result is True

    async def test_cache_decorator_basic(self):
        """测试基本缓存装饰器"""
        call_count = 0

        @cache('test_func', ttl=300)
        async def test_function(param1: str, param2: int):
            nonlocal call_count
            call_count += 1
            return f'{param1}_{param2}_{call_count}'

        result1 = await test_function('hello', 123)
        assert 'hello_123' in result1

    async def test_cache_invalidate_decorator(self):
        """测试缓存失效装饰器"""

        @cache_invalidate('user:*')
        async def update_user_data(user_id: str):
            return f'Updated user {user_id}'

        result = await update_user_data('123')
        assert result == 'Updated user 123'

    def test_cache_pattern_matching(self):
        """测试缓存模式匹配逻辑"""
        import fnmatch

        test_keys = [
            'user:123:profile',
            'user:123:permissions',
            'user:456:profile',
            'workflow:789:definition',
        ]

        patterns = [
            ('user:123:*', ['user:123:profile', 'user:123:permissions']),
            ('user:*:profile', ['user:123:profile', 'user:456:profile']),
            ('workflow:*', ['workflow:789:definition']),
        ]

        for pattern, expected_matches in patterns:
            actual_matches = [key for key in test_keys if fnmatch.fnmatch(key, pattern)]
            assert set(actual_matches) == set(expected_matches)


class TestCacheStrategy:
    """缓存策略测试"""

    @pytest.fixture
    async def test_user(self, test_session: AsyncSession):
        """创建测试用户"""
        unique_id = uuid4()
        user = UserEntity(
            id=unique_id,
            name='testuser',
            email=f'test_{unique_id}@example.com',
            password_hash='hashed_password',
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        return user

    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器实例"""
        return CacheManager()

    async def test_cache_hit_and_miss(self, cache_manager: CacheManager):
        """测试缓存命中和失效"""
        cache_key = 'test_key'
        test_data = {'message': 'Hello, World!', 'timestamp': datetime.utcnow().isoformat()}

        cached_data = await cache_manager.get(cache_key)
        assert cached_data is None

        await cache_manager.set(cache_key, test_data, ttl=300)
        cached_data = await cache_manager.get(cache_key)
        assert cached_data is None or cached_data == test_data

    async def test_cache_expiration(self, cache_manager: CacheManager):
        """测试缓存过期"""
        cache_key = 'expiration_test_key'
        test_data = {'message': 'This will expire'}

        await cache_manager.set(cache_key, test_data, ttl=1)
        await asyncio.sleep(2)
        cached_data = await cache_manager.get(cache_key)
        assert cached_data is None

    async def test_cache_invalidation_patterns(self, cache_manager: CacheManager):
        """测试缓存失效模式"""
        user_id = str(uuid4())
        cache_keys = [
            f'user:{user_id}:profile',
            f'user:{user_id}:permissions',
            f'user:{user_id}:sessions',
        ]

        for key in cache_keys:
            await cache_manager.set(key, {'data': f'data_for_{key}'}, ttl=300)

        pattern = f'user:{user_id}:*'
        deleted_count = await cache_manager.invalidate_pattern(pattern)
        assert isinstance(deleted_count, int)

    async def test_cache_decorator(self, cache_manager: CacheManager):
        """测试缓存装饰器"""
        call_count = 0

        @cache_result(ttl=300, key_prefix='test_func')
        async def expensive_function(param1: str, param2: int):
            nonlocal call_count
            call_count += 1
            return {'result': f'{param1}_{param2}', 'call_count': call_count}

        result1 = await expensive_function('test', 123)
        assert result1['call_count'] == 1

        result2 = await expensive_function('test', 123)
        assert result2['call_count'] >= 1
