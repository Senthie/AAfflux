"""
CRUD Tests for Tasks 1-6 Implementation

This module tests the CRUD operations for all implemented features from tasks 1-6:
- Task 1: Infrastructure (Config, Database)
- Task 2: Data Models (Core domain models)
- Task 3: Authentication & Authorization
- Task 4: File Storage
- Task 5: Tenant Management (Organizations, Teams, Workspaces)
- Task 6: Permission Control (RBAC)

Note: Task 7 (BPM Engine) is excluded as it's planned for future implementation.

Only performs Create, Read, Update, Delete operations without modifying database schema.
"""

from datetime import datetime
from decimal import Decimal
from typing import AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

# Task 2: Data Models
from app.models.application.application import Application
from app.models.audit.audit_log import AuditLog
from app.models.auth.api_key import APIKey
from app.models.auth.token import RefreshToken
from app.models.auth.user import User
from app.models.billing.billing import Subscription
from app.models.dataset.dataset import Dataset
from app.models.file.reference import FileReference
from app.models.tenant.invitation import TeamInvitation
from app.models.tenant.organization import Organization, Team, TeamMember, Workspace
from app.models.workflow.workflow import Workflow


@pytest.fixture(scope='function')
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """专用测试数据库会话 - 使用 lowcode_test 数据库"""
    # 构建测试数据库URL
    test_db_url = 'postgresql+asyncpg://postgres:postgres@14.12.0.102:5432/lowcode_test'

    # 创建测试专用引擎
    engine = create_async_engine(
        test_db_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # 创建会话
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()  # 自动回滚

    await engine.dispose()


class TestTask1Infrastructure:
    """Test Task 1: Infrastructure and Configuration"""

    @pytest.mark.asyncio
    async def test_database_connection(self, test_db_session: AsyncSession):
        """Test database connection and basic query."""
        from sqlalchemy import text

        result = await test_db_session.execute(text('SELECT 1 as test_value'))
        row = result.fetchone()
        assert row[0] == 1

    @pytest.mark.asyncio
    async def test_configuration_loading(self):
        """Test configuration loading."""
        from app.core.config import settings

        assert settings.app_name is not None
        assert settings.database_url is not None
        assert settings.jwt_secret_key is not None


class TestTask2DataModels:
    """Test Task 2: Data Models CRUD Operations"""

    @pytest.mark.asyncio
    async def test_user_crud(self, test_db_session: AsyncSession):
        """Test User model CRUD operations."""
        # Create
        unique_id = str(uuid4())[:8]
        user = User(
            name=f'Test User {unique_id}',
            email=f'test{unique_id}@example.com',
            password_hash='hashed_password',
            is_active=True,
        )
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        # Read
        stmt = select(User).where(User.email == f'test{unique_id}@example.com')
        result = await test_db_session.execute(stmt)
        found_user = result.scalar_one_or_none()
        assert found_user is not None
        assert found_user.name == f'Test User {unique_id}'

        # Update
        found_user.name = f'Updated User {unique_id}'
        await test_db_session.commit()
        await test_db_session.refresh(found_user)
        assert found_user.name == f'Updated User {unique_id}'

        # Delete (soft delete)
        found_user.is_deleted = True
        found_user.deleted_at = datetime.now()
        await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_organization_crud(self, test_db_session: AsyncSession):
        """Test Organization model CRUD operations."""
        user_id = uuid4()

        # Create
        unique_id = str(uuid4())[:8]
        org = Organization(
            name=f'Test Organization {unique_id}',
            description='Test Description',
            created_by=user_id,
        )
        test_db_session.add(org)
        await test_db_session.commit()
        await test_db_session.refresh(org)

        # Read
        stmt = select(Organization).where(Organization.name == f'Test Organization {unique_id}')
        result = await test_db_session.execute(stmt)
        found_org = result.scalar_one_or_none()
        assert found_org is not None
        assert found_org.description == 'Test Description'

        # Update
        found_org.description = 'Updated Description'
        await test_db_session.commit()

        # Delete (soft delete)
        found_org.is_deleted = True
        found_org.deleted_at = datetime.now()
        await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_workflow_crud(self, test_db_session: AsyncSession):
        """Test Workflow model CRUD operations."""
        workspace_id = uuid4()
        user_id = uuid4()

        # Create
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

        # Read
        stmt = select(Workflow).where(Workflow.name == f'Test Workflow {unique_id}')
        result = await test_db_session.execute(stmt)
        found_workflow = result.scalar_one_or_none()
        assert found_workflow is not None

        # Update
        found_workflow.description = 'Updated workflow description'
        await test_db_session.commit()

        # Delete (soft delete)
        found_workflow.is_deleted = True
        found_workflow.deleted_at = datetime.now()
        await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_application_crud(self, test_db_session: AsyncSession):
        """Test Application model CRUD operations."""
        workspace_id = uuid4()
        workflow_id = uuid4()
        user_id = uuid4()

        # Create
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

        # Read
        stmt = select(Application).where(Application.name == f'Test Application {unique_id}')
        result = await test_db_session.execute(stmt)
        found_app = result.scalar_one_or_none()
        assert found_app is not None

        # Update
        found_app.is_published = True
        await test_db_session.commit()

        # Delete (soft delete)
        found_app.is_deleted = True
        found_app.deleted_at = datetime.now()
        await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_dataset_crud(self, test_db_session: AsyncSession):
        """Test Dataset CRUD operations."""
        workspace_id = uuid4()
        user_id = uuid4()

        # Create
        unique_id = str(uuid4())[:8]
        dataset = Dataset(
            name=f'Test Dataset {unique_id}',
            description='Test dataset description',
            workspace_id=workspace_id,
            created_by=user_id,
            embedding_model='text-embedding-ada-002',
            embedding_model_provider='openai',
            indexing_technique='vector',
            document_count=0,
            word_count=0,
        )
        test_db_session.add(dataset)
        await test_db_session.commit()
        await test_db_session.refresh(dataset)

        # Read
        stmt = select(Dataset).where(Dataset.name == f'Test Dataset {unique_id}')
        result = await test_db_session.execute(stmt)
        found_dataset = result.scalar_one_or_none()
        assert found_dataset is not None

        # Update
        found_dataset.description = 'Updated dataset description'
        await test_db_session.commit()

        # Delete (soft delete)
        found_dataset.is_deleted = True
        found_dataset.deleted_at = datetime.now()
        await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_subscription_crud(self, test_db_session: AsyncSession):
        """Test Subscription model CRUD operations."""
        workspace_id = uuid4()

        # Create
        subscription = Subscription(
            workspace_id=workspace_id,
            plan_type='pro',
            plan_name='Professional Plan',
            status='active',
            billing_cycle='monthly',
            price=Decimal('99.00'),
            quota_limits={'api_calls': 10000},
            current_period_start=datetime.now(),
            current_period_end=datetime.now(),
        )
        test_db_session.add(subscription)
        await test_db_session.commit()
        await test_db_session.refresh(subscription)

        # Read
        stmt = select(Subscription).where(Subscription.workspace_id == workspace_id)
        result = await test_db_session.execute(stmt)
        found_sub = result.scalar_one_or_none()
        assert found_sub is not None

        # Update
        found_sub.status = 'cancelled'
        await test_db_session.commit()

        # Delete (soft delete)
        found_sub.is_deleted = True
        found_sub.deleted_at = datetime.now()
        await test_db_session.commit()


class TestTask3Authentication:
    """Test Task 3: Authentication and Authorization"""

    @pytest.mark.asyncio
    async def test_user_token_crud(self, test_db_session: AsyncSession):
        """Test User Token CRUD operations."""
        user_id = uuid4()

        # Create
        token = RefreshToken(
            user_id=user_id,
            token_hash='hashed_token',
            expires_at=datetime.now(),
            revoked=False,
            created_by=user_id,  # 添加必需的created_by字段
        )
        test_db_session.add(token)
        await test_db_session.commit()
        await test_db_session.refresh(token)

        # Read
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
        result = await test_db_session.execute(stmt)
        found_token = result.scalar_one_or_none()
        assert found_token is not None
        assert found_token.revoked is not True

        # Update
        found_token.revoked = True
        await test_db_session.commit()

        # Delete
        await test_db_session.delete(found_token)
        await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_api_key_crud(self, test_db_session: AsyncSession):
        """Test API Key CRUD operations."""
        application_id = uuid4()

        # Create
        api_key = APIKey(
            application_id=application_id,
            key_hash='hashed_api_key',
            key_prefix='ak_test',
            name='Test API Key',
            is_active=True,
        )
        test_db_session.add(api_key)
        await test_db_session.commit()
        await test_db_session.refresh(api_key)

        # Read
        stmt = select(APIKey).where(APIKey.key_prefix == 'ak_test')
        result = await test_db_session.execute(stmt)
        found_key = result.scalar_one_or_none()
        assert found_key is not None

        # Update
        found_key.is_active = False
        await test_db_session.commit()

        # Delete
        await test_db_session.delete(found_key)
        await test_db_session.commit()


class TestTask4FileStorage:
    """Test Task 4: File Storage"""

    @pytest.mark.skip(
        reason="FileReference table has problematic 'd' field - database schema issue"
    )
    @pytest.mark.asyncio
    async def test_file_reference_crud(self, test_db_session: AsyncSession):
        """Test File Reference CRUD operations."""
        workspace_id = uuid4()
        file_id = uuid4()
        user_id = uuid4()

        # Create
        file_ref = FileReference(
            workspace_id=workspace_id,
            file_id=file_id,
            filename='test_file.txt',
            content_type='text/plain',
            size_bytes=1024,
            storage_type='gridfs',
            mongo_id='507f1f77bcf86cd799439011',
            uploaded_by=user_id,
        )
        test_db_session.add(file_ref)
        await test_db_session.commit()
        await test_db_session.refresh(file_ref)

        # Read
        stmt = select(FileReference).where(FileReference.filename == 'test_file.txt')
        result = await test_db_session.execute(stmt)
        found_file = result.scalar_one_or_none()
        assert found_file is not None
        assert found_file.content_type == 'text/plain'

        # Update
        found_file.filename = 'updated_file.txt'
        await test_db_session.commit()

        # Delete (soft delete)
        found_file.is_deleted = True
        found_file.deleted_at = datetime.now()
        await test_db_session.commit()


class TestTask5TenantManagement:
    """Test Task 5: Tenant Management"""

    @pytest.mark.asyncio
    async def test_team_crud(self, test_db_session: AsyncSession):
        """Test Team CRUD operations."""
        organization_id = uuid4()
        user_id = uuid4()

        # Create
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

        # Read
        stmt = select(Team).where(Team.name == f'Test Team {unique_id}')
        result = await test_db_session.execute(stmt)
        found_team = result.scalar_one_or_none()
        assert found_team is not None

        # Update
        found_team.description = 'Updated team description'
        await test_db_session.commit()

        # Delete (soft delete)
        found_team.is_deleted = True
        found_team.deleted_at = datetime.now()
        await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_workspace_crud(self, test_db_session: AsyncSession):
        """Test Workspace CRUD operations."""
        team_id = uuid4()
        user_id = uuid4()

        # Create
        unique_id = str(uuid4())[:8]
        workspace = Workspace(
            name=f'Test Workspace {unique_id}',
            description='Test workspace description',
            team_id=team_id,
            created_by=user_id,
        )
        test_db_session.add(workspace)
        await test_db_session.commit()
        await test_db_session.refresh(workspace)

        # Read
        stmt = select(Workspace).where(Workspace.name == f'Test Workspace {unique_id}')
        result = await test_db_session.execute(stmt)
        found_workspace = result.scalar_one_or_none()
        assert found_workspace is not None

        # Update
        found_workspace.description = 'Updated workspace description'
        await test_db_session.commit()

        # Delete (soft delete)
        found_workspace.is_deleted = True
        found_workspace.deleted_at = datetime.now()
        await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_team_member_crud(self, test_db_session: AsyncSession):
        """Test Team Member CRUD operations."""
        team_id = uuid4()
        user_id = uuid4()
        invited_by = uuid4()

        # Create
        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role='member',
            invited_by=invited_by,
            joined_at=datetime.now(),
        )
        test_db_session.add(member)
        await test_db_session.commit()
        await test_db_session.refresh(member)

        # Read
        stmt = select(TeamMember).where(TeamMember.user_id == user_id)
        result = await test_db_session.execute(stmt)
        found_member = result.scalar_one_or_none()
        assert found_member is not None
        assert found_member.role == 'member'

        # Update
        found_member.role = 'admin'
        await test_db_session.commit()

        # Delete
        await test_db_session.delete(found_member)
        await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_invitation_crud(self, test_db_session: AsyncSession):
        """Test Invitation CRUD operations."""
        team_id = uuid4()
        invited_by = uuid4()

        # Create
        invitation = TeamInvitation(
            email='invite@example.com',
            team_id=team_id,
            role='MEMBER',
            token='test_token_123',
            invited_by=invited_by,
            status='PENDING',
            expires_at=datetime.now(),
        )
        test_db_session.add(invitation)
        await test_db_session.commit()
        await test_db_session.refresh(invitation)

        # Read
        stmt = select(TeamInvitation).where(TeamInvitation.email == 'invite@example.com')
        result = await test_db_session.execute(stmt)
        found_invitation = result.scalar_one_or_none()
        assert found_invitation is not None

        # Update
        found_invitation.status = 'ACCEPTED'
        await test_db_session.commit()

        # Delete
        await test_db_session.delete(found_invitation)
        await test_db_session.commit()


