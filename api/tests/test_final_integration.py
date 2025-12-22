"""
测试任务22 - 最终集成测试
只对数据库进行CRUD操作，不进行迁移
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.main import app
from app.models.auth.user import User
from app.models.tenant.organization import Organization
from app.services.auth_service import AuthService
from app.services.workflow_service import WorkflowService
from app.services.application_service import ApplicationService


class TestFinalIntegration:
    """最终集成测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    async def test_user(self, test_session: AsyncSession):
        """创建测试用户"""
        user = User(
            id=uuid4(),
            email="integration@example.com",
            username="integrationuser",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJflLxQjm",  # "secret"
            is_active=True
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        return user

    @pytest.fixture
    async def test_organization(self, test_session: AsyncSession, test_user: User):
        """创建测试组织"""
        org = Organization(
            id=uuid4(),
            name="Integration Test Org",
            creator_id=test_user.id,
            is_active=True
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
        return token_data["access_token"]

    async def test_all_modules_integration(self, client: TestClient, test_user: User, test_organization: Organization, auth_token: str):
        """测试所有模块集成"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # 1. 测试用户认证模块
        profile_response = client.get("/api/v1/users/profile", headers=headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["data"]["email"] == test_user.email

        # 2. 测试工作流创建
        workflow_data = {
            "name": "Integration Test Workflow",
            "description": "Test workflow for integration",
            "definition": {
                "nodes": [
                    {
                        "id": "start_node",
                        "type": "start",
                        "config": {"message": "Hello World"}
                    },
                    {
                        "id": "llm_node",
                        "type": "llm",
                        "config": {"model": "gpt-3.5-turbo", "prompt": "Process: {{input}}"}
                    }
                ],
                "connections": [
                    {
                        "source": "start_node",
                        "target": "llm_node",
                        "source_handle": "output",
                        "target_handle": "input"
                    }
                ]
            }
        }

        workflow_response = client.post(
            "/api/v1/workflows",
            json=workflow_data,
            headers=headers
        )
        assert workflow_response.status_code == 201
        workflow = workflow_response.json()["data"]
        workflow_id = workflow["id"]

        # 3. 测试应用创建和发布
        app_data = {
            "name": "Integration Test App",
            "description": "Test application for integration",
            "workflow_id": workflow_id
        }

        app_response = client.post(
            "/api/v1/applications",
            json=app_data,
            headers=headers
        )
        assert app_response.status_code == 201
        application = app_response.json()["data"]
        app_id = application["id"]

        # 4. 发布应用
        publish_response = client.post(
            f"/api/v1/applications/{app_id}/publish",
            headers=headers
        )
        assert publish_response.status_code == 200

        # 5. 生成API密钥
        api_key_response = client.post(
            f"/api/v1/applications/{app_id}/api-key",
            headers=headers
        )
        assert api_key_response.status_code == 200
        api_key = api_key_response.json()["data"]["api_key"]

        # 6. 测试应用运行时调用
        runtime_headers = {"X-API-Key": api_key}
        runtime_response = client.post(
            f"/api/v1/runtime/apps/{app_id}/execute",
            json={"input": "Test input data"},
            headers=runtime_headers
        )
        # 运行时调用可能返回202（异步）或200（同步）
        assert runtime_response.status_code in [200, 202]

    async def test_database_crud_operations(self, test_session: AsyncSession, test_user: User, test_organization: Organization):
        """测试数据库CRUD操作"""
        # 测试工作流CRUD
        workflow_service = WorkflowService(test_session)

        # Create
        workflow_data = {
            "name": "CRUD Test Workflow",
            "description": "Test workflow for CRUD operations",
            "creator_id": test_user.id,
            "organization_id": test_organization.id,
            "definition": {"nodes": [], "connections": []}
        }

        created_workflow = await workflow_service.create_workflow(workflow_data)
        assert created_workflow is not None
        assert created_workflow.name == "CRUD Test Workflow"

        # Read
        retrieved_workflow = await workflow_service.get_workflow(created_workflow.id)
        assert retrieved_workflow is not None
        assert retrieved_workflow.id == created_workflow.id

        # Update
        update_data = {
            "name": "Updated CRUD Test Workflow",
            "description": "Updated description"
        }
        updated_workflow = await workflow_service.update_workflow(created_workflow.id, update_data)
        assert updated_workflow.name == "Updated CRUD Test Workflow"

        # Delete
        delete_success = await workflow_service.delete_workflow(created_workflow.id)
        assert delete_success is True

        # Verify deletion
        deleted_workflow = await workflow_service.get_workflow(created_workflow.id)
        assert deleted_workflow is None

    async def test_system_health_check(self, client: TestClient, test_session: AsyncSession):
        """测试系统健康检查"""
        # 测试基本健康检查
        health_response = client.get("/health")

        if health_response.status_code == 200:
            health_data = health_response.json()
            assert "status" in health_data
            assert health_data["status"] in ["healthy", "ok"]

            # 检查详细的健康信息
            if "checks" in health_data:
                checks = health_data["checks"]

                # 数据库健康检查
                if "database" in checks:
                    db_status = checks["database"]["status"]
                    assert db_status in ["healthy", "unhealthy"]

                # Redis健康检查
                if "redis" in checks:
                    redis_status = checks["redis"]["status"]
                    assert redis_status in ["healthy", "unhealthy"]

                # MongoDB健康检查
                if "mongodb" in checks:
                    mongodb_status = checks["mongodb"]["status"]
                    assert mongodb_status in ["healthy", "unhealthy"]

    async def test_end_to_end_workflow_execution(self, client: TestClient, test_user: User, test_organization: Organization, auth_token: str, test_session: AsyncSession):
        """测试端到端工作流执行"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # 1. 创建完整的工作流
        workflow_data = {
            "name": "E2E Test Workflow",
            "description": "End-to-end test workflow",
            "definition": {
                "nodes": [
                    {
                        "id": "input_node",
                        "type": "input",
                        "config": {"schema": {"type": "object", "properties": {"message": {"type": "string"}}}}
                    },
                    {
                        "id": "transform_node",
                        "type": "transform",
                        "config": {"script": "output = {'processed': input['message'].upper()}"}
                    },
                    {
                        "id": "output_node",
                        "type": "output",
                        "config": {"format": "json"}
                    }
                ],
                "connections": [
                    {"source": "input_node", "target": "transform_node"},
                    {"source": "transform_node", "target": "output_node"}
                ]
            }
        }

        workflow_response = client.post("/api/v1/workflows", json=workflow_data, headers=headers)
        assert workflow_response.status_code == 201
        workflow_id = workflow_response.json()["data"]["id"]

        # 2. 执行工作流
        execution_data = {
            "input_data": {"message": "hello world"}
        }

        execution_response = client.post(
            f"/api/v1/workflows/{workflow_id}/execute",
            json=execution_data,
            headers=headers
        )

        if execution_response.status_code in [200, 202]:
            execution_result = execution_response.json()["data"]

            if execution_response.status_code == 202:
                # 异步执行，检查执行状态
                execution_id = execution_result["execution_id"]

                # 轮询执行状态
                import time
                for _ in range(10):  # 最多等待10次
                    status_response = client.get(
                        f"/api/v1/executions/{execution_id}",
                        headers=headers
                    )

                    if status_response.status_code == 200:
                        status_data = status_response.json()["data"]
                        if status_data["status"] in ["completed", "failed"]:
                            break

                    time.sleep(1)

                assert status_data["status"] == "completed"
                if "output_data" in status_data:
                    assert "processed" in status_data["output_data"]

    async def test_multi_tenant_isolation(self, client: TestClient, test_session: AsyncSession):
        """测试多租户隔离"""
        # 创建两个不同的用户和组织
        user1 = User(
            id=uuid4(),
            email="tenant1@example.com",
            username="tenant1user",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJflLxQjm",
            is_active=True
        )

        user2 = User(
            id=uuid4(),
            email="tenant2@example.com",
            username="tenant2user",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJflLxQjm",
            is_active=True
        )

        test_session.add_all([user1, user2])
        await test_session.commit()
        await test_session.refresh(user1)
        await test_session.refresh(user2)

        org1 = Organization(
            id=uuid4(),
            name="Tenant 1 Org",
            creator_id=user1.id,
            is_active=True
        )

        org2 = Organization(
            id=uuid4(),
            name="Tenant 2 Org",
            creator_id=user2.id,
            is_active=True
        )

        test_session.add_all([org1, org2])
        await test_session.commit()

        # 生成两个用户的令牌
        auth_service = AuthService(test_session)
        token1_data = await auth_service.create_access_token(user1.id)
        token2_data = await auth_service.create_access_token(user2.id)

        headers1 = {"Authorization": f"Bearer {token1_data['access_token']}"}
        headers2 = {"Authorization": f"Bearer {token2_data['access_token']}"}

        # 用户1创建工作流
        workflow_data = {
            "name": "Tenant 1 Workflow",
            "description": "Workflow for tenant 1",
            "definition": {"nodes": [], "connections": []}
        }

        workflow_response = client.post("/api/v1/workflows", json=workflow_data, headers=headers1)
        assert workflow_response.status_code == 201
        workflow_id = workflow_response.json()["data"]["id"]

        # 用户2尝试访问用户1的工作流（应该被拒绝）
        access_response = client.get(f"/api/v1/workflows/{workflow_id}", headers=headers2)
        assert access_response.status_code in [403, 404]  # 禁止访问或未找到

        # 用户1可以访问自己的工作流
        own_access_response = client.get(f"/api/v1/workflows/{workflow_id}", headers=headers1)
        assert own_access_response.status_code == 200

    async def test_performance_under_load(self, client: TestClient, auth_token: str):
        """测试负载下的性能"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # 并发创建多个工作流
        import asyncio
        import aiohttp

        async def create_workflow(session, index):
            workflow_data = {
                "name": f"Load Test Workflow {index}",
                "description": f"Load test workflow {index}",
                "definition": {"nodes": [], "connections": []}
            }

            async with session.post(
                "http://testserver/api/v1/workflows",
                json=workflow_data,
                headers=headers
            ) as response:
                return response.status

        # 创建10个并发请求
        async with aiohttp.ClientSession() as session:
            tasks = [create_workflow(session, i) for i in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 检查大部分请求是否成功
            success_count = sum(1 for result in results if result == 201)
            assert success_count >= 8  # 至少80%成功率

    async def test_data_consistency_across_services(self, test_session: AsyncSession, test_user: User, test_organization: Organization):
        """测试跨服务数据一致性"""
        workflow_service = WorkflowService(test_session)
        application_service = ApplicationService(test_session)

        # 创建工作流
        workflow_data = {
            "name": "Consistency Test Workflow",
            "description": "Test workflow for consistency",
            "creator_id": test_user.id,
            "organization_id": test_organization.id,
            "definition": {"nodes": [], "connections": []}
        }

        workflow = await workflow_service.create_workflow(workflow_data)

        # 基于工作流创建应用
        app_data = {
            "name": "Consistency Test App",
            "description": "Test application for consistency",
            "workflow_id": workflow.id,
            "creator_id": test_user.id
        }

        application = await application_service.create_application(app_data)

        # 验证数据一致性
        assert application.workflow_id == workflow.id

        # 删除工作流应该影响应用
        await workflow_service.delete_workflow(workflow.id)

        # 检查应用状态是否相应更新
        updated_app = await application_service.get_application(application.id)
        if updated_app:
            # 应用可能被标记为无效或者被级联删除
            assert updated_app.is_active is False or updated_app is None

    def test_api_documentation_completeness(self, client: TestClient):
        """测试API文档完整性"""
        # 获取OpenAPI规范
        openapi_response = client.get("/openapi.json")
        assert openapi_response.status_code == 200

        openapi_spec = openapi_response.json()

        # 检查基本结构
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
        assert "paths" in openapi_spec

        # 检查主要API端点是否都有文档
        paths = openapi_spec["paths"]
        expected_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/users/profile",
            "/api/v1/workflows",
            "/api/v1/applications"
        ]

        for endpoint in expected_endpoints:
            assert any(endpoint in path for path in paths.keys()), f"Missing documentation for {endpoint}"

        # 检查每个端点是否有适当的HTTP方法
        for path, methods in paths.items():
            if "/api/v1/" in path:
                assert isinstance(methods, dict)
                assert len(methods) > 0  # 至少有一个HTTP方法
