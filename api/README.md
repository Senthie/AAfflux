# Low-Code Platform Backend

一个基于FastAPI的低代码平台后端，支持工作流编排、AI集成和多租户管理。

## 🚀 功能特性

### 核心功能

- **用户认证与授权** - JWT令牌认证，基于角色的权限控制
- **多租户管理** - 组织、团队、工作空间的层级管理
- **工作流引擎** - 可视化DAG工作流编排和执行
- **AI集成** - 支持多种LLM提供商（OpenAI、Anthropic等）
- **应用发布** - 将工作流发布为API服务
- **文件存储** - 基于GridFS的大文件存储
- **执行记录** - 完整的工作流执行历史和统计

### 技术特性

- **异步架构** - 基于FastAPI和SQLModel的现代异步架构
- **数据库支持** - PostgreSQL主数据库 + MongoDB文件存储
- **缓存系统** - Redis缓存提升性能
- **任务队列** - Celery异步任务处理
- **监控日志** - 结构化日志和Sentry错误追踪
- **API文档** - 自动生成的OpenAPI文档

## 📋 系统要求

- Python 3.11+
- PostgreSQL 13+
- MongoDB 5.0+
- Redis 6.0+

## 🛠️ 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd api

# 安装uv包管理器
pip install uv

# 安装依赖
uv sync
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

### 3. 数据库初始化

```bash
# 启动数据库服务（使用Docker）
docker-compose up -d postgres mongodb redis

# 运行数据库迁移
uv run alembic upgrade head
```

### 4. 启动服务

```bash
# 开发模式启动
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用脚本启动
uv run python main.py
```

### 5. 访问服务

- API文档: <http://localhost:8000/docs>
- 健康检查: <http://localhost:8000/health>
- API根路径: <http://localhost:8000/api/v1>

## 🐳 Docker部署

### 开发环境

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

### 生产环境

```bash
# 使用生产配置
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 扩展API服务
docker-compose up -d --scale api=3
```

## 📚 API文档

### 认证接口

- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新令牌
- `POST /api/v1/auth/logout` - 用户登出

### 用户管理

- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新用户信息
- `POST /api/v1/users/me/password` - 修改密码

### 组织管理

- `GET /api/v1/organizations` - 获取组织列表
- `POST /api/v1/organizations` - 创建组织
- `GET /api/v1/organizations/{id}` - 获取组织详情

### 工作流管理

- `GET /api/v1/workflows` - 获取工作流列表
- `POST /api/v1/workflows` - 创建工作流
- `POST /api/v1/workflows/{id}/execute` - 执行工作流

### 应用管理

- `GET /api/v1/applications` - 获取应用列表
- `POST /api/v1/applications` - 创建应用
- `POST /api/v1/applications/{id}/publish` - 发布应用

### 执行记录

- `GET /api/v1/executions` - 获取执行记录
- `GET /api/v1/executions/{id}` - 获取执行详情
- `GET /api/v1/executions/statistics` - 获取执行统计

## 🔧 开发指南

### 项目结构

```
api/
├── app/
│   ├── api/                 # API路由
│   │   └── v1/             # API v1版本
│   ├── core/               # 核心配置
│   ├── models/             # 数据模型
│   ├── schemas/            # Pydantic模型
│   ├── services/           # 业务逻辑
│   ├── utils/              # 工具函数
│   ├── middleware/         # 中间件
│   └── tasks/              # Celery任务
├── alembic/                # 数据库迁移
├── tests/                  # 测试文件
└── docs/                   # 文档
```

### 添加新功能

1. **创建数据模型** - 在 `app/models/` 中定义SQLModel
2. **创建Pydantic模型** - 在 `app/schemas/` 中定义请求/响应模型
3. **实现业务逻辑** - 在 `app/services/` 中实现服务类
4. **创建API端点** - 在 `app/api/v1/` 中创建路由
5. **注册路由** - 在 `app/api/v1/__init__.py` 中注册
6. **编写测试** - 在 `tests/` 中添加测试用例

### 数据库迁移

```bash
# 创建迁移
uv run alembic revision --autogenerate -m "描述"

# 应用迁移
uv run alembic upgrade head

# 回滚迁移
uv run alembic downgrade -1
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_auth.py

# 生成覆盖率报告
uv run pytest --cov=app --cov-report=html
```

## 🔒 安全配置

### JWT配置

- 使用强密钥（至少32字符）
- 设置合适的过期时间
- 启用令牌刷新机制

### 数据库安全

- 使用强密码
- 限制数据库访问权限
- 启用SSL连接

### API安全

- 启用CORS配置
- 使用HTTPS
- 实施速率限制

## 📊 监控和日志

### 日志配置

- 结构化JSON日志
- 多级别日志记录
- 日志轮转和归档

### 错误追踪

- Sentry集成
- 异常自动上报
- 性能监控

### 健康检查

- `/health` - 基础健康检查
- 数据库连接检查
- 外部服务检查

## 🚀 性能优化

### 缓存策略

- Redis缓存热点数据
- 查询结果缓存
- 会话缓存

### 数据库优化

- 索引优化
- 查询优化
- 连接池配置

### 异步处理

- Celery后台任务
- 异步I/O操作
- 批量处理

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果您遇到问题或有疑问，请：

1. 查看[文档](docs/)
2. 搜索[Issues](../../issues)
3. 创建新的[Issue](../../issues/new)

## 🔄 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。
