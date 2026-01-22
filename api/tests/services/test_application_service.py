"""
应用服务层测试

来自: test_applications.py

测试内容:
- 应用CRUD操作
- API密钥管理
- 应用发布
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth.user import UserEntity
from app.models.tenant.organization import Organization
from app.models.workflow.workflow import WorkflowModel
from app.schemas.application import (
    APIKeyCreate,
    ApplicationCreate,
    ApplicationQuery,
    ApplicationUpdate,
)
from app.services.application_service import ApplicationService


class TestApplicationService:
    """应用服务测试"""

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
    async def test_organization(self, test_session: AsyncSession, test_user: UserEntity):
        """创建测试组织"""
        org = Organization(
            id=uuid4(),
            name='Test Org',
            created_by=test_user.id,
        )
        test_session.add(org)
        await test_session.commit()
        await test_session.refresh(org)
        return org

    @pytest.fixture
    async def test_workflow(
        self, test_session: AsyncSession, test_user: UserEntity, test_organization: Organization
    ):
        """创建测试工作流"""
        workflow = WorkflowModel(
            id=uuid4(),
            name='Test Workflow',
            description='Test workflow for application',
            created_by=test_user.id,
            workspace_id=uuid4(),
        )
        test_session.add(workflow)
        await test_session.commit()
        await test_session.refresh(workflow)
        return workflow

    @pytest.fixture
    def application_service(self, test_session: AsyncSession):
        """创建应用服务实例"""
        return ApplicationService(test_session)

    async def test_application_workflow_association(
        self,
        application_service: ApplicationService,
        test_workflow: WorkflowModel,
        test_user: UserEntity,
    ):
        """测试应用与工作流关联"""
        app_data = ApplicationCreate(
            name='Test App', description='Test application', workflow_id=test_workflow.id
        )

        app = await application_service.create_application(app_data, test_user.id)

        assert app is not None
        assert app.workflow_id == test_workflow.id
        assert app.name == 'Test App'

    async def test_api_endpoint_generation(
        self,
        application_service: ApplicationService,
        test_workflow: WorkflowModel,
        test_user: UserEntity,
    ):
        """测试API端点生成"""
        app_data = ApplicationCreate(
            name='Test App', description='Test application', workflow_id=test_workflow.id
        )

        app = await application_service.create_application(app_data, test_user.id)
        published_app = await application_service.publish_application(app.id, True, test_user.id)

        assert published_app.is_published is True
        assert published_app.api_endpoint is not None

    async def test_api_key_validation(
        self,
        application_service: ApplicationService,
        test_workflow: WorkflowModel,
        test_user: UserEntity,
    ):
        """测试API密钥验证"""
        app_data = ApplicationCreate(
            name='Test App', description='Test application', workflow_id=test_workflow.id
        )

        app = await application_service.create_application(app_data, test_user.id)

        api_key_data = APIKeyCreate(name='Test Key', expires_in_days=30)
        api_key_result = await application_service.create_api_key(
            app.id, api_key_data, test_user.id
        )

        assert api_key_result is not None
        assert 'api_key' in api_key_result
        assert len(api_key_result['api_key']) > 20

        api_key_obj = await application_service.verify_api_key(api_key_result['api_key'])
        assert api_key_obj is not None

        invalid_api_key = await application_service.verify_api_key('invalid_key')
        assert invalid_api_key is None

    async def test_application_config_immediate_effect(
        self,
        application_service: ApplicationService,
        test_workflow: WorkflowModel,
        test_user: UserEntity,
    ):
        """测试应用配置立即生效"""
        app_data = ApplicationCreate(
            name='Test App', description='Test application', workflow_id=test_workflow.id
        )

        app = await application_service.create_application(app_data, test_user.id)

        update_data = ApplicationUpdate(
            name='Updated App',
            config={'timeout': 30, 'retry': 3},
        )

        updated_app = await application_service.update_application(
            app.id, update_data, test_user.id
        )

        assert updated_app.name == 'Updated App'
        assert updated_app.config == {'timeout': 30, 'retry': 3}

    async def test_application_deletion_endpoint_revocation(
        self,
        application_service: ApplicationService,
        test_workflow: WorkflowModel,
        test_user: UserEntity,
    ):
        """测试应用删除时端点撤销"""
        app_data = ApplicationCreate(
            name='Test App', description='Test application', workflow_id=test_workflow.id
        )

        app = await application_service.create_application(app_data, test_user.id)
        await application_service.publish_application(app.id, True, test_user.id)

        api_key_data = APIKeyCreate(name='Test Key', expires_in_days=30)
        api_key_result = await application_service.create_api_key(
            app.id, api_key_data, test_user.id
        )

        success = await application_service.delete_application(app.id, test_user.id)
        assert success is True

        deleted_app = await application_service.get_application(app.id)
        assert deleted_app is None

        invalid_api_key = await application_service.verify_api_key(api_key_result['api_key'])
        assert invalid_api_key is None

    async def test_application_list_and_pagination(
        self,
        application_service: ApplicationService,
        test_workflow: WorkflowModel,
        test_user: UserEntity,
    ):
        """测试应用列表和分页"""
        for i in range(5):
            app_data = ApplicationCreate(
                name=f'Test App {i}',
                description=f'Test application {i}',
                workflow_id=test_workflow.id,
            )
            await application_service.create_application(app_data, test_user.id)

        query = ApplicationQuery(page=1, page_size=3)
        apps_page1, total = await application_service.list_applications(query, test_user.id)
        assert len(apps_page1) == 3
        assert total == 5

        query = ApplicationQuery(page=2, page_size=3)
        apps_page2, total = await application_service.list_applications(query, test_user.id)
        assert len(apps_page2) == 2

    async def test_api_key_management(
        self,
        application_service: ApplicationService,
        test_workflow: WorkflowModel,
        test_user: UserEntity,
    ):
        """测试API密钥管理"""
        app_data = ApplicationCreate(
            name='Test App', description='Test application', workflow_id=test_workflow.id
        )

        app = await application_service.create_application(app_data, test_user.id)

        api_key_data1 = APIKeyCreate(name='Test Key 1', expires_in_days=30)
        api_key_result1 = await application_service.create_api_key(
            app.id, api_key_data1, test_user.id
        )

        api_key_data2 = APIKeyCreate(name='Test Key 2', expires_in_days=60)
        api_key_result2 = await application_service.create_api_key(
            app.id, api_key_data2, test_user.id
        )

        assert api_key_result2['api_key'] != api_key_result1['api_key']

        api_keys = await application_service.list_api_keys(app.id)
        assert len(api_keys) == 2

        success = await application_service.revoke_api_key(
            app.id, api_key_result1['id'], test_user.id
        )
        assert success is True

        revoked_key = await application_service.verify_api_key(api_key_result1['api_key'])
        assert revoked_key is None

        valid_key = await application_service.verify_api_key(api_key_result2['api_key'])
        assert valid_key is not None
