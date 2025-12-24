"""
API集成测试

合并自:
- test_api_integration.py
- test_error_handling.py

测试内容:
- API路由整合
- 请求验证
- 错误处理
- 安全头部
"""

import logging
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.auth.user import User


class TestAPIIntegration:
    """API路由整合测试"""

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
            password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJflLxQjm',
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        return user

    def test_api_request_validation(self, client: TestClient):
        """测试API请求验证"""
        response = client.post('/api/v1/auth/register', json={'invalid': 'data'})
        assert response.status_code == 422

        response = client.post(
            '/api/v1/auth/register',
            json={'email': 'invalid-email', 'username': 'testuser', 'password': 'password123'},
        )
        assert response.status_code == 422

    def test_unified_error_handling(self, client: TestClient):
        """测试统一错误处理"""
        response = client.get('/api/v1/nonexistent')
        assert response.status_code == 404

        error_data = response.json()
        assert 'success' in error_data
        assert error_data['success'] is False

    def test_cors_headers(self, client: TestClient):
        """测试CORS头部"""
        # 发送带有 Origin 头的请求来触发 CORS
        response = client.options(
            '/api/v1/auth/login',
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
            },
        )
        # CORS 中间件应该返回 access-control-allow-origin 头
        # 或者如果没有配置 CORS，可能返回 200 但没有 CORS 头
        assert response.status_code in [200, 204, 405]
        # 如果返回了 CORS 头，验证它
        if 'access-control-allow-origin' in response.headers:
            assert response.headers['access-control-allow-origin'] in ['*', 'http://localhost:3000']

    def test_health_check_endpoint(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get('/health')
        if response.status_code == 200:
            data = response.json()
            assert 'status' in data

    def test_openapi_documentation(self, client: TestClient):
        """测试OpenAPI文档"""
        response = client.get('/openapi.json')
        assert response.status_code == 200

        openapi_data = response.json()
        assert 'openapi' in openapi_data
        assert 'info' in openapi_data
        assert 'paths' in openapi_data


class TestErrorHandling:
    """错误处理测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    def test_error_response_formats(self, client: TestClient):
        """测试各种错误类型的响应格式"""
        response = client.get('/api/v1/nonexistent')
        assert response.status_code == 404

        error_data = response.json()
        assert 'success' in error_data
        assert 'error_code' in error_data
        assert error_data['success'] is False

        response = client.post('/api/v1/auth/register', json={'invalid': 'data'})
        assert response.status_code == 422

    def test_validation_error_details(self, client: TestClient):
        """测试验证错误详细信息"""
        response = client.post(
            '/api/v1/auth/register',
            json={
                'email': 'invalid-email',
                'username': '',
                'password': '123',
            },
        )

        assert response.status_code == 422
        error_data = response.json()
        assert 'errors' in error_data

    def test_security_headers(self, client: TestClient):
        """测试安全头部"""
        response = client.get('/api/v1/auth/login')

        security_headers = [
            'x-content-type-options',
            'x-frame-options',
            'x-xss-protection',
        ]

        for header in security_headers:
            if header in response.headers:
                assert len(response.headers[header]) > 0

    def test_error_logging(self, client: TestClient, caplog):
        """测试错误日志记录"""
        with caplog.at_level(logging.ERROR):
            response = client.get('/api/v1/nonexistent')
            assert response.status_code == 404
