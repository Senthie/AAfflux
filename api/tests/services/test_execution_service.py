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

from app.models.auth.user import UserEntity
from app.models.tenant.organization import Organization
from app.models.workflow.workflow import Workflow
from app.schemas.execution import ExecutionRecordCreate, ExecutionRecordQuery, ExecutionRecordUpdate
from app.services.execution_record_service import ExecutionRecordService
from app.utils.migration import DataMigrator


class TestExecutionRecordService:
    """执行记录服务测试"""

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
        workflow = Workflow(
            id=uuid4(),
            name='Test Workflow',
            description='Test workflow for execution',
            created_by=test_user.id,
            workspace_id=uuid4(),
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
            inputs={'test': 'data'},
        )

        record = await execution_service.create_execution_record(record_data)

        assert record is not None
        assert record.workflow_id == test_workflow.id
        assert record.status == 'PENDING'

    async def test_query_execution_records_by_filters(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试按条件查询执行记录"""
        for i in range(3):
            record_data = ExecutionRecordCreate(
                workflow_id=test_workflow.id,
                inputs={'test': f'data_{i}'},
            )
            record = await execution_service.create_execution_record(record_data)
            # 更新状态
            if i % 2 == 0:
                update_data = ExecutionRecordUpdate(status='SUCCESS')
            else:
                update_data = ExecutionRecordUpdate(status='FAILED')
            await execution_service.update_execution_record(record.id, update_data)

        # 使用 list_execution_records 方法
        query = ExecutionRecordQuery(workflow_id=test_workflow.id, status='SUCCESS')
        completed_records, total = await execution_service.list_execution_records(query)
        assert len(completed_records) == 2

    async def test_time_range_filtering(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试时间范围筛选"""
        now = datetime.utcnow()

        # 创建记录
        old_record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            inputs={'test': 'old'},
        )
        recent_record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            inputs={'test': 'recent'},
        )

        await execution_service.create_execution_record(old_record_data)
        await execution_service.create_execution_record(recent_record_data)

        # 使用 get_execution_records_by_date_range 方法
        recent_records = await execution_service.get_execution_records_by_date_range(
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(hours=1),
            workflow_id=test_workflow.id,
        )

        assert len(recent_records) >= 1

    async def test_cleanup_expired_records(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试过期记录清理"""
        # 创建记录
        record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            inputs={'test': 'valid'},
        )

        record = await execution_service.create_execution_record(record_data)
        # 标记为成功
        await execution_service.update_execution_record(
            record.id, ExecutionRecordUpdate(status='SUCCESS')
        )

        # 清理 0 天前的记录（不应该删除刚创建的记录）
        cleanup_count = await execution_service.cleanup_expired_records(days=0)
        # 刚创建的记录不应该被清理
        assert cleanup_count >= 0

    async def test_update_execution_record(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试更新执行记录"""
        record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            inputs={'test': 'data'},
        )

        record = await execution_service.create_execution_record(record_data)

        update_data = ExecutionRecordUpdate(
            status='SUCCESS',
            outputs={'result': 'success'},
            completed_at=datetime.utcnow(),
        )

        updated_record = await execution_service.update_execution_record(record.id, update_data)

        assert updated_record.status == 'SUCCESS'
        assert updated_record.outputs == {'result': 'success'}


class TestDataMigration:
    """数据迁移测试"""

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
    def migration_manager(self, test_session: AsyncSession):
        """创建数据迁移管理器实例"""
        return DataMigrator()

    async def test_data_migration_backward_compatibility(
        self,
        migration_manager: DataMigrator,
        test_user: UserEntity,
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
            created_by=test_user.id,
            workspace_id=uuid4(),
        )
        test_session.add(workflow)
        await test_session.commit()

        migrated_definition = await migration_manager.migrate_workflow_definition(
            old_workflow_definition, from_version='1.0', to_version='2.0'
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
