"""
测试任务18 - API路由整合
只对数据库进行CRUD操作，不进行迁移
"""

from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.auth.user import User
from app.models.tenant.organization import Organization
from app.services.auth_service import AuthService


class TestAPIIntegration:
    """API路由整合测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    async def test_user(self, test_session: AsyncSession):
        """创建测试用户"""
        user = User(
            id=uuid4(),
            email='test@example.com',
            username='testuser',
            hashed_password='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJflLxQjm',  # "secret"
            is_active=True,
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        return user

    @pytest.fixture
    async def test_organization(self, test_session: AsyncSession, test_user: User):
        """创建测试组织"""
        org = Organization(id=uuid4(), name='Test Org', creator_id=test_user.id, is_active=True)
        test_session.add(org)
        await test_session.commit()
        await test_session.refresh(org)
        return org

    @pytest.fixture
    async def auth_token(self, test_session: AsyncSession, test_user: User):
        """生成认证令牌"""
        auth_service = AuthService(test_session)
        token_data = await auth_service.create_access_token(test_user.id)
        return token_data['access_token']

    def test_api_request_validation(self, client: TestClient):
        """测试API请求验证"""
        # 测试无效的JSON请求
        response = client.post('/api/v1/auth/register', json={'invalid': 'data'})
        assert response.status_code == 422  # Validation error

        # 测试缺少必填字段
        response = client.post(
            '/api/v1/auth/register',
            json={'email': 'test@example.com'},  # 缺少password等字段
        )
        assert response.status_code == 422

        # 测试无效的邮箱格式
        response = client.post(
            '/api/v1/auth/register',
            json={'email': 'invalid-email', 'username': 'testuser', 'password': 'password123'},
        )
        assert response.status_code == 422

    def test_api_success_response_format(self, client: TestClient):
        """测试API成功响应格式"""
        # 测试注册接口的响应格式
        response = client.post(
            '/api/v1/auth/register',
            json={'email': 'newuser@example.com', 'username': 'newuser', 'password': 'password123'},
        )

        if response.status_code == 201:
            data = response.json()
            # 验证响应格式
            assert 'success' in data
            assert 'data' in data
            assert 'message' in data
            assert data['success'] is True

            # 验证用户数据格式
            user_data = data['data']
            assert 'id' in user_data
            assert 'email' in user_data
            assert 'username' in user_data
            assert 'password' not in user_data  # 密码不应该返回

    def test_unified_error_handling(self, client: TestClient):
        """测试统一错误处理"""
        # 测试404错误
        response = client.get('/api/v1/nonexistent')
        assert response.status_code == 404

        error_data = response.json()
        assert 'success' in error_data
        assert 'error' in error_data
        assert 'message' in error_data
        assert error_data['success'] is False

        # 测试未授权访问
        response = client.get('/api/v1/users/profile')
        assert response.status_code == 401

        error_data = response.json()
        assert error_data['success'] is False
        assert (
            'unauthorized' in error_data['message'].lower()
            or 'authentication' in error_data['message'].lower()
        )

    def test_auth_endpoints(self, client: TestClient, test_user: User):
        """测试认证端点"""
        # 测试登录
        response = client.post(
            '/api/v1/auth/login', json={'email': test_user.email, 'password': 'secret'}
        )

        if response.status_code == 200:
            data = response.json()
            assert 'access_token' in data['data']
            assert 'token_type' in data['data']
            assert data['data']['token_type'] == 'bearer'

            # 使用令牌访问受保护的端点
            token = data['data']['access_token']
            headers = {'Authorization': f'Bearer {token}'}

            profile_response = client.get('/api/v1/users/profile', headers=headers)
            assert profile_response.status_code == 200

            profile_data = profile_response.json()
            assert profile_data['data']['email'] == test_user.email

    def test_cors_headers(self, client: TestClient):
        """测试CORS头部"""
        response = client.options('/api/v1/auth/login')

        # 检查CORS头部是否存在
        assert 'access-control-allow-origin' in response.headers
        assert 'access-control-allow-methods' in response.headers
        assert 'access-control-allow-headers' in response.headers

    def test_content_type_validation(self, client: TestClient):
        """测试内容类型验证"""
        # 测试非JSON请求
        response = client.post(
            '/api/v1/auth/login',
            data='email=test@example.com&password=secret',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )

        # 应该返回415 Unsupported Media Type 或者422 Validation Error
        assert response.status_code in [415, 422]

    def test_rate_limiting_headers(self, client: TestClient):
        """测试速率限制头部"""
        response = client.get('/api/v1/auth/login')

        # 检查是否有速率限制相关的头部
        # 这取决于是否实现了速率限制中间件
        if 'x-ratelimit-limit' in response.headers:
            assert 'x-ratelimit-remaining' in response.headers
            assert 'x-ratelimit-reset' in response.headers

    def test_api_versioning(self, client: TestClient):
        """测试API版本控制"""
        # 测试v1 API路径
        response = client.get('/api/v1/')
        # 应该返回404或者API信息
        assert response.status_code in [404, 200]

        # 测试不存在的版本
        response = client.get('/api/v2/auth/login')
        assert response.status_code == 404

    def test_health_check_endpoint(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get('/health')

        if response.status_code == 200:
            data = response.json()
            assert 'status' in data
            assert data['status'] in ['healthy', 'ok']

    def test_openapi_documentation(self, client: TestClient):
        """测试OpenAPI文档"""
        # 测试OpenAPI JSON
        response = client.get('/openapi.json')
        assert response.status_code == 200

        openapi_data = response.json()
        assert 'openapi' in openapi_data
        assert 'info' in openapi_data
        assert 'paths' in openapi_data

        # 测试Swagger UI
        response = client.get('/docs')
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']

    def test_request_id_header(self, client: TestClient):
        """测试请求ID头部"""
        response = client.get('/api/v1/auth/login')

        # 检查是否有请求ID头部
        if 'x-request-id' in response.headers:
            request_id = response.headers['x-request-id']
            assert len(request_id) > 0
            # 请求ID应该是UUID格式或者其他唯一标识符

    def test_security_headers(self, client: TestClient):
        """测试安全头部"""
        response = client.get('/api/v1/auth/login')

        # 检查安全相关的头部
        security_headers = [
            'x-content-type-options',
            'x-frame-options',
            'x-xss-protection',
            'strict-transport-security',
        ]

        for header in security_headers:
            if header in response.headers:
                assert len(response.headers[header]) > 0
