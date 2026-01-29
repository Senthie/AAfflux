# 数据库配置说明

## 概述

本项目已配置为连接到部署在 `14.12.0.102` 服务器上的数据库服务。

> **重要提示**: Alembic 现在会自动从 `.env` 文件读取数据库配置，无需手动设置环境变量！

## 数据库服务

### PostgreSQL (主数据库)

- **地址**: `14.12.0.102:5432`
- **数据库**: `lowcode_platform`
- **用户**: `postgres`
- **用途**: 存储结构化数据（用户、工作流、执行记录等）

### MongoDB (文档数据库)

- **地址**: `14.12.0.102:27017`
- **数据库**: `lowcode_platform`
- **用途**: 存储文件和非结构化数据

### Redis (缓存和消息队列)

- **地址**: `14.12.0.102:6379`
- **数据库**: `0`
- **用途**: 缓存、会话存储、Celery 消息队列

## 配置文件

### 环境变量 (.env)

```bash
# PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:postgres@14.12.0.102:5432/lowcode_platform

# MongoDB
MONGODB_URL=mongodb://14.12.0.102:27017
MONGODB_DATABASE=lowcode_platform

# Redis
REDIS_URL=redis://14.12.0.102:6379
REDIS_DB=0
```

## 数据库迁移

### 运行迁移

```bash
# 直接运行迁移（会自动从 .env 文件读取配置）
alembic upgrade head

# 查看当前迁移状态
alembic current

# 查看迁移历史
alembic history
```

### 创建新迁移

```bash
# 自动生成迁移（需要数据库连接）
alembic revision --autogenerate -m "描述迁移内容"

# 手动创建迁移
alembic revision -m "描述迁移内容"
```

## 快速设置

### 一键设置数据库

```bash
# 运行完整的数据库设置流程
python setup_database.py
```

这个脚本会：

1. 自动加载 `.env` 文件中的配置
2. 验证所有必需的环境变量
3. 运行数据库迁移
4. 显示下一步操作指南

## 验证连接

### 快速验证配置

```bash
python verify_config.py
```

### 测试数据库连接

```bash
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import text

async def test():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@14.12.0.102:5432/lowcode_platform')
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT version()'))
        print('✅ PostgreSQL连接成功:', result.fetchone()[0])
    await engine.dispose()

asyncio.run(test())
"
```

## 数据库表结构

当前已创建的表：

- `user` - 用户信息
- `organization` - 企业组织
- `team` - 团队
- `teammember` - 团队成员
- `workspace` - 工作空间
- `workflow` - 工作流
- `node` - 工作流节点
- `connection` - 节点连接
- `executionrecord` - 执行记录
- `nodeexecutionresult` - 节点执行结果
- `prompttemplate` - 提示词模板
- `prompttemplateversion` - 模板版本
- `llmprovider` - LLM 提供商
- `application` - 应用
- `filereference` - 文件引用

## 注意事项

1. **安全性**: 生产环境中请更改默认密码
2. **备份**: 定期备份数据库数据
3. **监控**: 监控数据库性能和连接状态
4. **网络**: 确保应用服务器能访问数据库服务器的相应端口

## 故障排除

### 连接失败

1. 检查网络连接：`ping 14.12.0.102`
2. 检查端口开放：`telnet 14.12.0.102 5432`
3. 验证凭据和数据库名称
4. 检查防火墙设置

### 迁移失败

1. 确保数据库存在
2. 检查用户权限
3. 验证迁移文件语法
4. 查看详细错误日志

### 性能问题

1. 检查连接池配置
2. 监控数据库负载
3. 优化查询和索引
4. 考虑读写分离
