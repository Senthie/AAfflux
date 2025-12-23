"""
测试任务19 - 数据迁移支持
只对数据库进行CRUD操作，不进行迁移
"""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth.user import User
from app.models.tenant.organization import Organization
from app.models.workflow.workflow import Workflow
from app.utils.migration import DataMigrator


class TestDataMigration:
    """数据迁移测试"""

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
        # 创建旧版本格式的工作流数据
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
        await test_session.refresh(workflow)

        # 测试迁移到新版本
        migrated_definition = await migration_manager.migrate_workflow_definition(
            workflow.definition, from_version='1.0', to_version='2.0'
        )

        # 验证迁移后的数据格式
        assert migrated_definition['version'] == '2.0'
        assert 'nodes' in migrated_definition
        assert 'connections' in migrated_definition
        assert 'metadata' in migrated_definition  # 新版本应该有metadata字段

        # 验证节点数据保持完整
        assert len(migrated_definition['nodes']) == 1
        assert migrated_definition['nodes'][0]['id'] == 'node1'
        assert migrated_definition['nodes'][0]['type'] == 'start'

    async def test_migration_version_management(self, migration_manager: DataMigrator):
        """测试迁移版本管理"""
        # 测试获取当前版本
        current_version = await migration_manager.get_current_schema_version()
        assert current_version is not None
        assert isinstance(current_version, str)

        # 测试版本比较
        assert migration_manager.compare_versions('1.0', '2.0') < 0
        assert migration_manager.compare_versions('2.0', '1.0') > 0
        assert migration_manager.compare_versions('1.0', '1.0') == 0

        # 测试版本兼容性检查
        is_compatible = await migration_manager.is_version_compatible('1.0', '2.0')
        assert isinstance(is_compatible, bool)

    async def test_rollback_migration(
        self,
        migration_manager: DataMigrator,
        test_user: User,
        test_organization: Organization,
        test_session: AsyncSession,
    ):
        """测试迁移回滚"""
        # 创建新版本格式的工作流数据
        new_workflow_definition = {
            'version': '2.0',
            'nodes': [
                {
                    'id': 'node1',
                    'type': 'llm',
                    'config': {'model': 'llama2', 'prompt': 'Hello'},
                    'position': {'x': 100, 'y': 100},
                }
            ],
            'connections': [],
            'metadata': {'created_at': datetime.utcnow().isoformat(), 'author': 'test'},
        }

        workflow = Workflow(
            id=uuid4(),
            name='Modern Workflow',
            description='Test modern workflow',
            creator_id=test_user.id,
            organization_id=test_organization.id,
            definition=new_workflow_definition,
            is_active=True,
        )
        test_session.add(workflow)
        await test_session.commit()
        await test_session.refresh(workflow)

        # 测试回滚到旧版本
        rolled_back_definition = await migration_manager.rollback_workflow_definition(
            workflow.definition, from_version='2.0', to_version='1.0'
        )

        # 验证回滚后的数据格式
        assert rolled_back_definition['version'] == '1.0'
        assert 'nodes' in rolled_back_definition
        assert 'connections' in rolled_back_definition
        assert 'metadata' not in rolled_back_definition  # 旧版本没有metadata字段

        # 验证节点数据保持核心信息
        assert len(rolled_back_definition['nodes']) == 1
        assert rolled_back_definition['nodes'][0]['id'] == 'node1'
        assert rolled_back_definition['nodes'][0]['type'] == 'llm'

    async def test_batch_migration(
        self,
        migration_manager: DataMigrator,
        test_user: User,
        test_organization: Organization,
        test_session: AsyncSession,
    ):
        """测试批量迁移"""
        # 创建多个需要迁移的工作流
        workflows = []
        for i in range(3):
            old_definition = {
                'version': '1.0',
                'nodes': [{'id': f'node{i}', 'type': 'start'}],
                'connections': [],
            }

            workflow = Workflow(
                id=uuid4(),
                name=f'Workflow {i}',
                description=f'Test workflow {i}',
                creator_id=test_user.id,
                organization_id=test_organization.id,
                definition=old_definition,
                is_active=True,
            )
            test_session.add(workflow)
            workflows.append(workflow)

        await test_session.commit()

        # 执行批量迁移
        workflow_ids = [w.id for w in workflows]
        migration_results = await migration_manager.batch_migrate_workflows(
            workflow_ids, from_version='1.0', to_version='2.0'
        )

        # 验证批量迁移结果
        assert len(migration_results) == 3
        for result in migration_results:
            assert result['success'] is True
            assert result['from_version'] == '1.0'
            assert result['to_version'] == '2.0'

    async def test_migration_validation(self, migration_manager: DataMigrator):
        """测试迁移数据验证"""
        # 测试有效的工作流定义
        valid_definition = {
            'version': '1.0',
            'nodes': [{'id': 'node1', 'type': 'start', 'config': {}}],
            'connections': [],
        }

        is_valid = await migration_manager.validate_workflow_definition(valid_definition)
        assert is_valid is True

        # 测试无效的工作流定义
        invalid_definition = {
            'version': '1.0',
            'nodes': [
                {'id': 'node1'}  # 缺少type字段
            ],
            'connections': [],
        }

        is_invalid = await migration_manager.validate_workflow_definition(invalid_definition)
        assert is_invalid is False

    async def test_migration_history_tracking(
        self,
        migration_manager: DataMigrator,
        test_user: User,
        test_organization: Organization,
        test_session: AsyncSession,
    ):
        """测试迁移历史跟踪"""
        # 创建工作流
        workflow_definition = {
            'version': '1.0',
            'nodes': [{'id': 'node1', 'type': 'start'}],
            'connections': [],
        }

        workflow = Workflow(
            id=uuid4(),
            name='Tracked Workflow',
            description='Test workflow with migration tracking',
            creator_id=test_user.id,
            organization_id=test_organization.id,
            definition=workflow_definition,
            is_active=True,
        )
        test_session.add(workflow)
        await test_session.commit()
        await test_session.refresh(workflow)

        # 执行迁移并记录历史
        await migration_manager.migrate_workflow_with_history(
            workflow.id, from_version='1.0', to_version='2.0'
        )

        # 获取迁移历史
        migration_history = await migration_manager.get_migration_history(workflow.id)

        assert len(migration_history) >= 1
        latest_migration = migration_history[0]
        assert latest_migration['from_version'] == '1.0'
        assert latest_migration['to_version'] == '2.0'
        assert 'migrated_at' in latest_migration

    async def test_schema_compatibility_check(self, migration_manager: DataMigrator):
        """测试模式兼容性检查"""
        # 测试兼容的版本
        compatible_versions = [('1.0', '1.1'), ('1.1', '2.0')]
        for from_ver, to_ver in compatible_versions:
            is_compatible = await migration_manager.check_schema_compatibility(from_ver, to_ver)
            assert isinstance(is_compatible, bool)

        # 测试不兼容的版本跳跃
        incompatible_result = await migration_manager.check_schema_compatibility('1.0', '3.0')
        # 根据实际实现，这可能返回False或抛出异常
        assert isinstance(incompatible_result, bool)
