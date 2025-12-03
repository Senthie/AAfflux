# AAfflux 项目完整结构

## 📋 项目概述

**AAfflux（爱附魔）** 是一个类似 Dify 的低代码平台，采用前后端分离架构：
- **后端**: FastAPI + Python 3.12，支持工作流编排、AI 集成、BPM 流程管理和多租户架构
- **前端**: Vue 3 + Quasar + TypeScript，提供可视化工作流编排界面

---

## 🏗️ 整体架构

```
AAfflux/
├── api/                    # 后端服务（FastAPI）
├── web/                    # 前端应用（Vue 3 + Quasar）
├── LICENSE                 # MIT 许可证
└── README.md              # 项目说明
```

---

## 🔧 后端服务 (api/)

### 技术栈
- **Python 3.12+**
- **FastAPI** - 高性能异步 Web 框架
- **SQLModel** - ORM (SQLAlchemy + Pydantic)
- **PostgreSQL** - 主数据库
- **MongoDB** - 文件存储 (GridFS)
- **Redis** - 缓存和会话
- **Celery** - 异步任务队列
- **Alembic** - 数据库迁移
- **Structlog** - 结构化日志
- **Sentry** - 错误追踪

### 目录结构（最新）

```
api/
├── app/                           # 应用主目录
│   ├── api/v1/                   # API 路由层
│   │   ├── __init__.py           # 路由注册
│   │   ├── bpm_processes.py     # BPM 流程 API ✅
│   │   ├── bpm_tasks.py         # BPM 任务 API ✅
│   │   └── bpm_approvals.py     # BPM 审批 API ✅
│   │
│   ├── core/                      # 核心配置层
│   │   ├── __init__.py
│   │   ├── config.py             # 应用配置（环境变量、设置）
│   │   ├── database.py           # PostgreSQL 连接和会话管理
│   │   ├── mongodb.py            # MongoDB 连接和 GridFS
│   │   ├── redis.py              # Redis 连接和缓存
│   │   ├── celery.py             # Celery 任务队列配置
│   │   ├── logging.py            # Structlog 日志配置
│   │   └── sentry.py             # Sentry 错误追踪配置
│   │
│   ├── models/                    # 数据模型层（按业务域分组）✅
│   │   ├── __init__.py           # 导出所有模型（37张表）
│   │   ├── base.py               # 基础模型类
│   │   │
│   │   ├── auth/                 # 认证域（4张表）✅
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # User
│   │   │   ├── token.py         # RefreshToken, PasswordReset
│   │   │   └── api_key.py       # APIKey
│   │   │
│   │   ├── tenant/               # 租户域（5张表）✅
│   │   │   ├── __init__.py
│   │   │   ├── organization.py  # Organization, Team, Workspace, TeamMember
│   │   │   └── invitation.py    # TeamInvitation
│   │   │
│   │   ├── workflow/             # 工作流域（5张表）✅
│   │   │   ├── __init__.py
│   │   │   └── workflow.py      # Workflow, Node, Connection, ExecutionRecord, NodeExecutionResult
│   │   │
│   │   ├── application/          # 应用域（4张表）✅
│   │   │   ├── __init__.py
│   │   │   ├── application.py   # Application
│   │   │   ├── llm_provider.py  # LLMProvider
│   │   │   └── prompt_template.py # PromptTemplate, PromptTemplateVersion
│   │   │
│   │   ├── conversation/         # 对话域（5张表）✅
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py  # Conversation, Message
│   │   │   ├── annotation.py    # MessageAnnotation, MessageFeedback
│   │   │   └── end_user.py      # EndUser
│   │   │
│   │   ├── dataset/              # 知识库域（4张表）✅
│   │   │   ├── __init__.py
│   │   │   └── dataset.py       # Dataset, Document, DocumentSegment, DatasetApplicationJoin
│   │   │
│   │   ├── plugin/               # 插件域（2张表）✅
│   │   │   ├── __init__.py
│   │   │   └── plugin.py        # Plugin, InstalledPlugin
│   │   │
│   │   ├── bpm/                  # BPM域（6张表）✅
│   │   │   ├── __init__.py
│   │   │   ├── process.py       # ProcessDefinition, ProcessInstance
│   │   │   ├── task.py          # Task
│   │   │   ├── approval.py      # Approval
│   │   │   └── form.py          # FormDefinition, FormData
│   │   │
│   │   ├── billing/              # 计费域（2张表）✅
│   │   │   ├── __init__.py
│   │   │   └── billing.py       # Subscription, UsageRecord
│   │   │
│   │   ├── file/                 # 文件域（1张表）✅
│   │   │   ├── __init__.py
│   │   │   ├── reference.py     # FileReference
│   │   │   └── service.py       # FileService
│   │   │
│   │   └── audit/                # 审计域（1张表）✅
│   │       ├── __init__.py
│   │       └── audit_log.py     # AuditLog
│   │
│   ├── schemas/                   # Pydantic Schemas（请求/响应模型）
│   │   ├── __init__.py
│   │   ├── bpm_process_schemas.py  # BPM 流程 Schemas ✅
│   │   ├── bpm_task_schemas.py     # BPM 任务 Schemas ✅
│   │   └── bpm_approval_schemas.py # BPM 审批 Schemas ✅
│   │
│   ├── services/                  # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── bpm_process_service.py  # BPM 流程服务 ✅
│   │   ├── bpm_task_service.py     # BPM 任务服务 ✅
│   │   └── bpm_approval_service.py # BPM 审批服务 ✅
│   │
│   ├── repositories/              # 数据访问层（Repository 模式）
│   │   └── __init__.py
│   │
│   ├── engine/                    # 执行引擎
│   │   ├── __init__.py
│   │   ├── nodes/                # Workflow 节点类型实现
│   │   │   └── __init__.py      # LLM、条件、代码、HTTP、数据转换节点
│   │   └── bpm/                  # BPM 执行引擎 ✅
│   │       ├── __init__.py
│   │       ├── executor.py       # 流程执行器
│   │       └── task_dispatcher.py # 任务分发器
│   │
│   ├── tasks/                     # Celery 异步任务
│   │   └── __init__.py
│   │
│   ├── middleware/                # 中间件
│   │   └── __init__.py           # 认证、日志、错误处理、租户上下文
│   │
│   ├── utils/                     # 工具函数
│   │   ├── __init__.py
│   │   └── llm/                  # LLM 客户端封装
│   │       └── __init__.py       # OpenAI, Anthropic 等
│   │
│   ├── __init__.py
│   └── main.py                   # FastAPI 应用入口
│
├── tests/                         # 测试目录
│   ├── test_models/              # 模型测试
│   ├── __init__.py
│   ├── conftest.py               # Pytest 配置和 fixtures
│   └── test_infrastructure.py    # 基础设施测试
│
├── docs/                          # 文档目录
│   ├── env_configuration.md      # 环境配置详细说明
│   ├── env_quick_guide.md        # 环境配置快速指南
│   └── sqlmodel_vs_sqlalchemy.md # SQLModel vs SQLAlchemy 对比
│
├── .kiro/                         # Kiro IDE 配置
│   └── specs/                    # 规格文档
│       └── low-code-platform-backend/
│           ├── design.md         # 设计文档
│           └── requirements.md   # 需求文档
│
├── # 配置文件
├── .dockerignore                 # Docker 忽略文件
├── .env.example                  # 环境变量示例
├── .gitignore                    # Git 忽略文件
├── .python-version               # Python 版本
├── docker-compose.yml            # Docker Compose 配置
├── Dockerfile                    # Docker 镜像构建
├── pyproject.toml                # Python 项目配置（uv）
├── uv.lock                       # 依赖锁定文件
│
├── # 文档
├── APP_STRUCTURE_REFACTORED.md   # 重构后的 APP 结构（最新）✅
├── BPM_RENAME_SUMMARY.md         # BPM 文件重命名总结 ✅
├── COMPLETE_BUSINESS_TABLES.md   # 完整业务表结构（37张表）✅
├── COMPLETE_TABLE_STRUCTURE.md   # 完整表结构详情
├── FINAL_MODELS_SUMMARY.md       # 模型总结
├── MIGRATION_GUIDE.md            # BPM 迁移指南 ✅
├── MODELS_REFACTORING_SUMMARY.md # Models 重构总结 ✅
├── PROJECT_STRUCTURE.md          # 项目结构说明（本文件）
├── QUICKSTART.md                 # 快速开始指南
├── README.md                     # 项目说明
├── REFACTORING_SUMMARY.md        # BPM 拆解重构总结 ✅
└── SETUP.md                      # 安装配置指南
```

