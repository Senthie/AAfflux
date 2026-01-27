"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/clean_test_database.py
Description: 数据库连接管理

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

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
