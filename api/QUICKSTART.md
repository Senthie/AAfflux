# 快速启动指南

## 🚀 5 分钟快速开始

### 1. 启动数据库服务

使用 Docker Compose 启动 PostgreSQL、MongoDB 和 Redis：

```bash
docker-compose up -d
```

验证服务状态：

```bash
docker-compose ps
```

### 2. 安装依赖

```bash
# 安装生产依赖
uv sync

# 安装开发依赖（包括测试工具）
uv sync --extra dev
```

### 3. 配置环境变量

环境变量已经在 `.env` 文件中配置好了，默认连接到本地数据库服务。

如需修改，编辑 `.env` 文件：

```bash
# 编辑环境变量
nano .env
```

### 4. 运行测试

验证基础设施是否正常工作：

```bash
# 运行所有测试
uv run pytest

# 运行基础设施测试
uv run pytest tests/test_infrastructure.py -v
```

### 5. 启动应用

```bash
# 开发模式（自动重载）
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问 API 文档

打开浏览器访问：

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **健康检查**: <http://localhost:8000/health>

## 📋 常用命令

### 开发

```bash
# 启动 API 服务器（开发模式）
uv run uvicorn app.main:app --reload

# 启动 Celery Worker
uv run celery -A app.core.celery worker --loglevel=info

# 代码格式化
uv run black app tests

# 代码检查
uv run ruff check app tests

# 类型检查
uv run mypy app
```

### 测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_infrastructure.py

# 显示测试覆盖率
uv run pytest --cov=app --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

### Docker

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### 数据库迁移

```bash
# 创建新迁移
uv run alembic revision --autogenerate -m "描述"

# 应用迁移
uv run alembic upgrade head

# 回滚迁移
uv run alembic downgrade -1

# 查看迁移历史
uv run alembic history
```

## 🔧 故障排除

### 问题 1: 数据库连接失败

**错误**: `password authentication failed for user "postgres"`

**解决方案**:

1. 确保 Docker 服务正在运行：`docker-compose ps`
2. 检查 `.env` 文件中的数据库连接配置
3. 重启数据库服务：`docker-compose restart postgres`

### 问题 2: 端口已被占用

**错误**: `Address already in use`

**解决方案**:

1. 查找占用端口的进程：`lsof -i :8000`
2. 停止该进程或使用其他端口：`--port 8001`

### 问题 3: 依赖安装失败

**错误**: `Failed to install dependencies`

**解决方案**:

1. 确保已安装 uv：`curl -LsSf https://astral.sh/uv/install.sh | sh`
2. 清理缓存：`uv cache clean`
3. 重新安装：`uv sync --reinstall`

### 问题 4: MongoDB 连接失败

**错误**: `Failed to connect to MongoDB`

**解决方案**:

1. 检查 MongoDB 服务状态：`docker-compose ps mongodb`
2. 查看 MongoDB 日志：`docker-compose logs mongodb`
3. 重启 MongoDB：`docker-compose restart mongodb`

## 📚 下一步

现在基础设施已经搭建完成，可以开始开发业务功能：

1. **实现数据模型** - 创建 User, Workflow, Application 等模型
2. **实现认证系统** - JWT 认证和权限控制
3. **实现工作流引擎** - DAG 执行和节点系统
4. **实现 API 端点** - RESTful API 接口

查看 `SETUP.md` 了解已完成的工作和详细说明。

## 💡 提示

- 使用 `uv run` 前缀运行所有 Python 命令，确保使用虚拟环境
- 开发时保持 `--reload` 模式，代码修改会自动重载
- 定期运行测试确保代码质量
- 使用 Black 和 Ruff 保持代码风格一致

## 🆘 获取帮助

- 查看 `README.md` 了解项目详情
- 查看 `SETUP.md` 了解已完成的工作
- 运行 `python verify_setup.py` 验证项目设置

祝开发愉快！🎉
