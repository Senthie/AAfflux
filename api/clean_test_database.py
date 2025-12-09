"""清空测试数据库"""
from sqlalchemy import create_engine, text

DB_URL = 'postgresql://postgres:postgres@14.12.0.102:5432/lowcode_test'

engine = create_engine(DB_URL)

with engine.connect() as conn:
    # 清空所有表
    conn.execute(text('TRUNCATE TABLE users CASCADE'))
    conn.commit()
    print('✅ 测试数据已清空')

engine.dispose()
