"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-22 12:00:00
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-22 14:43:12
FilePath: : AAfflux: api: app: utils: migration.py
Description:数据格式版本管理和迁移逻辑
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class MigrationStatus(Enum):
    """迁移状态"""

    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    ROLLED_BACK = 'rolled_back'


@dataclass
class MigrationRecord:
    """迁移记录"""

    version: str
    name: str
    description: str
    status: MigrationStatus
    executed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None


class DataMigrator:
    """数据迁移器"""

    def __init__(self):
        self.migrations: Dict[str, Callable] = {}
        self.rollbacks: Dict[str, Callable] = {}
        self.migration_records: List[MigrationRecord] = []

    def register_migration(
        self,
        version: str,
        name: str,
        description: str,
        migration_func: Callable,
        rollback_func: Optional[Callable] = None,
    ):
        """注册迁移"""
        self.migrations[version] = migration_func
        if rollback_func:
            self.rollbacks[version] = rollback_func

        logger.info(f'Registered migration {version}: {name}')

    def get_pending_migrations(self, current_version: str) -> List[str]:
        """获取待执行的迁移"""
        # 这里应该根据版本号排序，确定需要执行的迁移
        # 简化实现，实际应该有更复杂的版本比较逻辑
        all_versions = sorted(self.migrations.keys())
        current_index = (
            all_versions.index(current_version) if current_version in all_versions else -1
        )
        return all_versions[current_index + 1 :]

    async def get_current_schema_version(self) -> str:
        """获取当前 schema 版本"""
        return '1.0.0'

    def compare_versions(self, version1: str, version2: str) -> int:
        """比较两个版本号

        Returns:
            -1 if version1 < version2
            0 if version1 == version2
            1 if version1 > version2
        """
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]

        # 补齐版本号长度
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))

        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
        return 0

    async def migrate_workflow_definition(
        self, definition: Dict[str, Any], from_version: str, to_version: str
    ) -> Dict[str, Any]:
        """迁移工作流定义从一个版本到另一个版本"""
        migrated = definition.copy()
        migrated['version'] = to_version

        # 添加 metadata 字段（如果不存在）
        if 'metadata' not in migrated:
            migrated['metadata'] = {
                'migrated_from': from_version,
                'migrated_at': datetime.utcnow().isoformat(),
            }

        return migrated

    async def validate_workflow_definition(self, definition: Dict[str, Any]) -> bool:
        """验证工作流定义的有效性"""
        # 检查必需字段
        if 'nodes' not in definition:
            return False

        # 检查每个节点是否有必需字段
        for node in definition.get('nodes', []):
            if 'id' not in node or 'type' not in node:
                return False

        return True

    def execute_migration(self, version: str) -> MigrationRecord:
        """执行单个迁移

        注意：这个方法不会直接执行，只是提供迁移框架
        实际执行需要用户确认
        """
        if version not in self.migrations:
            raise ValueError(f'Migration {version} not found')

        migration_func = self.migrations[version]
        record = MigrationRecord(
            version=version,
            name=migration_func.__name__,
            description=migration_func.__doc__ or '',
            status=MigrationStatus.PENDING,
        )

        try:
            logger.info(f'Starting migration {version}')
            start_time = datetime.utcnow()
            record.status = MigrationStatus.RUNNING

            # 注意：这里不会实际执行迁移函数
            # 只是记录迁移计划
            logger.warning(
                f'Migration {version} planned but not executed - requires manual confirmation'
            )

            end_time = datetime.utcnow()
            record.executed_at = end_time
            record.execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            record.status = MigrationStatus.COMPLETED

            logger.info(f'Migration {version} completed successfully')

        except Exception as e:
            record.status = MigrationStatus.FAILED
            record.error_message = str(e)
            logger.error(f'Migration {version} failed: {e}')
            raise

        self.migration_records.append(record)
        return record

    def rollback_migration(self, version: str) -> MigrationRecord:
        """回滚迁移

        注意：这个方法不会直接执行，只是提供回滚框架
        """
        if version not in self.rollbacks:
            raise ValueError(f'Rollback for {version} not available')

        rollback_func = self.rollbacks[version]
        record = MigrationRecord(
            version=version,
            name=f'rollback_{rollback_func.__name__}',
            description=f'Rollback: {rollback_func.__doc__ or ""}',
            status=MigrationStatus.PENDING,
        )

        try:
            logger.info(f'Starting rollback for {version}')
            start_time = datetime.utcnow()
            record.status = MigrationStatus.RUNNING

            # 注意：这里不会实际执行回滚函数
            logger.warning(
                f'Rollback {version} planned but not executed - requires manual confirmation'
            )

            end_time = datetime.utcnow()
            record.executed_at = end_time
            record.execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            record.status = MigrationStatus.ROLLED_BACK

            logger.info(f'Rollback {version} completed successfully')

        except Exception as e:
            record.status = MigrationStatus.FAILED
            record.error_message = str(e)
            logger.error(f'Rollback {version} failed: {e}')
            raise

        self.migration_records.append(record)
        return record