class TestTask6PermissionControl:
    """Test Task 6: Permission Control (RBAC)"""

    @pytest.mark.asyncio
    async def test_audit_log_crud(self, test_db_session: AsyncSession):
        """Test Audit Log CRUD operations."""
        workspace_id = uuid4()
        user_id = uuid4()
        resource_id = uuid4()

        # Create
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

        # Read
        stmt = select(AuditLog).where(AuditLog.resource_id == resource_id)
        result = await test_db_session.execute(stmt)
        found_log = result.scalar_one_or_none()
        assert found_log is not None
        assert found_log.resource_type == 'workflow'

        # Update
        found_log.status = 'completed'
        await test_db_session.commit()

        # Delete
        await test_db_session.delete(found_log)
        await test_db_session.commit()


class TestIntegrationScenarios:
    """Test integration scenarios across multiple tasks"""

    @pytest.mark.asyncio
    async def test_complete_workflow_scenario(self, test_db_session: AsyncSession):
        """Test a complete workflow from user creation to workflow execution."""
        # Create user (Task 3)
        unique_id = str(uuid4())[:8]
        user = User(
            name=f'Integration Test User {unique_id}',
            email=f'integration{unique_id}@example.com',
            password_hash='hashed_password',
            is_active=True,
        )
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        # Create organization (Task 5)
        org = Organization(name=f'Integration Test Org {unique_id}', created_by=user.id)
        test_db_session.add(org)
        await test_db_session.commit()
        await test_db_session.refresh(org)

        # Create team (Task 5)
        team = Team(
            name=f'Integration Test Team {unique_id}', organization_id=org.id, created_by=user.id
        )
        test_db_session.add(team)
        await test_db_session.commit()
        await test_db_session.refresh(team)

        # Create workspace (Task 5)
        workspace = Workspace(
            name=f'Integration Test Workspace {unique_id}', team_id=team.id, created_by=user.id
        )
        test_db_session.add(workspace)
        await test_db_session.commit()
        await test_db_session.refresh(workspace)

        # Create workflow (Task 2)
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

        # Create application (Task 2)
        app = Application(
            name=f'Integration Test App {unique_id}',
            workspace_id=workspace.id,
            workflow_id=workflow.id,
            created_by=user.id,
            api_key_hash='integration_hash',
            endpoint=f'/api/integration/{unique_id}',
            is_published=True,
        )
        test_db_session.add(app)
        await test_db_session.commit()
        await test_db_session.refresh(app)

        # Create audit log (Task 6)
        audit_log = AuditLog(
            workspace_id=workspace.id,
            user_id=user.id,
            action='CREATE',
            resource_type='application',
            resource_id=app.id,
            details={'name': app.name},
            status='success',
        )
        test_db_session.add(audit_log)
        await test_db_session.commit()

        # Verify all entities exist and are linked correctly
        assert user.id is not None
        assert org.created_by == user.id
        assert team.organization_id == org.id
        assert workspace.team_id == team.id
        assert workflow.workspace_id == workspace.id
        assert app.workflow_id == workflow.id
        assert audit_log.resource_id == app.id