### 核心功能模块

#### 1. 多租户架构（三层隔离）
```
企业 (Organization)
  └── 团队 (Team)
        └── 工作空间 (Workspace)
              ├── 工作流 (Workflow)
              ├── 应用 (Application)
              ├── 知识库 (Dataset)
              ├── 插件 (Plugin)
              ├── BPM 流程 (Process) ✅
              └── LLM 配置 (Provider)
```

#### 2. 工作流引擎
- 基于 DAG（有向无环图）的可视化编排
- 支持节点类型：
  - LLM 节点（AI 对话）
  - 条件判断节点
  - 代码执行节点
  - HTTP 请求节点
  - 数据转换节点
  - BPM 审批节点 ✅
- 拓扑排序执行，支持并行
- 异步执行（Celery）

#### 3. BPM 流程管理 ✅ 新增
- 流程定义和版本控制
- 任务分配和认领
- 审批流程（通过/拒绝）
- 表单管理
- 流程执行引擎
- 任务分发器

#### 4. 知识库系统（RAG）
- 文档上传和管理
- 自动分段处理
- 向量化存储
- 语义检索
- 支持多种数据源

#### 5. 对话系统
- 多轮对话管理
- 消息历史记录
- Token 使用统计
- 成本追踪

#### 6. 标注和反馈
- 人工标注修正
- 用户反馈收集
- 效果评估

