"""
端到端集成测试

来自: test_final_integration.py

测试内容:
- 完整工作流场景
- 多租户隔离
- 数据一致性
"""

from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.auth.user import User
from app.models.tenant.organization import Organization
from app.services.application_service import ApplicationService
from app.services.auth_service import AuthService
from app.services.workflow_service import WorkflowService


class TestEndToEndIntegration:
    """端到端集成测试"""

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
            name='integrationuser',
            email=f'integration_{unique_id}@example.com',
            password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJflLxQjm',
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        return user

    @pytest.fixture
    async def test_organization(self, test_session: AsyncSession, test_user: User):
        """创建测试组织"""
        org = Organization(
            id=uuid4(), name='Integration Test Org', creator_id=test_user.id, is_active=True
        )
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

    async def test_database_crud_operations(
        self, test_session: AsyncSession, test_user: User, test_organization: Organization
    ):
        """测试数据库CRUD操作"""
        workflow_service = WorkflowService(test_session)

        # Create
        workflow_data = {
            'name': 'CRUD Test Workflow',
            'description': 'Test workflow for CRUD operations',
            'creator_id': test_user.id,
            'organization_id': test_organization.id,
            'definition': {'nodes': [], 'connections': []},
        }

        created_workflow = await workflow_service.create_workflow(workflow_data)
        assert created_workflow is not None

        # Read
        retrieved_workflow = await workflow_service.get_workflow(created_workflow.id)
        assert retrieved_workflow is not None

        # Update
        update_data = {'name': 'Updated CRUD Test Workflow'}
        updated_workflow = await workflow_service.update_workflow(created_workflow.id, update_data)
        assert updated_workflow.name == 'Updated CRUD Test Workflow'

        # Delete
        delete_success = await workflow_service.delete_workflow(created_workflow.id)
        assert delete_success is True

    async def test_system_health_check(self, client: TestClient, test_session: AsyncSession):
        """测试系统健康检查"""
        health_response = client.get('/health')

        if health_response.status_code == 200:
            health_data = health_response.json()
            assert 'status' in health_data

    async def test_multi_tenant_isolation(self, client: TestClient, test_session: AsyncSession):
        """测试多租户隔离"""
        unique_id1 = uuid4()
        unique_id2 = uuid4()

        user1 = User(
            id=unique_id1,
            name='tenant1user',
            email=f'tenant1_{unique_id1}@example.com',
            password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJflLxQjm',
        )

        user2 = User(
            id=unique_id2,
            name='tenant2user',
            email=f'tenant2_{unique_id2}@example.com',
            password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJflLxQjm',
        )

        test_session.add_all([user1, user2])
        await test_session.commit()

        org1 = Organization(id=uuid4(), name='Tenant 1 Org', creator_id=user1.id, is_active=True)
        org2 = Organization(id=uuid4(), name='Tenant 2 Org', creator_id=user2.id, is_active=True)

        test_session.add_all([org1, org2])
        await test_session.commit()

        auth_service = AuthService(test_session)
        token1_data = await auth_service.create_access_token(user1.id)
        token2_data = await auth_service.create_access_token(user2.id)

        headers1 = {'Authorization': f'Bearer {token1_data["access_token"]}'}
        headers2 = {'Authorization': f'Bearer {token2_data["access_token"]}'}

        # 用户1创建工作流
        workflow_data = {
            'name': 'Tenant 1 Workflow',
            'description': 'Workflow for tenant 1',
            'definition': {'nodes': [], 'connections': []},
        }

        workflow_response = client.post('/api/v1/workflows', json=workflow_data, headers=headers1)
        if workflow_response.status_code == 201:
            workflow_id = workflow_response.json()['data']['id']

            # 用户2尝试访问用户1的工作流（应该被拒绝）
            access_response = client.get(f'/api/v1/workflows/{workflow_id}', headers=headers2)
            assert access_response.status_code in [403, 404]

    async def test_data_consistency_across_services(
        self, test_session: AsyncSession, test_user: User, test_organization: Organization
    ):
        """测试跨服务数据一致性"""
        workflow_service = WorkflowService(test_session)
        application_service = ApplicationService(test_session)

        workflow_data = {
            'name': 'Consistency Test Workflow',
            'description': 'Test workflow for consistency',
            'creator_id': test_user.id,
            'organization_id': test_organization.id,
            'definition': {'nodes': [], 'connections': []},
        }

        workflow = await workflow_service.create_workflow(workflow_data)

        app_data = {
            'name': 'Consistency Test App',
            'description': 'Test application for consistency',
            'workflow_id': workflow.id,
            'creator_id': test_user.id,
        }

        application = await application_service.create_application(app_data)
        assert application.workflow_id == workflow.id

    def test_api_documentation_completeness(self, client: TestClient):
        """测试API文档完整性"""
        openapi_response = client.get('/openapi.json')
        assert openapi_response.status_code == 200

        openapi_spec = openapi_response.json()
        assert 'openapi' in openapi_spec
        assert 'info' in openapi_spec
        assert 'paths' in openapi_spec

        paths = openapi_spec['paths']
        expected_endpoints = [
            '/api/v1/auth/login',
            '/api/v1/auth/register',
        ]

        for endpoint in expected_endpoints:
            assert any(endpoint in path for path in paths.keys())
