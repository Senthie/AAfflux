# SQLModel vs SQLAlchemy - 为什么同时使用？

## 简单回答

**SQLModel = SQLAlchemy + Pydantic**

- **SQLModel** 用于定义模型（更简洁、更现代）
- **SQLAlchemy** 提供底层引擎和会话管理（更强大、更灵活）

## 详细说明

### 1. SQLModel 的优势

#### 传统 SQLAlchemy 方式（繁琐）

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

# 还需要单独定义 Pydantic Schema 用于 API
from pydantic import BaseModel

class UserSchema(BaseModel):
    id: int
    email: str
    name: str
```

#### SQLModel 方式（简洁）

```python
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    email: str = Field(unique=True)
    name: str

# 同一个类既是 ORM 模型，也是 Pydantic Schema！
```

### 2. 为什么还需要 SQLAlchemy？

SQLModel **内部使用** SQLAlchemy，但某些功能需要直接使用 SQLAlchemy：

#### 异步支持

```python
# 需要 SQLAlchemy 的异步模块
from sqlalchemy.ext.asyncio import (
    AsyncSession,           # 异步会话
    create_async_engine,    # 异步引擎
    async_sessionmaker      # 异步会话工厂
)

# SQLModel 目前不直接提供这些
engine = create_async_engine("postgresql+asyncpg://...")
```

#### 高级查询

```python
from sqlalchemy import select, func
from sqlmodel import Session

# 复杂查询需要 SQLAlchemy 的查询构建器
async def get_user_count(session: AsyncSession):
    statement = select(func.count(User.id))
    result = await session.execute(statement)
    return result.scalar()
```

#### 连接池和事务管理

```python
# SQLAlchemy 提供强大的连接池配置
engine = create_async_engine(
    url,
    pool_size=5,              # SQLAlchemy 功能
    max_overflow=10,          # SQLAlchemy 功能
    pool_pre_ping=True,       # SQLAlchemy 功能
)
```

### 3. 在我们的项目中如何使用

#### 定义模型（使用 SQLModel）

```python
# app/models/user.py
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4

class User(SQLModel, table=True):
    """用户模型 - 简洁的定义"""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    
    # 自动获得：
    # - 数据验证（Pydantic）
    # - 类型提示
    # - JSON 序列化
    # - ORM 功能
```

#### 数据库操作（使用 SQLAlchemy 会话）

```python
# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

async def get_user_by_email(session: AsyncSession, email: str):
    """使用 SQLAlchemy 会话查询 SQLModel 模型"""
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    return result.scalar_one_or_none()
```

#### 数据库连接（使用 SQLAlchemy 引擎）

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# SQLAlchemy 创建引擎
engine = create_async_engine(url, pool_size=5)

# SQLModel 创建表
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
```

## 对比表格

| 功能 | SQLModel | SQLAlchemy | 说明 |
|------|----------|------------|------|
| 模型定义 | ✅ 推荐 | ⚠️ 繁琐 | SQLModel 更简洁 |
| 数据验证 | ✅ 内置 | ❌ 需要 Pydantic | SQLModel = SQLAlchemy + Pydantic |
| 类型提示 | ✅ 原生支持 | ⚠️ 需要额外配置 | SQLModel 使用 Python 类型提示 |
| 异步支持 | ⚠️ 依赖 SQLAlchemy | ✅ 完整支持 | 需要 `sqlalchemy.ext.asyncio` |
| 连接池 | ❌ 不提供 | ✅ 完整支持 | 需要 SQLAlchemy 引擎 |
| 复杂查询 | ⚠️ 基础功能 | ✅ 强大 | 复杂查询用 SQLAlchemy |
| 事务管理 | ⚠️ 依赖 SQLAlchemy | ✅ 完整支持 | 需要 SQLAlchemy 会话 |
| API Schema | ✅ 自动 | ❌ 需要单独定义 | SQLModel 一举两得 |

## 最佳实践

### ✅ 推荐做法

```python
# 1. 使用 SQLModel 定义模型
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    email: str

# 2. 使用 SQLAlchemy 管理连接
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(url)

# 3. 使用 SQLAlchemy 会话进行查询
async def get_user(session: AsyncSession, user_id: int):
    return await session.get(User, user_id)
```

### ❌ 不推荐

```python
# 不要混用 SQLAlchemy 的 declarative_base
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()  # ❌ 不需要，用 SQLModel

class User(Base):  # ❌ 应该继承 SQLModel
    __tablename__ = "users"
    ...
```

## 总结

1. **SQLModel** = 更好的开发体验
   - 简洁的模型定义
   - 自动数据验证
   - 类型安全
   - 一个类同时作为 ORM 和 Schema

2. **SQLAlchemy** = 强大的底层支持
   - 异步数据库操作
   - 连接池管理
   - 复杂查询构建
   - 事务管理

3. **两者配合** = 最佳实践
   - 用 SQLModel 定义模型（简洁）
   - 用 SQLAlchemy 管理连接和会话（强大）
   - 享受两者的优势！

## 参考资料

- [SQLModel 官方文档](https://sqlmodel.tiangolo.com/)
- [SQLAlchemy 官方文档](https://docs.sqlalchemy.org/)
- [FastAPI + SQLModel 教程](https://sqlmodel.tiangolo.com/tutorial/fastapi/)
