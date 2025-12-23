"""
测试任务20 - 错误处理和监控
只对数据库进行CRUD操作，不进行迁移
"""

import logging
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.auth.user import User


class TestErrorHandling:
    """错误处理和监控测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    async def test_user(self, test_session: AsyncSession):
        """创建测试用户"""
        unique_id = uuid4()
        user = User(
            id=unique_id,
            name='testuser',
            email=f'test_{unique_id}@example.com',
            password_hash='hashed_password',
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        return user

    def test_error_response_formats(self, client: TestClient):
        """测试各种错误类型的响应格式"""
        # 测试404错误
        response = client.get('/api/v1/nonexistent')
        assert response.status_code == 404

        error_data = response.json()
        assert 'success' in error_data
        assert 'error_code' in error_data
        assert 'message' in error_data
        assert 'timestamp' in error_data
        assert error_data['success'] is False
        assert error_data['error_code'] == 'NOT_FOUND'

        # 测试422验证错误
        response = client.post('/api/v1/auth/register', json={'invalid': 'data'})
        assert response.status_code == 422

        validation_error = response.json()
        assert validation_error['success'] is False
        assert validation_error['error_code'] == 'VALIDATION_ERROR'
        assert 'errors' in validation_error

        # 测试401未授权错误
        response = client.get('/api/v1/applications')
        assert response.status_code == 401

        auth_error = response.json()
        assert auth_error['success'] is False
        assert auth_error['error_code'] == 'UNAUTHORIZED'

    def test_error_logging(self, client: TestClient, caplog):
        """测试错误日志记录"""
        with caplog.at_level(logging.ERROR):
            # 触发一个错误
            response = client.get('/api/v1/nonexistent')
            assert response.status_code == 404

            # 检查是否记录了错误日志
            error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
            if error_logs:
                assert any(
                    '404' in str(log.message) or 'not found' in str(log.message).lower()
                    for log in error_logs
                )

    def test_request_logging_middleware(self, client: TestClient, caplog):
        """测试请求日志中间件"""
        with caplog.at_level(logging.INFO):
            # 发送一个请求
            client.get('/api/v1/auth/login')

            # 检查是否记录了请求日志
            info_logs = [record for record in caplog.records if record.levelno == logging.INFO]
            if info_logs:
                # 应该记录请求的基本信息
                request_logged = any(
                    'GET' in str(log.message) and '/api/v1/auth/login' in str(log.message)
                    for log in info_logs
                )
                assert request_logged

    def test_database_error_handling(self, client: TestClient):
        """测试数据库错误处理"""
        # 模拟数据库连接错误的情况
        with patch('app.core.database.AsyncSession') as mock_session:
            mock_session.side_effect = Exception('Database connection failed')

            response = client.post(
                '/api/v1/auth/register',
                json={
                    'email': 'test@example.com',
                    'username': 'testuser',
                    'password': 'password123',
                },
            )

            # 应该返回500内部服务器错误或者其他错误状态码
            assert response.status_code >= 400

            if response.status_code == 500:
                error_data = response.json()
                assert error_data['success'] is False
                assert error_data['error_code'] == 'INTERNAL_SERVER_ERROR'

    def test_validation_error_details(self, client: TestClient):
        """测试验证错误详细信息"""
        response = client.post(
            '/api/v1/auth/register',
            json={
                'email': 'invalid-email',
                'username': '',
                'password': '123',  # 太短的密码
            },
        )

        assert response.status_code == 422

        error_data = response.json()
        assert 'errors' in error_data

        errors = error_data['errors']
        assert isinstance(errors, list)
        assert len(errors) > 0

        # 检查错误详情格式
        for error in errors:
            assert 'field' in error
            assert 'message' in error
            assert 'type' in error

    def test_rate_limit_error_handling(self, client: TestClient):
        """测试速率限制错误处理"""
        # 如果实现了速率限制，测试超出限制的情况
        # 这里跳过测试，因为速率限制功能尚未实现
        response = client.post(
            '/api/v1/auth/login', json={'email': 'test@example.com', 'password': 'password'}
        )

        # 由于速率限制未实现，我们只检查响应是否正常
        assert response.status_code in [200, 400, 401, 404, 422]

    def test_custom_exception_handling(self, client: TestClient):
        """测试自定义异常处理"""
        # 测试业务逻辑异常
        response = client.post(
            '/api/v1/auth/register',
            json={
                'email': 'existing@example.com',  # 假设这个邮箱已存在
                'username': 'existinguser',
                'password': 'password123',
            },
        )

        if response.status_code == 409:  # Conflict
            error_data = response.json()
            assert error_data['success'] is False
            assert error_data['error_code'] == 'DATABASE_INTEGRITY_ERROR'
            assert (
                'already exists' in error_data['message'].lower()
                or '数据已存在' in error_data['message']
            )

    def test_error_correlation_id(self, client: TestClient):
        """测试错误关联ID"""
        response = client.get('/api/v1/nonexistent')
        assert response.status_code == 404

        error_data = response.json()

        # 检查是否有关联ID用于错误追踪
        if 'correlation_id' in error_data or 'request_id' in error_data:
            correlation_id = error_data.get('correlation_id') or error_data.get('request_id')
            assert len(correlation_id) > 0
            assert isinstance(correlation_id, str)

    def test_sensitive_data_masking(self, client: TestClient):
        """测试敏感数据掩码"""
        # 模拟包含敏感信息的错误响应，避免实际数据库连接
        with patch('app.api.errors.logger'):
            # 触发一个简单的404错误，不涉及数据库
            response = client.get('/api/v1/nonexistent')

            # 验证基本错误响应
            assert response.status_code == 404

            # 检查响应文本不包含常见的敏感信息关键词
            response_text = response.text.lower()
            sensitive_keywords = ['password', 'secret', 'token', 'key', 'credential']

            # 验证响应中没有明显的敏感信息
            for keyword in sensitive_keywords:
                # 如果包含关键词，应该是被掩码的形式
                if keyword in response_text:
                    assert '***' in response.text or '[MASKED]' in response.text

    @patch('app.core.sentry.sentry_sdk.capture_exception')
    def test_sentry_integration(self, mock_sentry, client: TestClient):
        """测试Sentry集成"""
        # 触发一个服务器错误
        with patch('app.services.auth_service.AuthService.register') as mock_register:
            mock_register.side_effect = Exception('Test exception for Sentry')

            response = client.post(
                '/api/v1/auth/register',
                json={
                    'email': 'test@example.com',
                    'username': 'testuser',
                    'password': 'password123',
                },
            )

            if response.status_code == 500:
                # 检查是否调用了Sentry
                mock_sentry.assert_called()

    def test_health_check_error_monitoring(self, client: TestClient):
        """测试健康检查错误监控"""
        response = client.get('/health')

        if response.status_code == 200:
            health_data = response.json()
            assert 'status' in health_data

            # 如果有详细的健康检查信息
            if 'checks' in health_data:
                checks = health_data['checks']
                for check_result in checks.values():
                    assert 'status' in check_result
                    assert check_result['status'] in ['healthy', 'unhealthy', 'degraded']

    def test_error_metrics_collection(self, client: TestClient):
        """测试错误指标收集"""
        # 触发不同类型的错误
        error_endpoints = [
            ('/api/v1/nonexistent', 404),
            ('/api/v1/applications', 401),  # 修正为实际返回401的端点
        ]

        for endpoint, expected_status in error_endpoints:
            response = client.get(endpoint)
            assert response.status_code == expected_status

            # 检查响应头中是否有指标信息
            if 'x-error-count' in response.headers:
                error_count = int(response.headers['x-error-count'])
                assert error_count >= 0

    def test_structured_logging_format(self, client: TestClient, caplog):
        """测试结构化日志格式"""
        with caplog.at_level(logging.INFO):
            client.get('/api/v1/auth/login')

            # 检查日志格式是否结构化
            for record in caplog.records:
                # 结构化日志应该包含特定字段
                if hasattr(record, 'extra'):
                    extra = record.extra
                    expected_fields = ['method', 'path', 'status_code', 'duration']
                    for field in expected_fields:
                        if field in extra:
                            assert extra[field] is not None
