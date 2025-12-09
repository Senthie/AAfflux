"""测试数据库连接和配置

验证测试环境是否正确配置。
"""
import pytest
from sqlalchemy import text


class TestDatabaseSetup:
    """测试数据库设置"""

    @pytest.mark.asyncio
    async def test_database_connection(self, test_session):
        """测试数据库连接"""
        result = await test_session.execute(text('SELECT 1 as test'))
        assert result.fetchone()[0] == 1

    @pytest.mark.asyncio
    async def test_database_version(self, test_session):
        """测试 PostgreSQL 版本"""
        result = await test_session.execute(text('SELECT version()'))
        version = result.fetchone()[0]
        assert 'PostgreSQL' in version
        print(f"\nPostgreSQL 版本: {version.split(',')[0]}")

    @pytest.mark.asyncio
    async def test_database_name(self, test_session):
        """测试当前数据库名称"""
        result = await test_session.execute(text('SELECT current_database()'))
        db_name = result.fetchone()[0]
        assert db_name == 'lowcode_test'
        print(f"\n当前数据库: {db_name}")

    @pytest.mark.asyncio
    async def test_tables_exist(self, test_session):
        """测试表是否存在"""
        # 查询所有表
        result = await test_session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result.fetchall()]
        
        # 验证核心表存在
        expected_tables = [
            'users',
            'organizations',
            'teams',
            'workspaces',
            'applications',
            'workflows',
            'datasets',
            'conversations',
            'file_references',
        ]
        
        for table in expected_tables:
            assert table in tables, f"表 {table} 不存在"
        
        print(f"\n找到 {len(tables)} 个表")
        print(f"核心表验证通过: {', '.join(expected_tables)}")

    @pytest.mark.asyncio
    async def test_soft_delete_fields(self, test_session):
        """测试软删除字段是否存在"""
        # 检查 users 表的软删除字段
        result = await test_session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('deleted_at', 'is_deleted')
        """))
        
        columns = [row[0] for row in result.fetchall()]
        
        assert 'deleted_at' in columns, "users 表缺少 deleted_at 字段"
        assert 'is_deleted' in columns, "users 表缺少 is_deleted 字段"
        
        print("\n✅ 软删除字段验证通过")

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, test_session):
        """测试事务回滚功能"""
        from app.models.auth.user import User
        from uuid import uuid4
        
        # 创建测试用户
        test_user = User(
            id=uuid4(),
            name='Test Rollback User',
            email='rollback@test.com',
            password_hash='test_hash',
        )
        
        test_session.add(test_user)
        await test_session.commit()
        
        # 查询用户
        result = await test_session.execute(
            text("SELECT name FROM users WHERE email = 'rollback@test.com'")
        )
        user = result.fetchone()
        
        assert user is not None
        assert user[0] == 'Test Rollback User'
        
        print("\n✅ 事务功能正常")


class TestEnvironmentConfig:
    """测试环境配置"""

    def test_test_environment_loaded(self):
        """测试是否加载了测试环境配置"""
        import os
        
        database_url = os.getenv('DATABASE_URL', '')
        assert 'lowcode_test' in database_url, "未使用测试数据库"
        
        print(f"\n✅ 测试环境配置正确")
        print(f"   数据库: {database_url}")

    def test_settings_isolation(self):
        """测试配置隔离"""
        from app.core.config import settings
        
        # 测试环境应该使用测试数据库
        assert 'lowcode_test' in settings.database_url
        
        print(f"\n✅ 配置隔离正确")
        print(f"   App Name: {settings.app_name}")
        print(f"   Database: {settings.database_url}")
