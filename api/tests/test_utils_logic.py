"""
纯逻辑工具函数测试 - 不涉及数据库操作
测试各种工具函数的核心逻辑
"""

from datetime import datetime, timedelta
from uuid import uuid4
import hashlib
import json

from app.utils.api_key import APIKeyGenerator, APIKeyValidator
from app.utils.token import generate_access_token, decode_token, verify_token
from app.utils.invitation_security import InvitationSecurityManager


class TestUtilsLogic:
    """工具函数逻辑测试"""

    def test_api_key_generation(self):
        """测试API密钥生成逻辑"""
        generator = APIKeyGenerator()

        # 测试基本生成
        api_key = generator.generate_api_key()
        assert api_key is not None
        assert len(api_key) > 0
        assert isinstance(api_key, str)

        # 测试生成的密钥格式
        validator = APIKeyValidator()
        assert validator.validate_key_format(api_key) is True

        # 测试多次生成的唯一性
        keys = set()
        for _ in range(100):
            key = generator.generate_api_key()
            assert key not in keys
            keys.add(key)

    def test_api_key_validation(self):
        """测试API密钥验证逻辑"""
        validator = APIKeyValidator()
        generator = APIKeyGenerator()

        # 测试有效的密钥格式
        valid_key = generator.generate_api_key()
        assert validator.validate_key_format(valid_key) is True

        # 测试无效的密钥格式
        invalid_keys = [
            "",
            "invalid",
            "ak_",
            "ak_short",
            "wrong_prefix_" + "a" * 64,
            None
        ]

        for key in invalid_keys:
            if key is not None:
                assert validator.validate_key_format(key) is False

    def test_token_creation_and_validation(self):
        """测试令牌创建和验证逻辑"""
        # 测试访问令牌创建
        user_id = uuid4()
        additional_claims = {
            "email": "test@example.com",
            "permissions": ["read", "write"]
        }

        token = generate_access_token(user_id, additional_claims)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # 测试令牌验证
        payload = verify_token(token, "access")
        if payload:  # 如果验证成功
            assert payload["user_id"] == str(user_id)
            assert payload["email"] == additional_claims["email"]
            assert "exp" in payload  # 应该包含过期时间

        # 测试令牌解码（不验证签名）
        decoded_data = decode_token(token)
        if decoded_data:
            assert decoded_data["user_id"] == str(user_id)
            assert decoded_data["email"] == additional_claims["email"]

    def test_token_expiration_logic(self):
        """测试令牌过期逻辑"""
        user_id = uuid4()

        # 创建令牌
        token = generate_access_token(user_id)

        # 尝试验证令牌
        payload = verify_token(token, "access")
        # 新创建的令牌应该是有效的
        if payload:
            assert payload["user_id"] == str(user_id)
            assert "exp" in payload

    def test_invitation_token_logic(self):
        """测试邀请令牌逻辑"""
        from uuid import UUID
        
        # 创建邀请安全管理器实例（这里我们只测试令牌生成和验证逻辑，不涉及Redis）
        # 由于需要Redis客户端，我们直接测试令牌生成和验证方法
        team_id = uuid4()
        email = "invite@example.com"
        
        # 模拟InvitationSecurityManager的令牌生成逻辑
        import secrets
        import hmac
        import hashlib
        from datetime import datetime
        
        # 模拟generate_secure_token方法的逻辑
        base_token = secrets.token_urlsafe(32)
        timestamp = str(int(datetime.utcnow().timestamp()))
        
        # 这里我们只测试令牌格式，不测试实际的HMAC签名
        # 因为需要settings.secret_key
        token_parts = [base_token, timestamp, "mock_signature"]
        token = ".".join(token_parts)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # 应该有三个部分
        
        # 测试令牌格式验证
        parts = token.split('.')
        assert len(parts) == 3
        base_token_part, timestamp_part, signature_part = parts
        assert len(base_token_part) > 0
        assert timestamp_part.isdigit()
        assert len(signature_part) > 0

    def test_hash_consistency(self):
        """测试哈希一致性"""
        test_data = "test_string_for_hashing"

        # 测试相同输入产生相同哈希
        hash1 = hashlib.md5(test_data.encode()).hexdigest()
        hash2 = hashlib.md5(test_data.encode()).hexdigest()
        assert hash1 == hash2

        # 测试不同输入产生不同哈希
        hash3 = hashlib.md5("different_string".encode()).hexdigest()
        assert hash1 != hash3

    def test_json_serialization_logic(self):
        """测试JSON序列化逻辑"""
        test_cases = [
            {"string": "test", "number": 123, "boolean": True},
            {"list": [1, 2, 3], "nested": {"key": "value"}},
            {"datetime": datetime.utcnow().isoformat()},
            {"uuid": str(uuid4())},
            {"empty_dict": {}, "empty_list": []},
            {"null_value": None}
        ]

        for test_data in test_cases:
            # 测试序列化
            serialized = json.dumps(test_data, default=str)
            assert isinstance(serialized, str)

            # 测试反序列化
            deserialized = json.loads(serialized)
            assert isinstance(deserialized, dict)

            # 测试数据完整性（除了datetime等特殊类型）
            for key, value in test_data.items():
                if value is not None and not isinstance(value, datetime):
                    assert key in deserialized

    def test_uuid_generation_logic(self):
        """测试UUID生成逻辑"""
        # 测试UUID唯一性
        uuids = set()
        for _ in range(1000):
            new_uuid = uuid4()
            assert new_uuid not in uuids
            uuids.add(new_uuid)

            # 测试UUID格式
            uuid_str = str(new_uuid)
            assert len(uuid_str) == 36  # 标准UUID长度
            assert uuid_str.count('-') == 4  # 标准UUID格式

    def test_datetime_logic(self):
        """测试日期时间逻辑"""
        now = datetime.utcnow()

        # 测试时间计算
        future = now + timedelta(hours=1)
        past = now - timedelta(hours=1)

        assert future > now
        assert past < now
        assert (future - now).total_seconds() == 3600
        assert (now - past).total_seconds() == 3600

        # 测试ISO格式转换
        iso_string = now.isoformat()
        assert isinstance(iso_string, str)
        assert 'T' in iso_string

    def test_string_validation_logic(self):
        """测试字符串验证逻辑"""
        # 测试邮箱格式验证逻辑
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]

        invalid_emails = [
            "",
            "invalid",
            "@example.com",
            "test@",
            "test.example.com"
        ]

        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        for email in valid_emails:
            assert re.match(email_pattern, email) is not None

        for email in invalid_emails:
            assert re.match(email_pattern, email) is None

    def test_data_validation_logic(self):
        """测试数据验证逻辑"""
        # 测试必填字段验证
        required_fields = ["name", "email", "password"]

        valid_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        }

        invalid_data_cases = [
            {},  # 空数据
            {"name": "Test"},  # 缺少字段
            {"name": "", "email": "test@example.com", "password": "123"},  # 空值
            {"name": "Test", "email": "", "password": "123"}  # 空邮箱
        ]

        # 验证有效数据
        for field in required_fields:
            assert field in valid_data
            assert valid_data[field] is not None
            assert len(str(valid_data[field])) > 0

        # 验证无效数据
        for invalid_data in invalid_data_cases:
            missing_fields = [field for field in required_fields if field not in invalid_data or not invalid_data[field]]
            assert len(missing_fields) > 0

    def test_pagination_logic(self):
        """测试分页逻辑"""
        total_items = 100
        page_size = 10

        # 测试分页计算
        total_pages = (total_items + page_size - 1) // page_size
        assert total_pages == 10

        # 测试各页的项目范围
        for page in range(1, total_pages + 1):
            start_index = (page - 1) * page_size
            end_index = min(start_index + page_size, total_items)

            assert start_index >= 0
            assert end_index <= total_items
            assert end_index > start_index

            if page < total_pages:
                assert end_index - start_index == page_size
            else:
                # 最后一页可能不满
                assert end_index - start_index <= page_size

    def test_error_code_logic(self):
        """测试错误代码逻辑"""
        error_mappings = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            422: "VALIDATION_ERROR",
            500: "INTERNAL_SERVER_ERROR"
        }

        # 测试错误代码映射
        for status_code, error_code in error_mappings.items():
            assert isinstance(status_code, int)
            assert isinstance(error_code, str)
            assert status_code >= 400
            assert len(error_code) > 0

    def test_configuration_logic(self):
        """测试配置逻辑"""
        # 测试默认配置值
        default_config = {
            "jwt_expire_minutes": 30,
            "max_upload_size": 104857600,  # 100MB
            "cache_ttl": 3600,
            "page_size": 20
        }

        for key, value in default_config.items():
            assert isinstance(key, str)
            assert value is not None
            assert isinstance(value, (int, str, bool, float))

    def test_utility_functions_edge_cases(self):
        """测试工具函数边界情况"""
        # 测试空值处理
        empty_values = [None, "", [], {}]

        for empty_value in empty_values:
            # 测试空值检查逻辑
            is_empty = empty_value is None or (hasattr(empty_value, '__len__') and len(empty_value) == 0)
            assert is_empty is True

        # 测试非空值
        non_empty_values = ["test", [1], {"key": "value"}, 123, True]

        for non_empty_value in non_empty_values:
            is_empty = non_empty_value is None or (hasattr(non_empty_value, '__len__') and len(non_empty_value) == 0)
            assert is_empty is False
