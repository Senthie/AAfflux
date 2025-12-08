"""检查数据库表"""

import asyncio
from sqlalchemy import text
from app.core.database import engine


async def check_tables():
    async with engine.begin() as conn:
        # 获取所有表名
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
            )
        )
        tables = [row[0] for row in result]

        print(f'\n数据库中共有 {len(tables)} 张表:\n')
        for table in tables:
            print(f'  ✓ {table}')

        # 检查是否有 alembic_version 表
        if 'alembic_version' in tables:
            result = await conn.execute(text('SELECT version_num FROM alembic_version'))
            version = result.scalar()
            print(f'\n当前迁移版本: {version}')


if __name__ == '__main__':
    asyncio.run(check_tables())
