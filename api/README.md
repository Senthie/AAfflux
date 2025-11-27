# Low-Code Platform Backend

类似 Dify 的低代码平台后端，支持工作流编排、AI 集成和多租户架构。

## 功能特性

- 🚀 **FastAPI** - 高性能异步 Web 框架
- 🗄️ **多数据库支持** - PostgreSQL (主数据库) + MongoDB (文件存储) + Redis (缓存)
- 🔐 **JWT 认证** - 安全的用户认证和授权
- 👥 **多租户架构** - 企业 → 团队 → 工作空间三层隔离
- 🔄 **工作流引擎** - 基于 DAG 的可视化工作流编排
- 🤖 **AI 集成** - 支持多种 LLM 提供商 (OpenAI, Anthropic 等)
- 📝 **结构化日志** - 使用 structlog 进行日志记录
- 📊 **错误追踪** - Sentry 集成
- ⚡ **异步任务** - Celery 任务队列

## 技术栈

- **Python 3.12+**
- **FastAPI** - Web 框架
- **SQLModel** - ORM (SQLAlchemy + Pydantic)
- **PostgreSQL** - 主数据库
- **MongoDB** - 文件存储 (支持 GridFS)
- **Redis** - 缓存和会话
- **Celery** - 异步任务队列
- **Alembic** - 数据库迁移
- **Structlog** - 结构化日志
- **Sentry** - 错误追踪

## 项目结构

```
app/
├── api/              # API 路由
│   └── v1/          # API v1 端点
├── core/            # 核心配置
│   ├── config.py    # 应用配置
│   ├── database.py  # PostgreSQL 连接
│   ├── mongodb.py   # MongoDB 连接
│   ├── redis.py     # Redis 连接
│   ├── logging.py   # 日志配置
│   ├── sentry.py    # Sentry 配置
│   └── celery.py    # Celery 配置
├── models/          # 数据模型 (SQLModel)
├── schemas/         # Pydantic schemas
├── services/        # 业务逻辑层
├── repositories/    # 数据访问层
├── middleware/      # 中间件
├── engine/          # 工作流引擎
│   └── nodes/      # 节点类型实现
├── tasks/           # Celery 任务
├── utils/           # 工具函数
│   └── llm/        # LLM 客户端
└── main.py          # 应用入口
```

## 快速开始

### 前置要求

- Python 3.12+
- PostgreSQL 14+
- MongoDB 6+
- Redis 7+
- uv (Python 包管理器)

### 安装

1. 克隆仓库

```bash
git clone <repository-url>
cd low-code-platform-backend
```

2. 安装依赖

```bash
# 安装生产依赖
uv sync

# 安装开发依赖
uv sync --extra dev
```

3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等信息
```

4. 初始化数据库

```bash
# 运行数据库迁移
uv run alembic upgrade head
```

### 运行

#### 开发模式

```bash
# 启动 API 服务器
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动 Celery worker (另一个终端)
uv run celery -A app.core.celery worker --loglevel=info
```

#### 生产模式

```bash
# 使用 gunicorn + uvicorn workers
uv run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 使用 Docker Compose

```bash
# 启动所有服务 (API, PostgreSQL, MongoDB, Redis)
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

## 开发

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_infrastructure.py

# 运行测试并显示覆盖率
uv run pytest --cov=app --cov-report=html
```

### 代码格式化

```bash
# 格式化代码
uv run black app tests

# 检查代码风格
uv run ruff check app tests

# 类型检查
uv run mypy app
```

### 数据库迁移

```bash
# 创建新迁移
uv run alembic revision --autogenerate -m "描述"

# 应用迁移
uv run alembic upgrade head

# 回滚迁移
uv run alembic downgrade -1
```

## API 文档

启动服务器后，访问以下地址查看 API 文档：

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

## 环境变量

主要环境变量说明（详见 `.env.example`）：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接 URL | - |
| `MONGODB_URL` | MongoDB 连接 URL | - |
| `REDIS_URL` | Redis 连接 URL | - |
| `JWT_SECRET_KEY` | JWT 密钥 (至少 32 字符) | - |
| `SENTRY_DSN` | Sentry DSN (可选) | - |
| `LOG_LEVEL` | 日志级别 | INFO |
| `LOG_FORMAT` | 日志格式 (json/console) | json |

## 架构设计

### 多租户架构

系统采用三层租户隔离模型：

```
企业 (Organization)
  └── 团队 (Team)
        └── 工作空间 (Workspace)
              ├── 工作流 (Workflow)
              ├── 应用 (Application)
              ├── 模板 (Template)
              └── LLM 配置 (Provider)
```

- **企业级**: 顶层组织，可包含多个团队
- **团队级**: 协作单位，可包含多个工作空间
- **工作空间级**: 资源隔离单元，所有资源按工作空间隔离

### 工作流引擎

- 基于 DAG (有向无环图) 的工作流编排
- 支持多种节点类型：LLM、条件判断、代码执行、HTTP 请求、数据转换
- 拓扑排序执行，支持并行执行
- 异步执行支持 (Celery)

### 权限控制

基于角色的访问控制 (RBAC)：

- **管理员**: 完全权限 (CRUD)
- **成员**: 创建和读取权限
- **访客**: 只读权限

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

[MIT License](LICENSE)

## 联系方式

- 项目链接: [GitHub Repository]
- 问题反馈: [GitHub Issues]
