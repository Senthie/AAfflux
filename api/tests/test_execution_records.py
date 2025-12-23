"""
测试任务16 - 执行记录模块
只对数据库进行CRUD操作，不进行迁移
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.execution_record_service import ExecutionRecordService
from app.schemas.execution import ExecutionRecordCreate, ExecutionRecordUpdate
from app.models.workflow.workflow import Workflow
from app.models.auth.user import User
from app.models.tenant.organization import Organization


class TestExecutionRecords:
    """执行记录模块测试"""

    @pytest.fixture
    async def test_user(self, test_session: AsyncSession):
        """创建测试用户"""
        user = User(
            id=uuid4(),
            email='test@example.com',
            username='testuser',
            hashed_password='hashed_password',
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
        assert record.input_data == {'test': 'data'}
        assert record.started_at is not None

    async def test_query_execution_records_by_filters(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试按条件查询执行记录"""
        # 创建多个执行记录
        for i in range(3):
            record_data = ExecutionRecordCreate(
                workflow_id=test_workflow.id,
                status='completed' if i % 2 == 0 else 'failed',
                input_data={'test': f'data_{i}'},
                started_at=datetime.utcnow() - timedelta(hours=i),
            )
            await execution_service.create_execution_record(record_data)

        # 按状态查询
        completed_records = await execution_service.get_execution_records(
            workflow_id=test_workflow.id, status='completed'
        )
        assert len(completed_records) == 2

        # 按工作流ID查询
        all_records = await execution_service.get_execution_records(workflow_id=test_workflow.id)
        assert len(all_records) == 3

    async def test_execution_record_integrity(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试执行记录数据完整性"""
        record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            status='running',
            input_data={'complex': {'nested': {'data': [1, 2, 3]}}},
            started_at=datetime.utcnow(),
        )

        record = await execution_service.create_execution_record(record_data)

        # 验证数据完整性
        retrieved_record = await execution_service.get_execution_record(record.id)
        assert retrieved_record is not None
        assert retrieved_record.input_data == record_data.input_data
        assert retrieved_record.workflow_id == test_workflow.id

    async def test_time_range_filtering(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试时间范围筛选"""
        now = datetime.utcnow()

        # 创建不同时间的记录
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

        # 查询最近24小时的记录
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

        # 创建过期记录
        expired_record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            status='completed',
            input_data={'test': 'expired'},
            started_at=now - timedelta(days=31),  # 31天前
        )

        # 创建未过期记录
        valid_record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            status='completed',
            input_data={'test': 'valid'},
            started_at=now - timedelta(days=1),
        )

        await execution_service.create_execution_record(expired_record_data)
        await execution_service.create_execution_record(valid_record_data)

        # 执行清理（清理30天前的记录）
        cleanup_count = await execution_service.cleanup_expired_records(days=30)

        assert cleanup_count == 1

        # 验证只剩下未过期的记录
        remaining_records = await execution_service.get_execution_records(
            workflow_id=test_workflow.id
        )
        assert len(remaining_records) == 1
        assert remaining_records[0].input_data == {'test': 'valid'}

    async def test_update_execution_record(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试更新执行记录"""
        # 创建记录
        record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            status='running',
            input_data={'test': 'data'},
            started_at=datetime.utcnow(),
        )

        record = await execution_service.create_execution_record(record_data)

        # 更新记录
        update_data = ExecutionRecordUpdate(
            status='completed', output_data={'result': 'success'}, ended_at=datetime.utcnow()
        )

        updated_record = await execution_service.update_execution_record(record.id, update_data)

        assert updated_record.status == 'completed'
        assert updated_record.output_data == {'result': 'success'}
        assert updated_record.ended_at is not None

    async def test_delete_execution_record(
        self, execution_service: ExecutionRecordService, test_workflow: Workflow
    ):
        """测试删除执行记录"""
        # 创建记录
        record_data = ExecutionRecordCreate(
            workflow_id=test_workflow.id,
            status='completed',
            input_data={'test': 'data'},
            started_at=datetime.utcnow(),
        )

        record = await execution_service.create_execution_record(record_data)
        record_id = record.id

        # 删除记录
        success = await execution_service.delete_execution_record(record_id)
        assert success is True

        # 验证记录已删除
        deleted_record = await execution_service.get_execution_record(record_id)
        assert deleted_record is None
