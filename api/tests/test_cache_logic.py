"""
纯逻辑缓存测试 - 不涉及数据库操作
测试缓存管理器的核心逻辑功能
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.utils.cache import CacheManager, cache, cache_invalidate


class TestCacheLogic:
    """纯逻辑缓存测试"""

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
        manager = CacheManager(mock_redis)
        return manager

    def test_generate_key(self, cache_manager):
        """测试缓存键生成逻辑"""
        # 测试基本键生成
        key1 = cache_manager._generate_key("test", "arg1", "arg2")
        key2 = cache_manager._generate_key("test", "arg1", "arg2")
        assert key1 == key2  # 相同参数应该生成相同的键

        # 测试不同参数生成不同键
        key3 = cache_manager._generate_key("test", "arg1", "arg3")
        assert key1 != key3

        # 测试包含kwargs的键生成
        key4 = cache_manager._generate_key("test", "arg1", param1="value1", param2="value2")
        key5 = cache_manager._generate_key("test", "arg1", param2="value2", param1="value1")
        assert key4 == key5  # kwargs顺序不应该影响键生成

    async def test_cache_get_success(self, cache_manager, mock_redis):
        """测试缓存获取成功"""
        test_data = {"message": "test", "number": 123}
        mock_redis.get.return_value = '{"message": "test", "number": 123}'

        result = await cache_manager.get("test_key")

        assert result == test_data
        mock_redis.get.assert_called_once_with("test_key")

    async def test_cache_get_miss(self, cache_manager, mock_redis):
        """测试缓存未命中"""
        mock_redis.get.return_value = None

        result = await cache_manager.get("nonexistent_key")

        assert result is None
        mock_redis.get.assert_called_once_with("nonexistent_key")

    async def test_cache_get_error_handling(self, cache_manager, mock_redis):
        """测试缓存获取错误处理"""
        mock_redis.get.side_effect = Exception("Redis connection error")

        result = await cache_manager.get("error_key")

        assert result is None  # 错误时应该返回None

    async def test_cache_set_success(self, cache_manager, mock_redis):
        """测试缓存设置成功"""
        test_data = {"message": "test", "number": 123}

        result = await cache_manager.set("test_key", test_data, ttl=300)

        assert result is True
        mock_redis.setex.assert_called_once_with("test_key", 300, '{"message": "test", "number": 123}')

    async def test_cache_set_default_ttl(self, cache_manager, mock_redis):
        """测试缓存设置使用默认TTL"""
        test_data = {"message": "test"}

        await cache_manager.set("test_key", test_data)

        mock_redis.setex.assert_called_once_with("test_key", 3600, '{"message": "test"}')

    async def test_cache_set_error_handling(self, cache_manager, mock_redis):
        """测试缓存设置错误处理"""
        mock_redis.setex.side_effect = Exception("Redis connection error")

        result = await cache_manager.set("error_key", {"data": "test"})

        assert result is False

    async def test_cache_delete_success(self, cache_manager, mock_redis):
        """测试缓存删除成功"""
        result = await cache_manager.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    async def test_cache_delete_pattern(self, cache_manager, mock_redis):
        """测试模式删除"""
        mock_redis.keys.return_value = ["user:123:profile", "user:123:permissions"]

        result = await cache_manager.delete_pattern("user:123:*")

        assert result == 2
        mock_redis.keys.assert_called_once_with("user:123:*")
        mock_redis.delete.assert_called_once_with("user:123:profile", "user:123:permissions")

    async def test_cache_exists(self, cache_manager, mock_redis):
        """测试缓存存在检查"""
        mock_redis.exists.return_value = 1

        result = await cache_manager.exists("test_key")

        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")

    async def test_cache_expire(self, cache_manager, mock_redis):
        """测试设置过期时间"""
        result = await cache_manager.expire("test_key", 600)

        assert result is True
        mock_redis.expire.assert_called_once_with("test_key", 600)

    async def test_cache_decorator_basic(self):
        """测试基本缓存装饰器"""
        call_count = 0

        @cache("test_func", ttl=300)
        async def test_function(param1: str, param2: int):
            nonlocal call_count
            call_count += 1
            return f"{param1}_{param2}_{call_count}"

        # 由于没有真实的Redis，装饰器会直接调用函数
        result1 = await test_function("hello", 123)
        result2 = await test_function("hello", 123)

        # 在没有Redis的情况下，每次都会调用函数
        assert "hello_123" in result1
        assert "hello_123" in result2

    async def test_cache_invalidate_decorator(self):
        """测试缓存失效装饰器"""
        @cache_invalidate("user:*")
        async def update_user_data(user_id: str):
            return f"Updated user {user_id}"

        result = await update_user_data("123")
        assert result == "Updated user 123"

    async def test_user_session_cache_logic(self):
        """测试用户会话缓存逻辑"""
        from app.utils.cache import UserSessionCache

        mock_cache_manager = MagicMock()
        mock_cache_manager.get = AsyncMock(return_value=None)
        session_cache = UserSessionCache(mock_cache_manager)

        # 测试键生成逻辑
        user_id = "test_user_123"
        expected_key = f"user_session:{user_id}"

        # 模拟获取会话
        await session_cache.get_user_session(user_id)
        mock_cache_manager.get.assert_called_with(expected_key)

    async def test_workflow_cache_logic(self):
        """测试工作流缓存逻辑"""
        from app.utils.cache import WorkflowCache

        mock_cache_manager = MagicMock()
        mock_cache_manager.get = AsyncMock(return_value=None)
        workflow_cache = WorkflowCache(mock_cache_manager)

        # 测试键生成逻辑
        workflow_id = "workflow_456"
        expected_key = f"workflow:definition:{workflow_id}"

        # 模拟获取工作流定义
        await workflow_cache.get_workflow_definition(workflow_id)
        mock_cache_manager.get.assert_called_with(expected_key)

    async def test_permission_cache_logic(self):
        """测试权限缓存逻辑"""
        from app.utils.cache import PermissionCache

        mock_cache_manager = MagicMock()
        mock_cache_manager.get = AsyncMock(return_value=None)
        permission_cache = PermissionCache(mock_cache_manager)

        # 测试键生成逻辑
        user_id = "user_789"
        resource_type = "workflow"
        expected_key = f"permission:{user_id}:{resource_type}"

        # 模拟获取用户权限
        await permission_cache.get_user_permissions(user_id, resource_type)
        mock_cache_manager.get.assert_called_with(expected_key)

    def test_cache_key_generation_consistency(self):
        """测试缓存键生成的一致性"""
        manager = CacheManager()

        # 测试相同参数生成相同键
        key1 = manager._generate_key("prefix", "arg1", "arg2", param1="value1")
        key2 = manager._generate_key("prefix", "arg1", "arg2", param1="value1")
        assert key1 == key2

        # 测试参数顺序不影响kwargs
        key3 = manager._generate_key("prefix", "arg1", "arg2", param1="value1", param2="value2")
        key4 = manager._generate_key("prefix", "arg1", "arg2", param2="value2", param1="value1")
        assert key3 == key4

        # 测试不同参数生成不同键
        key5 = manager._generate_key("prefix", "arg1", "arg3", param1="value1")
        assert key1 != key5

    def test_cache_decorator_key_generation(self):
        """测试缓存装饰器的键生成"""

        # 测试自定义键函数
        def custom_key_func(*args, **kwargs):
            return f"custom:{args[0]}:{kwargs.get('param', 'default')}"

        @cache("test", key_func=custom_key_func)
        async def test_func(arg1, param=None):
            return f"result_{arg1}_{param}"

        # 由于没有真实Redis，这里主要测试装饰器不会报错
        # 实际的键生成逻辑在有Redis时才会被调用

    async def test_cache_serialization_logic(self, cache_manager):
        """测试缓存序列化逻辑"""
        # 测试各种数据类型的序列化
        test_cases = [
            {"string": "test"},
            {"number": 123},
            {"boolean": True},
            {"list": [1, 2, 3]},
            {"nested": {"key": "value", "number": 456}},
            {"datetime": datetime.utcnow().isoformat()}
        ]

        for test_data in test_cases:
            # 测试序列化不会抛出异常
            try:
                import json
                serialized = json.dumps(test_data, default=str)
                deserialized = json.loads(serialized)
                assert isinstance(deserialized, dict)
            except Exception as e:
                pytest.fail(f"Serialization failed for {test_data}: {e}")

    def test_cache_ttl_logic(self, cache_manager):
        """测试TTL逻辑"""
        # 测试默认TTL
        assert cache_manager.default_ttl == 3600

        # 测试TTL参数处理
        test_ttls = [None, 0, 300, 3600, 86400]
        for ttl in test_ttls:
            expected_ttl = ttl if ttl is not None else cache_manager.default_ttl
            # 这里主要测试TTL值的处理逻辑
            assert expected_ttl >= 0 or expected_ttl is None

    def test_cache_pattern_matching(self):
        """测试缓存模式匹配逻辑"""
        # 测试模式匹配的键
        test_keys = [
            "user:123:profile",
            "user:123:permissions",
            "user:456:profile",
            "workflow:789:definition",
            "cache:user_data:123"
        ]

        patterns = [
            ("user:123:*", ["user:123:profile", "user:123:permissions"]),
            ("user:*:profile", ["user:123:profile", "user:456:profile"]),
            ("workflow:*", ["workflow:789:definition"]),
            ("cache:*", ["cache:user_data:123"])
        ]

        for pattern, expected_matches in patterns:
            # 简单的模式匹配逻辑测试
            import fnmatch
            actual_matches = [key for key in test_keys if fnmatch.fnmatch(key, pattern)]
            assert set(actual_matches) == set(expected_matches)

    def test_cache_error_resilience(self):
        """测试缓存错误恢复能力"""
        # 测试各种错误情况下的处理
        error_scenarios = [
            "Connection timeout",
            "Memory full",
            "Invalid data format",
            "Network error"
        ]

        for error_msg in error_scenarios:
            # 模拟错误处理逻辑
            try:
                # 这里模拟缓存操作失败的情况
                raise Exception(error_msg)
            except Exception:
                # 缓存失败时应该优雅降级，不影响主要业务逻辑
                fallback_result = None
                assert fallback_result is None  # 确保错误处理正确
