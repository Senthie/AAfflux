"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/tests/unit/test_utils.py
Description: Test Utils工具

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

"""
工具函数单元测试

合并自:
- test_pure_logic.py
- test_utils_logic.py
- test_invitation_security.py

测试内容:
- 纯逻辑函数测试
- API密钥生成和验证
- Token创建和验证
- 邀请安全功能
"""

from datetime import datetime, timedelta
import hashlib
import json
import re
from uuid import uuid4

import pytest

from app.utils.api_key import APIKeyGenerator, APIKeyValidator
from app.utils.invitation_security import InvitationSecurityManager
from app.utils.token import generate_access_token, verify_token


class TestPureLogic:
    """纯逻辑测试"""

    def test_uuid_generation_logic(self):
        """测试UUID生成逻辑"""
        uuids = set()
        for _ in range(1000):
            new_uuid = uuid4()
            assert new_uuid not in uuids
            uuids.add(new_uuid)
            uuid_str = str(new_uuid)
            assert len(uuid_str) == 36
            assert uuid_str.count('-') == 4

    def test_datetime_logic(self):
        """测试日期时间逻辑"""
        now = datetime.utcnow()
        future = now + timedelta(hours=1)
        past = now - timedelta(hours=1)

        assert future > now
        assert past < now
        assert (future - now).total_seconds() == 3600

    def test_hash_consistency(self):
        """测试哈希一致性"""
        test_data = 'test_string_for_hashing'
        hash1 = hashlib.md5(test_data.encode()).hexdigest()
        hash2 = hashlib.md5(test_data.encode()).hexdigest()
        assert hash1 == hash2

        hash3 = hashlib.md5('different_string'.encode()).hexdigest()
        assert hash1 != hash3

    def test_json_serialization_logic(self):
        """测试JSON序列化逻辑"""
        test_cases = [
            {'string': 'test', 'number': 123, 'boolean': True},
            {'list': [1, 2, 3], 'nested': {'key': 'value'}},
            {'uuid': str(uuid4())},
            {'empty_dict': {}, 'empty_list': []},
            {'null_value': None},
        ]

        for test_data in test_cases:
            serialized = json.dumps(test_data, default=str)
            assert isinstance(serialized, str)
            deserialized = json.loads(serialized)
            assert isinstance(deserialized, dict)

    def test_string_validation_logic(self):
        """测试字符串验证逻辑"""
        valid_emails = ['test@example.com', 'user.name@domain.co.uk']
        invalid_emails = ['', 'invalid', '@example.com', 'test@']
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        for email in valid_emails:
            assert re.match(email_pattern, email) is not None

        for email in invalid_emails:
            assert re.match(email_pattern, email) is None

    def test_pagination_logic(self):
        """测试分页逻辑"""
        total_items = 100
        page_size = 10
        total_pages = (total_items + page_size - 1) // page_size
        assert total_pages == 10

        for page in range(1, total_pages + 1):
            start_index = (page - 1) * page_size
            end_index = min(start_index + page_size, total_items)
            assert start_index >= 0
            assert end_index <= total_items

    def test_error_code_logic(self):
        """测试错误代码逻辑"""
        error_mappings = {
            400: 'BAD_REQUEST',
            401: 'UNAUTHORIZED',
            403: 'FORBIDDEN',
            404: 'NOT_FOUND',
            422: 'VALIDATION_ERROR',
            500: 'INTERNAL_SERVER_ERROR',
        }

        for status_code, _error_code in error_mappings.items():
            assert isinstance(status_code, int)
            assert status_code >= 400

    def test_sorting_logic(self):
        """测试排序逻辑"""
        numbers = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3]
        sorted_numbers = sorted(numbers)
        assert sorted_numbers == [1, 1, 2, 3, 3, 4, 5, 5, 6, 9]

        data = [
            {'name': 'Alice', 'age': 30},
            {'name': 'Bob', 'age': 25},
            {'name': 'Charlie', 'age': 35},
        ]
        sorted_by_age = sorted(data, key=lambda x: x['age'])
        assert sorted_by_age[0]['name'] == 'Bob'

    def test_filtering_logic(self):
        """测试过滤逻辑"""
        numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        even_numbers = [n for n in numbers if n % 2 == 0]
        assert even_numbers == [2, 4, 6, 8, 10]

    def test_aggregation_logic(self):
        """测试聚合逻辑"""
        numbers = [1, 2, 3, 4, 5]
        assert sum(numbers) == 15
        assert max(numbers) == 5
        assert min(numbers) == 1


class TestAPIKeyUtils:
    """API密钥工具测试"""

    def test_api_key_generation(self):
        """测试API密钥生成逻辑"""
        generator = APIKeyGenerator()
        api_key = generator.generate_api_key()
        assert api_key is not None
        assert len(api_key) > 0

        validator = APIKeyValidator()
        assert validator.validate_key_format(api_key) is True

        # 测试唯一性
        keys = set()
        for _ in range(100):
            key = generator.generate_api_key()
            assert key not in keys
            keys.add(key)

    def test_api_key_validation(self):
        """测试API密钥验证逻辑"""
        validator = APIKeyValidator()
        generator = APIKeyGenerator()

        valid_key = generator.generate_api_key()
        assert validator.validate_key_format(valid_key) is True

        invalid_keys = ['', 'invalid', 'ak_', 'ak_short']
        for key in invalid_keys:
            assert validator.validate_key_format(key) is False


class TestTokenUtils:
    """Token工具测试"""

    def test_token_creation_and_validation(self):
        """测试令牌创建和验证逻辑"""
        user_id = uuid4()
        additional_claims = {'email': 'test@example.com', 'permissions': ['read', 'write']}

        token = generate_access_token(user_id, additional_claims)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        payload = verify_token(token, 'access')
        if payload:
            assert payload['user_id'] == str(user_id)
            assert 'exp' in payload


class TestInvitationSecurity:
    """邀请安全功能测试"""

    @pytest.mark.asyncio
    async def test_invitation_security(self):
        """测试邀请安全功能"""

        class MockRedis:
            def __init__(self):
                self.data = {}

            async def get(self, key):
                return self.data.get(key)

            async def incr(self, key):
                self.data[key] = int(self.data.get(key, 0)) + 1
                return self.data[key]

            async def expire(self, key, seconds):
                return True

            async def setex(self, key, seconds, value):
                self.data[key] = value
                return True

            async def exists(self, key):
                return key in self.data

        redis_client = MockRedis()
        security_manager = InvitationSecurityManager(redis_client)

        team_id = uuid4()
        email = 'test@example.com'
        token = security_manager.generate_secure_token(team_id, email)
        assert token is not None

        is_valid = security_manager.verify_token_signature(token, team_id, email)
        assert is_valid is True

        user_id = uuid4()
        for _i in range(3):
            rate_check = await security_manager.check_rate_limit(user_id)
            assert rate_check['allowed'] is True
            await security_manager.increment_rate_limit(user_id)
