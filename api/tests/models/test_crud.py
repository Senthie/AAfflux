"""
模型CRUD测试

合并自:
- test_tasks_1_6_crud.py
- test_infrastructure.py

测试内容:
- 基础设施配置
- 数据模型CRUD
- 认证模型
- 租户管理模型
"""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

from app.core.config import settings
from app.models.application.application import Application
from app.models.audit.audit_log import AuditLog
from app.models.auth.token import RefreshToken
from app.models.auth.user import UserEntity
from app.models.tenant.organization import Organization, Team, Workspace
from app.models.workflow.workflow import Workflow


@pytest.fixture(scope='function')
async def test_db_session():
    """专用测试数据库会话"""
    test_db_url = 'postgresql+asyncpg://postgres:postgres@14.12.0.102:5432/lowcode_test'

    engine = create_async_engine(
        test_db_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()


class TestConfiguration:
    """配置测试"""

    def test_settings_loaded(self):
        """Test that settings are loaded correctly."""
        assert settings.app_name == 'Low-Code Platform Backend'
        assert settings.jwt_algorithm == 'HS256'
        assert settings.database_url is not None

    def test_jwt_secret_key_length(self):
        """Test that JWT secret key meets minimum length requirement."""
        assert len(settings.jwt_secret_key) >= 32


class TestDatabaseConnection:
    """数据库连接测试"""

    @pytest.mark.asyncio
    async def test_database_session(self, test_session):
        """Test that database session can be created."""
        assert test_session is not None
        result = await test_session.execute(text('SELECT 1'))
        assert result is not None


class TestUserCRUD:
    """用户模型CRUD测试"""

    @pytest.mark.asyncio
    async def test_user_crud(self, test_db_session: AsyncSession):
        """Test User model CRUD operations."""
        unique_id = str(uuid4())[:8]
        user = UserEntity(
            name=f'Test User {unique_id}',
            email=f'test{unique_id}@example.com',
            password_hash='hashed_password',
            is_active=True,
        )
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        stmt = select(UserEntity).where(UserEntity.email == f'test{unique_id}@example.com')
        result = await test_db_session.execute(stmt)
        found_user = result.scalar_one_or_none()
        assert found_user is not None

        found_user.name = f'Updated User {unique_id}'
        await test_db_session.commit()
        assert found_user.name == f'Updated User {unique_id}'

        found_user.is_deleted = True
        found_user.deleted_at = datetime.now()
        await test_db_session.commit()


class TestOrganizationCRUD:
    """组织模型CRUD测试"""

    @pytest.mark.asyncio
    async def test_organization_crud(self, test_db_session: AsyncSession):
        """Test Organization model CRUD operations."""
        user_id = uuid4()
        unique_id = str(uuid4())[:8]

        org = Organization(
            name=f'Test Organization {unique_id}',
            description='Test Description',
            created_by=user_id,
        )
        test_db_session.add(org)
        await test_db_session.commit()
        await test_db_session.refresh(org)

        stmt = select(Organization).where(Organization.name == f'Test Organization {unique_id}')
        result = await test_db_session.execute(stmt)
        found_org = result.scalar_one_or_none()
        assert found_org is not None

        found_org.description = 'Updated Description'
        await test_db_session.commit()

        found_org.is_deleted = True
        await test_db_session.commit()


class TestWorkflowCRUD:
    """工作流模型CRUD测试"""

    @pytest.mark.asyncio
    async def test_workflow_crud(self, test_db_session: AsyncSession):
        """Test Workflow model CRUD operations."""
        workspace_id = uuid4()
        user_id = uuid4()
        unique_id = str(uuid4())[:8]

        workflow = Workflow(
            name=f'Test Workflow {unique_id}',
            description='Test workflow description',
            workspace_id=workspace_id,
            created_by=user_id,
            input_schema={'type': 'object'},
            output_schema={'type': 'object'},
        )
        test_db_session.add(workflow)
        await test_db_session.commit()
        await test_db_session.refresh(workflow)

        stmt = select(Workflow).where(Workflow.name == f'Test Workflow {unique_id}')
        result = await test_db_session.execute(stmt)
        found_workflow = result.scalar_one_or_none()
        assert found_workflow is not None

        found_workflow.description = 'Updated workflow description'
        await test_db_session.commit()

        found_workflow.is_deleted = True
        await test_db_session.commit()


class TestApplicationCRUD:
    """应用模型CRUD测试"""

    @pytest.mark.asyncio
    async def test_application_crud(self, test_db_session: AsyncSession):
        """Test Application model CRUD operations."""
        workspace_id = uuid4()
        workflow_id = uuid4()
        user_id = uuid4()
        unique_id = str(uuid4())[:8]

        app = Application(
            name=f'Test Application {unique_id}',
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            created_by=user_id,
            api_key_hash='test_hash',
            endpoint=f'/api/test/{unique_id}',
            is_published=False,
        )
        test_db_session.add(app)
        await test_db_session.commit()
        await test_db_session.refresh(app)

        stmt = select(Application).where(Application.name == f'Test Application {unique_id}')
        result = await test_db_session.execute(stmt)
        found_app = result.scalar_one_or_none()
        assert found_app is not None

        found_app.is_published = True
        await test_db_session.commit()


class TestTokenCRUD:
    """Token模型CRUD测试"""

    @pytest.mark.asyncio
    async def test_user_token_crud(self, test_db_session: AsyncSession):
        """Test User Token CRUD operations."""
        user_id = uuid4()

        token = RefreshToken(
            user_id=user_id,
            token_hash='hashed_token',
            expires_at=datetime.now(),
            revoked=False,
            created_by=user_id,
        )
        test_db_session.add(token)
        await test_db_session.commit()
        await test_db_session.refresh(token)

        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
        result = await test_db_session.execute(stmt)
        found_token = result.scalar_one_or_none()
        assert found_token is not None

        found_token.revoked = True
        await test_db_session.commit()

        await test_db_session.delete(found_token)
        await test_db_session.commit()


class TestTeamCRUD:
    """团队模型CRUD测试"""

    @pytest.mark.asyncio
    async def test_team_crud(self, test_db_session: AsyncSession):
        """Test Team CRUD operations."""
        organization_id = uuid4()
        user_id = uuid4()
        unique_id = str(uuid4())[:8]

        team = Team(
            name=f'Test Team {unique_id}',
            description='Test team description',
            organization_id=organization_id,
            created_by=user_id,
        )
        test_db_session.add(team)
        await test_db_session.commit()
        await test_db_session.refresh(team)

        stmt = select(Team).where(Team.name == f'Test Team {unique_id}')
        result = await test_db_session.execute(stmt)
        found_team = result.scalar_one_or_none()
        assert found_team is not None

        found_team.description = 'Updated team description'
        await test_db_session.commit()


class TestAuditLogCRUD:
    """审计日志模型CRUD测试"""

    @pytest.mark.asyncio
    async def test_audit_log_crud(self, test_db_session: AsyncSession):
        """Test Audit Log CRUD operations."""
        workspace_id = uuid4()
        user_id = uuid4()
        resource_id = uuid4()

        audit_log = AuditLog(
            workspace_id=workspace_id,
            user_id=user_id,
            action='CREATE',
            resource_type='workflow',
            resource_id=resource_id,
            details={'name': 'Test Workflow'},
            ip_address='192.168.1.1',
            user_agent='Test Agent',
            status='success',
        )
        test_db_session.add(audit_log)
        await test_db_session.commit()
        await test_db_session.refresh(audit_log)

        stmt = select(AuditLog).where(AuditLog.resource_id == resource_id)
        result = await test_db_session.execute(stmt)
        found_log = result.scalar_one_or_none()
        assert found_log is not None
        assert found_log.resource_type == 'workflow'


class TestIntegrationScenarios:
    """集成场景测试"""

    @pytest.mark.asyncio
    async def test_complete_workflow_scenario(self, test_db_session: AsyncSession):
        """Test a complete workflow from user creation to workflow execution."""
        unique_id = str(uuid4())[:8]

        # Create user
        user = UserEntity(
            name=f'Integration Test User {unique_id}',
            email=f'integration{unique_id}@example.com',
            password_hash='hashed_password',
            is_active=True,
        )
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        # Create organization
        org = Organization(name=f'Integration Test Org {unique_id}', created_by=user.id)
        test_db_session.add(org)
        await test_db_session.commit()
        await test_db_session.refresh(org)

        # Create team
        team = Team(
            name=f'Integration Test Team {unique_id}', organization_id=org.id, created_by=user.id
        )
        test_db_session.add(team)
        await test_db_session.commit()
        await test_db_session.refresh(team)

        # Create workspace
        workspace = Workspace(
            name=f'Integration Test Workspace {unique_id}', team_id=team.id, created_by=user.id
        )
        test_db_session.add(workspace)
        await test_db_session.commit()
        await test_db_session.refresh(workspace)

        # Create workflow
        workflow = Workflow(
            name=f'Integration Test Workflow {unique_id}',
            workspace_id=workspace.id,
            created_by=user.id,
            input_schema={'type': 'object'},
            output_schema={'type': 'object'},
        )
        test_db_session.add(workflow)
        await test_db_session.commit()
        await test_db_session.refresh(workflow)

        # Verify all entities exist and are linked correctly
        assert user.id is not None
        assert org.created_by == user.id
        assert team.organization_id == org.id
        assert workspace.team_id == team.id
        assert workflow.workspace_id == workspace.id
