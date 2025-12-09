# 测试环境配置指南

## 📋 概述

本项目使用 PostgreSQL 作为测试数据库，与生产环境保持一致，确保测试的准确性。

## 🚀 快速开始

### 1. 初始化测试数据库

```bash
cd api
python setup_test_database.py
```

这个脚本会：
- ✅ 创建 `lowcode_test` 数据库
- ✅ 运行所有数据库迁移
- ✅ 验证数据库连接

### 2. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_database_setup.py -v

# 运行特定测试类
pytest tests/test_database_setup.py::TestDatabaseSetup -v

# 运行特定测试方法
pytest tests/test_database_setup.py::TestDatabaseSetup::test_database_connection -v

# 显示打印输出
pytest tests/ -v -s

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

## 🔧 配置说明

### 环境配置文件

- `.env` - 开发环境配置
- `.env.test` - 测试环境配置（使用独立的测试数据库）

### 测试数据库配置

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:postgres@14.12.0.102:5432/lowcode_test

# MongoDB
MONGODB_DATABASE=lowcode_test

# Redis
REDIS_DB=1  # 使用不同的 Redis DB
```

## 📁 测试文件结构

```
tests/
├── README.md                      # 本文件
├── conftest.py                    # Pytest 配置和 fixtures
├── test_database_setup.py         # 数据库设置测试
├── test_infrastructure.py         # 基础设施测试
├── test_workflow_*.py            # 工作流测试
│
├── test_auth/                     # 认证模块测试
│   ├── test_user_crud.py
│   └── test_auth_service.py
│
├── test_tenant/                   # 租户模块测试
│   ├── test_organization_crud.py
│   ├── test_team_crud.py
│   └── test_workspace_crud.py
│
├── test_application/              # 应用模块测试
├── test_workflow/                 # 工作流模块测试
├── test_bpm/                      # BPM 模块测试
├── test_dataset/                  # 数据集模块测试
├── test_conversation/             # 对话模块测试
├── test_file/                     # 文件模块测试
└── test_plugin/                   # 插件模块测试
```

## 🧪 Fixtures 说明

### `test_engine`
- **作用域**: session
- **说明**: 创建测试数据库引擎，整个测试会话共享

### `setup_test_database`
- **作用域**: session
- **说明**: 在测试会话开始时创建所有表，结束时清理

### `test_session`
- **作用域**: function
- **说明**: 为每个测试函数创建独立的数据库会话
- **特性**: 使用事务，测试结束后自动回滚，确保测试隔离

### `clean_database`
- **作用域**: function
- **说明**: 清空所有表数据
- **使用场景**: 需要完全清空数据库的测试

## 📝 编写测试示例

### 基础 CRUD 测试

```python
import pytest
from uuid import uuid4
from app.models.auth.user import User


class TestUserCRUD:
    """用户 CRUD 测试"""

    @pytest.mark.asyncio
    async def test_create_user(self, test_session):
        """测试创建用户"""
        user = User(
            id=uuid4(),
            username='testuser',
            email='test@example.com',
            hashed_password='hashed_password',
            full_name='Test User',
        )
        
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        
        assert user.id is not None
        assert user.username == 'testuser'

    @pytest.mark.asyncio
    async def test_read_user(self, test_session):
        """测试读取用户"""
        # 创建用户
        user = User(
            id=uuid4(),
            username='readuser',
            email='read@example.com',
            hashed_password='hashed_password',
            full_name='Read User',
        )
        test_session.add(user)
        await test_session.commit()
        
        # 读取用户
        from sqlalchemy import select
        result = await test_session.execute(
            select(User).where(User.username == 'readuser')
        )
        found_user = result.scalar_one_or_none()
        
        assert found_user is not None
        assert found_user.email == 'read@example.com'

    @pytest.mark.asyncio
    async def test_update_user(self, test_session):
        """测试更新用户"""
        # 创建用户
        user = User(
            id=uuid4(),
            username='updateuser',
            email='update@example.com',
            hashed_password='hashed_password',
            full_name='Update User',
        )
        test_session.add(user)
        await test_session.commit()
        
        # 更新用户
        user.full_name = 'Updated User'
        await test_session.commit()
        await test_session.refresh(user)
        
        assert user.full_name == 'Updated User'

    @pytest.mark.asyncio
    async def test_soft_delete_user(self, test_session):
        """测试软删除用户"""
        # 创建用户
        user = User(
            id=uuid4(),
            username='deleteuser',
            email='delete@example.com',
            hashed_password='hashed_password',
            full_name='Delete User',
        )
        test_session.add(user)
        await test_session.commit()
        
        # 软删除
        user.soft_delete()
        await test_session.commit()
        await test_session.refresh(user)
        
        assert user.is_deleted is True
        assert user.deleted_at is not None
```

### API 端点测试

```python
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_create_user_api():
    """测试创建用户 API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/users",
            json={
                "username": "apiuser",
                "email": "api@example.com",
                "password": "password123",
                "full_name": "API User",
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "apiuser"
```

## 🔍 调试技巧

### 1. 查看测试输出
```bash
pytest tests/ -v -s
```

### 2. 只运行失败的测试
```bash
pytest tests/ --lf
```

### 3. 进入调试模式
```bash
pytest tests/ --pdb
```

### 4. 查看测试覆盖率
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

## ⚠️ 注意事项

1. **数据隔离**: 每个测试使用独立事务，测试结束后自动回滚
2. **测试数据库**: 使用独立的 `lowcode_test` 数据库，不影响开发数据
3. **并发测试**: 避免在测试中使用固定的 ID 或唯一值
4. **清理数据**: 使用 `clean_database` fixture 清空数据
5. **异步测试**: 所有数据库操作测试需要使用 `@pytest.mark.asyncio`

## 🐛 常见问题

### Q: 测试数据库连接失败？
A: 检查 `.env.test` 中的数据库配置是否正确，确保数据库服务正在运行。

### Q: 表不存在错误？
A: 运行 `python setup_test_database.py` 初始化测试数据库。

### Q: 测试之间数据污染？
A: 确保使用 `test_session` fixture，它会自动回滚事务。

### Q: 如何重置测试数据库？
A: 运行 `python setup_test_database.py` 并选择删除重建。

## 📚 参考资料

- [Pytest 文档](https://docs.pytest.org/)
- [SQLAlchemy 异步文档](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI 测试文档](https://fastapi.tiangolo.com/tutorial/testing/)
