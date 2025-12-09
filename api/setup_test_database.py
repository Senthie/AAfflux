"""初始化测试数据库

创建测试数据库并运行迁移。
"""
import asyncio
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

# 加载测试环境配置
load_dotenv('.env.test')

# 数据库配置
DB_HOST = '14.12.0.102'
DB_PORT = '5432'
DB_USER = 'postgres'
DB_PASSWORD = 'postgres'
DB_NAME = 'lowcode_test'

# 管理员连接 URL（连接到 postgres 数据库）
ADMIN_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres'

# 测试数据库 URL
TEST_DB_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
TEST_DB_URL_ASYNC = f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


def create_test_database():
    """创建测试数据库"""
    print(f"正在创建测试数据库: {DB_NAME}")
    
    # 连接到 postgres 数据库
    engine = create_engine(ADMIN_URL, isolation_level='AUTOCOMMIT')
    
    with engine.connect() as conn:
        # 检查数据库是否存在
        result = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        )
        exists = result.fetchone() is not None
        
        if exists:
            print(f"⚠️  数据库 {DB_NAME} 已存在")
            
            # 询问是否删除重建
            response = input("是否删除并重建? (y/N): ").strip().lower()
            if response == 'y':
                # 断开所有连接
                conn.execute(text(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{DB_NAME}'
                    AND pid <> pg_backend_pid()
                """))
                
                # 删除数据库
                conn.execute(text(f'DROP DATABASE {DB_NAME}'))
                print(f"✅ 已删除数据库 {DB_NAME}")
                
                # 创建数据库
                conn.execute(text(f'CREATE DATABASE {DB_NAME} OWNER {DB_USER}'))
                print(f"✅ 已创建数据库 {DB_NAME}")
            else:
                print("跳过数据库创建")
        else:
            # 创建数据库
            conn.execute(text(f'CREATE DATABASE {DB_NAME} OWNER {DB_USER}'))
            print(f"✅ 已创建数据库 {DB_NAME}")
    
    engine.dispose()


async def verify_connection():
    """验证数据库连接"""
    print(f"\n正在验证数据库连接...")
    
    try:
        engine = create_async_engine(TEST_DB_URL_ASYNC)
        
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT version()'))
            version = result.fetchone()[0]
            print(f"✅ 数据库连接成功!")
            print(f"   PostgreSQL 版本: {version.split(',')[0]}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def run_migrations():
    """运行数据库迁移"""
    print(f"\n正在运行数据库迁移...")
    
    # 设置环境变量
    os.environ['DATABASE_URL'] = TEST_DB_URL_ASYNC
    
    # 运行 alembic 迁移
    import subprocess
    
    try:
        result = subprocess.run(
            ['alembic', 'upgrade', 'head'],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ 数据库迁移完成")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 数据库迁移失败: {e}")
        print(e.stderr)
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("测试数据库初始化")
    print("=" * 60)
    
    # 1. 创建数据库
    try:
        create_test_database()
    except Exception as e:
        print(f"❌ 创建数据库失败: {e}")
        sys.exit(1)
    
    # 2. 验证连接
    if not await verify_connection():
        sys.exit(1)
    
    # 3. 运行迁移
    if not run_migrations():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ 测试数据库初始化完成!")
    print("=" * 60)
    print(f"\n测试数据库 URL: {TEST_DB_URL_ASYNC}")
    print(f"\n现在可以运行测试:")
    print(f"  pytest tests/ -v")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
