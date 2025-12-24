"""
执行记录服务层测试

合并自:
- test_execution_records.py
- test_data_migration.py

测试内容:
- 执行记录CRUD
- 时间范围筛选
- 过期记录清理
- 数据迁移
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth.user import User
from app.models.tenant.organization import Organization
from app.models.workflow.workflow import Workflow
from app.schemas.execution import ExecutionRecordCreate, ExecutionRecordUpdate
from app.services.execution_record_service import ExecutionRecordService
from app.utils.migration import DataMigrator


class TestExecutionRecordService:
    """执行记录服务测试"""

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

    @pytest.fixture
    async def test_organization(self, test_session: AsyncSession, test_user: User):
        """创建测试组织"""
        org = Organization(id=uuid4(), name='Test Org', creator_id=test_user.id, is_active=True)
        test_session.add(org)
        await test_session.commit()
        await test_session.refresh(org)
        return org

    @pytest.fixture
    async def test_workflow(
        self, test_session: AsyncSession, test_user: User, test_organization: Organization
    ):
        """创建测试工作流"""
        workflow = Workflow(
            id=uuid4(),
            name='Test Workflow',
            description='Test workflow for execution',
            creator_id=test_user.id,
            organization_id=test_organization.id,
            definition={'nodes': [], 'connections': []},
            is_active=True,
        )
        test_session.add(workflow)
        await test_session.commit()
        await test_session.refresh(workflow)
        return workflow

    @pytest.fixture
    def execution_service(self, test_session: AsyncSession):
        """创建执行记录服务实例"""
        return ExecutionRecordService(test_session)

    async def test_create_execution_record(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试创建执行记录"""
        record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            status='running',
            input_data={'test': 'data'},
            started_at=datetime.utcnow(),
        )

        record = await execution_service.create_execution_record(record_data)

        assert record is not None
        assert record.workflow_id == test_workflow.id
        assert record.status == 'running'

    async def test_query_execution_records_by_filters(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试按条件查询执行记录"""
        for i in range(3):
            record_data = ExecutionRecordCreate(
                workflow_id=test_workflow.id,
                status='completed' if i % 2 == 0 else 'failed',
                input_data={'test': f'data_{i}'},
                started_at=datetime.utcnow() - timedelta(hours=i),
            )
            await execution_service.create_execution_record(record_data)

        completed_records = await execution_service.get_execution_records(
            workflow_id=test_workflow.id, status='completed'
        )
        assert len(completed_records) == 2

    async def test_time_range_filtering(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试时间范围筛选"""
        now = datetime.utcnow()

        old_record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            status='completed',
            input_data={'test': 'old'},
            started_at=now - timedelta(days=2),
        )

        recent_record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            status='completed',
            input_data={'test': 'recent'},
            started_at=now - timedelta(hours=1),
        )

        await execution_service.create_execution_record(old_record_data)
        await execution_service.create_execution_record(recent_record_data)

        recent_records = await execution_service.get_execution_records(
            workflow_id=test_workflow.id, start_time=now - timedelta(days=1), end_time=now
        )

        assert len(recent_records) == 1
        assert recent_records[0].input_data == {'test': 'recent'}

    async def test_cleanup_expired_records(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试过期记录清理"""
        now = datetime.utcnow()

        expired_record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            status='completed',
            input_data={'test': 'expired'},
            started_at=now - timedelta(days=31),
        )

        valid_record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            status='completed',
            input_data={'test': 'valid'},
            started_at=now - timedelta(days=1),
        )

        await execution_service.create_execution_record(expired_record_data)
        await execution_service.create_execution_record(valid_record_data)

        cleanup_count = await execution_service.cleanup_expired_records(days=30)
        assert cleanup_count == 1

        remaining_records = await execution_service.get_execution_records(
            workflow_id=test_workflow.id
        )
        assert len(remaining_records) == 1

    async def test_update_execution_record(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试更新执行记录"""
        record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            status='running',
            input_data={'test': 'data'},
            started_at=datetime.utcnow(),
        )

        record = await execution_service.create_execution_record(record_data)

        update_data = ExecutionRecordUpdate(
            status='completed', output_data={'result': 'success'}, ended_at=datetime.utcnow()
        )

        updated_record = await execution_service.update_execution_record(record.id, update_data)

        assert updated_record.status == 'completed'
        assert updated_record.output_data == {'result': 'success'}


class TestDataMigration:
    """数据迁移测试"""

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

    @pytest.fixture
    async def test_organization(self, test_session: AsyncSession, test_user: User):
        """创建测试组织"""
        org = Organization(id=uuid4(), name='Test Org', creator_id=test_user.id, is_active=True)
        test_session.add(org)
        await test_session.commit()
        await test_session.refresh(org)
        return org

    @pytest.fixture
    def migration_manager(self, test_session: AsyncSession):
        """创建数据迁移管理器实例"""
        return DataMigrator()

    async def test_data_migration_backward_compatibility(
        self,
        migration_manager: DataMigrator,
        test_user: User,
        test_organization: Organization,
        test_session: AsyncSession,
    ):
        """测试数据迁移向后兼容性"""
        old_workflow_definition = {
            'version': '1.0',
            'nodes': [{'id': 'node1', 'type': 'start', 'config': {'message': 'Hello'}}],
            'connections': [],
        }

        workflow = Workflow(
            id=uuid4(),
            name='Legacy Workflow',
            description='Test legacy workflow',
            creator_id=test_user.id,
            organization_id=test_organization.id,
            definition=old_workflow_definition,
            is_active=True,
        )
        test_session.add(workflow)
        await test_session.commit()

        migrated_definition = await migration_manager.migrate_workflow_definition(
            workflow.definition, from_version='1.0', to_version='2.0'
        )

        assert migrated_definition['version'] == '2.0'
        assert 'nodes' in migrated_definition
        assert 'metadata' in migrated_definition

    async def test_migration_version_management(self, migration_manager: DataMigrator):
        """测试迁移版本管理"""
        current_version = await migration_manager.get_current_schema_version()
        assert current_version is not None

        assert migration_manager.compare_versions('1.0', '2.0') < 0
        assert migration_manager.compare_versions('2.0', '1.0') > 0
        assert migration_manager.compare_versions('1.0', '1.0') == 0

    async def test_migration_validation(self, migration_manager: DataMigrator):
        """测试迁移数据验证"""
        valid_definition = {
            'version': '1.0',
            'nodes': [{'id': 'node1', 'type': 'start', 'config': {}}],
            'connections': [],
        }

        is_valid = await migration_manager.validate_workflow_definition(valid_definition)
        assert is_valid is True

        invalid_definition = {
            'version': '1.0',
            'nodes': [{'id': 'node1'}],  # 缺少type字段
            'connections': [],
        }

        is_invalid = await migration_manager.validate_workflow_definition(invalid_definition)
        assert is_invalid is False