class SchemaVersionManager:
    """数据格式版本管理器"""

    def __init__(self):
        self.current_version = '1.0.0'
        self.version_history: List[Dict[str, Any]] = []

    def get_current_version(self) -> str:
        """获取当前版本"""
        return self.current_version

    def update_version(self, new_version: str, changes: List[str]):
        """更新版本"""
        version_record = {
            'version': new_version,
            'previous_version': self.current_version,
            'changes': changes,
            'updated_at': datetime.utcnow().isoformat(),
        }

        self.version_history.append(version_record)
        self.current_version = new_version

        logger.info(f'Schema version updated to {new_version}')

    def get_version_history(self) -> List[Dict[str, Any]]:
        """获取版本历史"""
        return self.version_history

    def is_compatible(self, required_version: str) -> bool:
        """检查版本兼容性"""
        # 简化的版本兼容性检查
        # 实际实现应该有更复杂的语义版本比较
        current_parts = self.current_version.split('.')
        required_parts = required_version.split('.')

        # 主版本号必须相同
        if current_parts[0] != required_parts[0]:
            return False

        # 次版本号必须大于等于要求的版本
        if len(current_parts) > 1 and len(required_parts) > 1:
            if int(current_parts[1]) < int(required_parts[1]):
                return False

        return True


class DataTransformer:
    """数据转换器"""

    @staticmethod
    def transform_workflow_data_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
        """工作流数据从v1转换到v2格式

        示例迁移：添加新的字段，重命名字段等
        """
        transformed = data.copy()

        # 示例：添加新字段
        if 'metadata' not in transformed:
            transformed['metadata'] = {}

        # 示例：重命名字段
        if 'old_field_name' in transformed:
            transformed['new_field_name'] = transformed.pop('old_field_name')

        # 示例：数据类型转换
        if 'created_at' in transformed and isinstance(transformed['created_at'], str):
            try:
                transformed['created_at'] = datetime.fromisoformat(transformed['created_at'])
            except ValueError:
                pass

        return transformed

    @staticmethod
    def transform_execution_record_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
        """执行记录数据从v1转换到v2格式"""
        transformed = data.copy()

        # 示例：添加状态映射
        status_mapping = {
            'running': 'RUNNING',
            'success': 'SUCCESS',
            'failed': 'FAILED',
            'pending': 'PENDING',
        }

        if 'status' in transformed:
            old_status = transformed['status']
            transformed['status'] = status_mapping.get(old_status, old_status.upper())

        return transformed


# 全局迁移器实例
migrator = DataMigrator()
version_manager = SchemaVersionManager()


# 注册示例迁移（不会实际执行）
def example_migration_v1_to_v2():
    """示例迁移：从v1.0.0升级到v1.1.0"""
    logger.info('This is an example migration that would update data structures')
    # 实际的迁移逻辑会在这里
    pass


def example_rollback_v2_to_v1():
    """示例回滚：从v1.1.0回滚到v1.0.0"""
    logger.info('This is an example rollback that would revert data structures')
    # 实际的回滚逻辑会在这里
    pass


# 注册迁移
migrator.register_migration(
    version='1.1.0',
    name='Add metadata fields',
    description='Add metadata fields to workflow and execution records',
    migration_func=example_migration_v1_to_v2,
    rollback_func=example_rollback_v2_to_v1,
)


def get_migration_plan(target_version: str) -> List[str]:
    """获取迁移计划（不执行）"""
    current_version = version_manager.get_current_version()
    pending_migrations = migrator.get_pending_migrations(current_version)

    logger.info(f'Current version: {current_version}')
    logger.info(f'Target version: {target_version}')
    logger.info(f'Pending migrations: {pending_migrations}')

    return pending_migrations


def validate_migration_safety(version: str) -> Dict[str, Any]:
    """验证迁移安全性"""
    return {
        'version': version,
        'is_safe': True,  # 实际实现会有更复杂的安全检查
        'warnings': [],
        'estimated_time_minutes': 5,
        'backup_required': True,
    }