#### 7. 插件系统
- 插件市场
- 自定义节点
- 扩展功能

### 数据库设计

**37张核心表**（31张主业务表 + 6张BPM表），按业务域分组：

| 业务域 | 表数量 | 主要表 |
|--------|--------|--------|
| 认证域 | 4 | users, refresh_tokens, password_resets, api_keys |
| 租户域 | 5 | organizations, teams, workspaces, team_members, team_invitations |
| 工作流域 | 5 | workflows, nodes, connections, execution_records, node_execution_results |
| 应用域 | 4 | applications, llm_providers, prompt_templates, prompt_template_versions |
| 对话域 | 5 | conversations, messages, message_annotations, message_feedbacks, end_users |
| 知识库域 | 4 | datasets, documents, document_segments, dataset_application_joins |
| 插件域 | 2 | plugins, installed_plugins |
| **BPM域** ✅ | **6** | **bpm_process_definitions, bpm_process_instances, bpm_tasks, bpm_approvals, bpm_form_definitions, bpm_form_data** |
| 计费域 | 2 | subscriptions, usage_records |
| 文件域 | 1 | file_references |
| 审计域 | 1 | audit_logs |

详细表结构见 `COMPLETE_BUSINESS_TABLES.md`

### API 端点设计

```
/api/v1/
├── auth/                  # 认证相关
│   ├── POST /login
│   ├── POST /register
│   ├── POST /refresh
│   └── POST /logout
│
├── organizations/         # 企业管理
├── teams/                # 团队管理
├── workspaces/           # 工作空间管理
│
├── workflows/            # 工作流管理
│   ├── GET /workflows
│   ├── POST /workflows
│   ├── GET /workflows/{id}
│   ├── PUT /workflows/{id}
│   ├── DELETE /workflows/{id}
│   └── POST /workflows/{id}/execute
│
├── bpm/                  # BPM 流程管理 ✅
│   ├── processes/        # 流程管理
│   │   ├── POST /start
│   │   ├── GET /{id}
│   │   └── POST /{id}/cancel
│   ├── tasks/            # 任务管理
│   │   ├── GET /my-tasks
│   │   ├── POST /{id}/claim
│   │   ├── POST /{id}/complete
│   │   └── GET /{id}
│   └── approvals/        # 审批管理
│       ├── POST /{id}/approve
│       └── POST /{id}/reject
│
├── applications/         # 应用管理
├── datasets/            # 知识库管理
├── conversations/       # 对话管理
├── plugins/             # 插件管理
└── llm-providers/       # LLM 提供商配置
```

