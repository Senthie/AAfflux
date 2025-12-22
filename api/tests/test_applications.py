"""
测试任务17 - 应用管理模块
只对数据库进行CRUD操作，不进行迁移
"""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.application_service import ApplicationService
from app.schemas.application import ApplicationCreate, ApplicationUpdate, APIKeyCreate
from app.utils.api_key import APIKeyManager
from app.models.workflow.workflow import Workflow
from app.models.auth.user import User
from app.models.tenant.organization import Organization


class TestApplications:
    """应用管理模块测试"""

    @pytest.fixture
    async def test_user(self, test_session: AsyncSession):
        """创建测试用户"""
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
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
            name="Test Org",
            creator_id=test_user.id,
            is_active=True
        )
        test_session.add(org)
        await test_session.commit()
        await test_session.refresh(org)
        return org

    @pytest.fixture
    async def test_workflow(self, test_session: AsyncSession, test_user: User, test_organization: Organization):
        """创建测试工作流"""
        workflow = Workflow(
            id=uuid4(),
            name="Test Workflow",
            description="Test workflow for application",
            creator_id=test_user.id,
            organization_id=test_organization.id,
            definition={"nodes": [], "connections": []},
            is_active=True
        )
        test_session.add(workflow)
        await test_session.commit()
        await test_session.refresh(workflow)
        return workflow

    @pytest.fixture
    def application_service(self, test_session: AsyncSession):
        """创建应用服务实例"""
        return ApplicationService(test_session)

    async def test_application_workflow_association(self, application_service: ApplicationService, test_workflow: Workflow, test_user: User):
        """测试应用与工作流关联"""
        app_data = ApplicationCreate(
            name="Test App",
            description="Test application",
            workflow_id=test_workflow.id
        )

        app = await application_service.create_application(app_data, test_user.id)

        assert app is not None
        assert app.workflow_id == test_workflow.id
        assert app.name == "Test App"
        assert app.created_by == test_user.id

    async def test_api_endpoint_generation(self, application_service: ApplicationService, test_workflow: Workflow, test_user: User):
        """测试API端点生成"""
        app_data = ApplicationCreate(
            name="Test App",
            description="Test application",
            workflow_id=test_workflow.id
        )

        app = await application_service.create_application(app_data, test_user.id)

        # 发布应用生成API端点
        published_app = await application_service.publish_application(app.id, True, test_user.id)

        assert published_app.is_published is True
        assert published_app.api_endpoint is not None
        assert f"/runtime/apps/{app.id}" in published_app.api_endpoint

    async def test_api_key_validation(self, application_service: ApplicationService, test_workflow: Workflow, test_user: User):
        """测试API密钥验证"""
        app_data = ApplicationCreate(
            name="Test App",
            description="Test application",
            workflow_id=test_workflow.id
        )

        app = await application_service.create_application(app_data, test_user.id)

        # 生成API密钥
        api_key_data = APIKeyCreate(name="Test Key", expires_in_days=30)
        api_key_result = await application_service.create_api_key(app.id, api_key_data, test_user.id)

        assert api_key_result is not None
        assert "api_key" in api_key_result
        assert len(api_key_result["api_key"]) > 20  # API密钥应该足够长

        # 验证API密钥
        api_key_obj = await application_service.verify_api_key(api_key_result["api_key"])
        assert api_key_obj is not None

        # 验证无效密钥
        invalid_api_key = await application_service.verify_api_key("invalid_key")
        assert invalid_api_key is None

    async def test_application_config_immediate_effect(self, application_service: ApplicationService, test_workflow: Workflow, test_user: User):
        """测试应用配置立即生效"""
        app_data = ApplicationCreate(
            name="Test App",
            description="Test application",
            workflow_id=test_workflow.id
        )

        app = await application_service.create_application(app_data, test_user.id)

        # 更新应用配置
        update_data = ApplicationUpdate(
            name="Updated App",
            description="Updated description",
            config={"timeout": 30, "retry": 3}
        )

        updated_app = await application_service.update_application(app.id, update_data, test_user.id)

        # 验证配置立即生效
        assert updated_app.name == "Updated App"
        assert updated_app.description == "Updated description"
        assert updated_app.config == {"timeout": 30, "retry": 3}

        # 从数据库重新获取验证
        retrieved_app = await application_service.get_application(app.id)
        assert retrieved_app.config == {"timeout": 30, "retry": 3}

    async def test_application_deletion_endpoint_revocation(self, application_service: ApplicationService, test_workflow: Workflow, test_user: User):
        """测试应用删除时端点撤销"""
        app_data = ApplicationCreate(
            name="Test App",
            description="Test application",
            workflow_id=test_workflow.id
        )

        app = await application_service.create_application(app_data, test_user.id)

        # 发布应用
        published_app = await application_service.publish_application(app.id, True, test_user.id)
        assert published_app.is_published is True

        # 生成API密钥
        api_key_data = APIKeyCreate(name="Test Key", expires_in_days=30)
        api_key_result = await application_service.create_api_key(app.id, api_key_data, test_user.id)
        assert api_key_result is not None

        # 删除应用
        success = await application_service.delete_application(app.id, test_user.id)
        assert success is True

        # 验证应用已删除
        deleted_app = await application_service.get_application(app.id)
        assert deleted_app is None

        # 验证API密钥失效
        invalid_api_key = await application_service.verify_api_key(api_key_result["api_key"])
        assert invalid_api_key is None

    async def test_application_status_management(self, application_service: ApplicationService, test_workflow: Workflow, test_user: User):
        """测试应用状态管理"""
        app_data = ApplicationCreate(
            name="Test App",
            description="Test application",
            workflow_id=test_workflow.id
        )

        app = await application_service.create_application(app_data, test_user.id)

        # 初始状态应该是未发布
        assert app.is_published is False

        # 发布应用
        published_app = await application_service.publish_application(app.id, True, test_user.id)
        assert published_app.is_published is True

        # 取消发布应用
        unpublished_app = await application_service.publish_application(app.id, False, test_user.id)
        assert unpublished_app.is_published is False

    async def test_application_list_and_pagination(self, application_service: ApplicationService, test_workflow: Workflow, test_user: User):
        """测试应用列表和分页"""
        # 创建多个应用
        for i in range(5):
            app_data = ApplicationCreate(
                name=f"Test App {i}",
                description=f"Test application {i}",
                workflow_id=test_workflow.id
            )
            await application_service.create_application(app_data, test_user.id)

        # 测试分页查询
        from app.schemas.application import ApplicationQuery
        query = ApplicationQuery(page=1, page_size=3)
        apps_page1, total = await application_service.list_applications(query, test_user.id)
        assert len(apps_page1) == 3
        assert total == 5

        query = ApplicationQuery(page=2, page_size=3)
        apps_page2, total = await application_service.list_applications(query, test_user.id)
        assert len(apps_page2) == 2
        assert total == 5

    async def test_api_key_management(self, application_service: ApplicationService, test_workflow: Workflow, test_user: User):
        """测试API密钥管理"""
        app_data = ApplicationCreate(
            name="Test App",
            description="Test application",
            workflow_id=test_workflow.id
        )

        app = await application_service.create_application(app_data, test_user.id)

        # 生成第一个API密钥
        api_key_data1 = APIKeyCreate(name="Test Key 1", expires_in_days=30)
        api_key_result1 = await application_service.create_api_key(app.id, api_key_data1, test_user.id)
        assert api_key_result1 is not None

        # 生成第二个API密钥
        api_key_data2 = APIKeyCreate(name="Test Key 2", expires_in_days=60)
        api_key_result2 = await application_service.create_api_key(app.id, api_key_data2, test_user.id)
        assert api_key_result2 is not None
        assert api_key_result2["api_key"] != api_key_result1["api_key"]

        # 列出API密钥
        api_keys = await application_service.list_api_keys(app.id)
        assert len(api_keys) == 2

        # 撤销第一个API密钥
        success = await application_service.revoke_api_key(app.id, api_key_result1["id"], test_user.id)
        assert success is True

        # 验证撤销后的密钥无效
        revoked_key = await application_service.verify_api_key(api_key_result1["api_key"])
        assert revoked_key is None

        # 验证第二个密钥仍然有效
        valid_key = await application_service.verify_api_key(api_key_result2["api_key"])
        assert valid_key is not None