### 租户上下文管理 ✅

采用主流 SaaS 方案：**JWT (身份) + Header (上下文) + Redis (验证)**

```
请求流程：
1. Client 发送请求
   - Authorization: Bearer <JWT>
   - X-Workspace-ID: <workspace_id>
   
2. Middleware 验证
   - 验证 JWT（身份认证）
   - 提取 workspace_id（上下文）
   - Redis 验证权限
   
3. 构建 TenantContext
   - user_id
   - workspace_id
   - team_id
   - role
   - permissions
   
4. 请求处理
   - 自动过滤租户数据
   - 权限检查
```

---

## 🎨 前端应用 (web/)

### 技术栈
- **Vue 3** - 渐进式 JavaScript 框架
- **Quasar Framework** - Vue 3 UI 组件库
- **TypeScript** - 类型安全
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端
- **Vue I18n** - 国际化

### 目录结构

```
web/
├── src/                          # 源代码目录
│   ├── assets/                   # 静态资源
│   ├── boot/                     # 启动文件（插件初始化）
│   │   ├── axios.ts             # Axios 配置
│   │   └── i18n.ts              # 国际化配置
│   ├── components/               # 可复用组件
│   ├── css/                      # 全局样式
│   ├── i18n/                     # 国际化资源
│   ├── layouts/                  # 布局组件
│   ├── pages/                    # 页面组件
│   ├── router/                   # 路由配置
│   ├── stores/                   # Pinia 状态管理
│   ├── App.vue                   # 根组件
│   └── env.d.ts                  # 环境类型定义
│
├── public/                       # 公共静态文件
├── .vscode/                      # VS Code 配置
│
├── # 配置文件
├── .editorconfig                 # 编辑器配置
├── eslint.config.js              # ESLint 配置
├── quasar.config.ts              # Quasar 配置
├── tsconfig.json                 # TypeScript 配置
│
├── package.json                  # 项目依赖
├── pnpm-lock.yaml               # pnpm 锁定文件
├── index.html                    # HTML 入口
└── README.md                     # 前端说明
```

### 核心功能模块（规划）

#### 1. 工作流编辑器
- 可视化 DAG 编排
- 拖拽式节点添加
- 节点配置面板
- 连线管理
- 实时预览

#### 2. BPM 流程管理 ✅
- 流程设计器
- 任务待办列表
- 审批界面
- 流程监控

#### 3. 知识库管理
- 文档上传
- 文档列表
- 分段查看
- 检索测试

#### 4. 应用管理
- 应用创建
- 配置管理
- 发布部署
- API 密钥管理

#### 5. 对话界面
- 聊天窗口
- 消息历史
- 反馈按钮
- 标注功能

#### 6. 插件市场
- 插件浏览
- 插件安装
- 插件配置

---

## 🔄 业务流程

### B端（租户）流程

```
1. 用户注册登录
   ↓
2. 创建企业/团队/工作空间
   ↓
3. 邀请团队成员
   ↓
4. 创建工作流（DAG 编排）
   ↓
5. 创建 BPM 流程（审批流程）✅
   ↓
6. 构建知识库（上传文档）
   ↓
7. 配置 LLM 提供商
   ↓
8. 安装插件（扩展功能）
   ↓
9. 创建应用（关联工作流和知识库）
   ↓
10. 发布应用（生成 API 端点）
```

### C端（终端用户）流程

```
1. 终端用户访问应用
   ↓
2. 创建对话会话
   ↓
3. 发送消息（用户输入）
   ↓
4. 系统执行工作流
   ↓
5. 检索知识库（RAG）
   ↓
6. 调用 LLM 生成回复
   ↓
7. 返回 AI 回复
   ↓
8. 用户评价反馈（点赞/点踩）
   ↓
9. 继续多轮对话
```

### BPM 审批流程 ✅

```
1. 用户发起审批（如：创建工作空间）
   ↓
2. 系统创建 BPM 流程实例
   ↓
3. 生成审批任务并分配给审批人
   ↓
4. 审批人收到待办通知
   ↓
5. 审批人审批（通过/拒绝）
   ↓
6. 系统执行后续操作
   ↓
7. 通知申请人结果
```

---

## 🚀 快速开始

### 后端启动

```bash
cd api

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env

# 启动数据库（Docker）
docker-compose up -d postgres mongodb redis

# 运行数据库迁移
uv run alembic upgrade head

# 启动 API 服务器
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动 Celery worker（另一个终端）
uv run celery -A app.core.celery worker --loglevel=info
```

访问 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 前端启动

```bash
cd web

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

访问前端应用：http://localhost:9000

---

## 📦 部署

### Docker Compose 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 生产环境

后端：
```bash
# 使用 gunicorn + uvicorn workers
uv run gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

前端：
```bash
# 构建生产版本
pnpm build

# 部署 dist/ 目录到 Nginx/CDN
```

---

## 🧪 测试

### 后端测试

```bash
cd api

# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_infrastructure.py

# 测试覆盖率
uv run pytest --cov=app --cov-report=html
```

### 前端测试

```bash
cd web

# 运行测试
pnpm test

# Lint 检查
pnpm lint
```

---

## � 开发规式范

### 代码风格

后端：
- 使用 Black 格式化代码
- 使用 Ruff 进行代码检查
- 使用 MyPy 进行类型检查

前端：
- 使用 ESLint 进行代码检查
- 使用 TypeScript 严格模式
- 遵循 Vue 3 Composition API 风格

### Git 工作流

```bash
# 创建特性分支
git checkout -b feature/amazing-feature

# 提交更改
git commit -m "feat: add amazing feature"

# 推送分支
git push origin feature/amazing-feature

# 创建 Pull Request
```

### 提交信息规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

---

## 📚 相关文档

### 后端文档
- [重构后的 APP 结构](api/APP_STRUCTURE_REFACTORED.md) - 最新的详细结构 ✅
- [完整业务表结构](api/COMPLETE_BUSINESS_TABLES.md) - 37张表详细说明 ✅
- [BPM 重命名总结](api/BPM_RENAME_SUMMARY.md) - BPM 文件重命名 ✅
- [Models 重构总结](api/MODELS_REFACTORING_SUMMARY.md) - Models 按业务域分组 ✅
- [BPM 迁移指南](api/MIGRATION_GUIDE.md) - 导入路径迁移 ✅
- [快速开始](api/QUICKSTART.md) - 快速上手指南
- [安装配置](api/SETUP.md) - 详细安装步骤
- [环境配置](api/docs/env_configuration.md) - 环境变量说明
- [设计文档](api/.kiro/specs/low-code-platform-backend/design.md) - 系统设计

### 前端文档
- [Quasar 文档](https://quasar.dev/)
- [Vue 3 文档](https://vuejs.org/)
- [Pinia 文档](https://pinia.vuejs.org/)

---

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 开启 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 📞 联系方式

- 项目作者: Senthie
- 项目名称: AAfflux（爱附魔）
- 问题反馈: GitHub Issues

---

## 🎯 开发状态

### 已完成 ✅
- [x] 项目架构设计
- [x] 数据库模型设计（37张表：31张主业务表 + 6张BPM表）
- [x] Models 按业务域分组重构（11个业务域）
- [x] BPM 模块集成（流程、任务、审批）
- [x] 核心配置层（数据库、Redis、MongoDB、Celery）
- [x] 租户上下文管理方案设计
- [x] 基础项目结构
- [x] Docker 配置
- [x] 测试框架搭建

### 进行中 🚧
- [ ] API 路由实现
- [ ] 业务逻辑层实现
- [ ] 工作流引擎实现
- [ ] BPM 引擎实现
- [ ] 租户上下文中间件实现
- [ ] 前端界面开发

### 计划中 📋
- [ ] 知识库向量化
- [ ] LLM 集成
- [ ] 插件系统
- [ ] 用户认证和授权
- [ ] 完整的单元测试
- [ ] API 文档完善
- [ ] 部署文档

---

**最后更新**: 2024-12-02  
**总表数**: 37张（31张主业务表 + 6张BPM表）  
**业务域数**: 11个  
**重构次数**: 3次（BPM拆解 + BPM重命名 + Models分组）
