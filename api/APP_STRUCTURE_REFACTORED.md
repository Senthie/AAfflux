# API/APP 最终重构后的完整项目结构

## 📋 重构说明

经过两次重构：
1. **第一次重构**：将 BPM 模块从独立目录拆解并整合到 app 的同名模块中
2. **第二次重构**：为 BPM 文件添加 `bpm_` 前缀，提高识别性
3. **第三次重构**：将 models 模块按业务域分组，统一结构

## 🎯 重构目标

1. ✅ 统一项目结构，符合 FastAPI 最佳实践
2. ✅ 简化导入路径，减少嵌套层级
3. ✅ 保持业务边界清晰（通过子目录分组）
4. ✅ 提高文件识别性（BPM 文件添加前缀）
5. ✅ 便于维护和扩展

## 📁 最终目录结构

```
api/app/
├── __init__.py                          # 应用包初始化
├── main.py                              # FastAPI 应用入口
│
├── api/v1/                              # API 路由层（统一）
│   ├── __init__.py                     # 路由注册
│   ├── bpm_processes.py                # BPM 流程 API ✅
│   ├── bpm_tasks.py                    # BPM 任务 API ✅
│   └── bpm_approvals.py                # BPM 审批 API ✅
│
├── core/                                # 核心配置层
│   ├── __init__.py
│   ├── config.py                       # 应用配置
│   ├── database.py                     # PostgreSQL 连接
│   ├── mongodb.py                      # MongoDB 连接
│   ├── redis.py                        # Redis 连接
│   ├── celery.py                       # Celery 配置
│   ├── logging.py                      # 日志配置
│   └── sentry.py                       # Sentry 配置
│
├── models/                              # 数据模型层（按业务域分组）✅
│   ├── __init__.py                     # 导出所有模型（37张表）
│   ├── base.py                         # 基础模型类
│   │
│   ├── auth/                           # 认证域（4张表）✅
│   │   ├── __init__.py
│   │   ├── user.py                    # User
│   │   ├── token.py                   # RefreshToken, PasswordReset
│   │   └── api_key.py                 # APIKey
│   │
│   ├── tenant/                         # 租户域（5张表）✅
│   │   ├── __init__.py
│   │   ├── organization.py            # Organization, Team, Workspace, TeamMember
│   │   └── invitation.py              # TeamInvitation
│   │
│   ├── workflow/                       # 工作流域（5张表）✅
│   │   ├── __init__.py
│   │   └── workflow.py                # Workflow, Node, Connection, ExecutionRecord, NodeExecutionResult
│   │
│   ├── application/                    # 应用域（4张表）✅
│   │   ├── __init__.py
│   │   ├── application.py             # Application
│   │   ├── llm_provider.py            # LLMProvider
│   │   └── prompt_template.py         # PromptTemplate, PromptTemplateVersion
│   │
│   ├── conversation/                   # 对话域（5张表）✅
│   │   ├── __init__.py
│   │   ├── conversation.py            # Conversation, Message
│   │   ├── annotation.py              # MessageAnnotation, MessageFeedback
│   │   └── end_user.py                # EndUser
│   │
│   ├── dataset/                        # 知识库域（4张表）✅
│   │   ├── __init__.py
│   │   └── dataset.py                 # Dataset, Document, DocumentSegment, DatasetApplicationJoin
│   │
│   ├── plugin/                         # 插件域（2张表）✅
│   │   ├── __init__.py
│   │   └── plugin.py                  # Plugin, InstalledPlugin
│   │
│   ├── bpm/                            # BPM域（6张表）✅
│   │   ├── __init__.py
│   │   ├── process.py                 # ProcessDefinition, ProcessInstance
│   │   ├── task.py                    # Task
│   │   ├── approval.py                # Approval
│   │   └── form.py                    # FormDefinition, FormData
│   │
│   ├── billing/                        # 计费域（2张表）✅
│   │   ├── __init__.py
│   │   └── billing.py                 # Subscription, UsageRecord
│   │
│   ├── file/                           # 文件域（1张表）✅
│   │   ├── __init__.py
│   │   ├── reference.py               # FileReference
│   │   └── service.py                 # FileService
│   │
│   └── audit/                          # 审计域（1张表）✅
│       ├── __init__.py
│       └── audit_log.py               # AuditLog
│
├── schemas/                             # Pydantic Schemas（统一）
│   ├── __init__.py                     # 导出所有 Schemas
│   ├── bpm_process_schemas.py          # 流程 Schemas ✅
│   ├── bpm_task_schemas.py             # 任务 Schemas ✅
│   └── bpm_approval_schemas.py         # 审批 Schemas ✅
│
├── services/                            # 业务逻辑层（统一）
│   ├── __init__.py                     # 导出所有服务
│   ├── bpm_process_service.py          # 流程服务 ✅
│   ├── bpm_task_service.py             # 任务服务 ✅
│   └── bpm_approval_service.py         # 审批服务 ✅
│
├── repositories/                        # 数据访问层
│   └── __init__.py
│
├── engine/                              # 执行引擎（分组）
│   ├── __init__.py
│   ├── nodes/                          # Workflow 节点
│   │   └── __init__.py
│   └── bpm/                            # BPM 引擎 ✅
│       ├── __init__.py
│       ├── executor.py                 # 流程执行器
│       └── task_dispatcher.py          # 任务分发器
│
├── tasks/                               # Celery 异步任务
│   └── __init__.py
│
├── middleware/                          # 中间件
│   └── __init__.py
│
└── utils/                               # 工具函数
    ├── __init__.py
    └── llm/                            # LLM 客户端
        └── __init__.py
```

## 🔄 三次重构对比

### 原始结构（独立 BPM 模块）

```python
app/
├── bpm/                    # 独立模块
│   ├── models/
│   ├── services/
│   ├── schemas/
│   ├── api/
│   └── engine/
├── models/                 # 平铺的主业务模型
│   ├── user.py
│   ├── workflow.py
│   └── ...（20个文件）
└── services/               # 主业务服务
```

### 第一次重构（拆解 BPM）

```python
app/
├── models/                 # 合并所有模型（平铺）
│   ├── user.py
│   ├── workflow.py
│   ├── process_definition.py  # BPM
│   └── ...
├── services/               # 合并所有服务
│   ├── process_service.py     # BPM
│   └── ...
└── api/v1/                 # 合并所有 API
    ├── processes.py           # BPM
    └── ...
```

### 第二次重构（添加 BPM 前缀）

```python
app/
├── models/                 # 模型仍然平铺
│   ├── user.py
│   ├── workflow.py
│   └── bpm/               # BPM 用子目录
├── services/               # 添加 bpm_ 前缀
│   ├── bpm_process_service.py  ✅
│   └── bpm_task_service.py     ✅
├── schemas/                # 添加 bpm_ 前缀
│   ├── bpm_process_schemas.py  ✅
│   └── bpm_task_schemas.py     ✅
└── api/v1/                 # 添加 bpm_ 前缀
    ├── bpm_processes.py        ✅
    └── bpm_tasks.py            ✅
```

### 第三次重构（Models 按业务域分组）✅ 当前

```python
app/
├── models/                 # 按业务域分组
│   ├── auth/              # 认证域 ✅
│   ├── tenant/            # 租户域 ✅
│   ├── workflow/          # 工作流域 ✅
│   ├── conversation/      # 对话域 ✅
│   ├── dataset/           # 知识库域 ✅
│   ├── bpm/               # BPM域 ✅
│   └── ...                # 其他域
├── services/               # BPM 文件有前缀
│   ├── bpm_process_service.py
│   └── bpm_task_service.py
└── api/v1/                 # BPM 文件有前缀
    ├── bpm_processes.py
    └── bpm_tasks.py
```

## 📊 数据模型统计（按业务域）

| 业务域 | 表数量 | 文件位置 | 说明 |
|--------|--------|----------|------|
| 认证域 | 4 | models/auth/ | User, RefreshToken, PasswordReset, APIKey |
| 租户域 | 5 | models/tenant/ | Organization, Team, Workspace, TeamMember, TeamInvitation |
| 工作流域 | 5 | models/workflow/ | Workflow, Node, Connection, ExecutionRecord, NodeExecutionResult |
| 应用域 | 4 | models/application/ | Application, LLMProvider, PromptTemplate, PromptTemplateVersion |
| 对话域 | 5 | models/conversation/ | Conversation, Message, MessageAnnotation, MessageFeedback, EndUser |
| 知识库域 | 4 | models/dataset/ | Dataset, Document, DocumentSegment, DatasetApplicationJoin |
| 插件域 | 2 | models/plugin/ | Plugin, InstalledPlugin |
| **BPM域** | **6** | **models/bpm/** | **ProcessDefinition, ProcessInstance, Task, Approval, FormDefinition, FormData** |
| 计费域 | 2 | models/billing/ | Subscription, UsageRecord |
| 文件域 | 1 | models/file/ | FileReference |
| 审计域 | 1 | models/audit/ | AuditLog |
| **总计** | **37** | **11个业务域** | **31张主业务表 + 6张BPM表** |

## 🔧 导入示例

### Models 导入

```python
# 方式 1：从主包导入（推荐，向后兼容）
from api.app.models import (
    User,                    # 认证域
    Organization,            # 租户域
    Workflow,                # 工作流域
    Application,             # 应用域
    Conversation,            # 对话域
    Dataset,                 # 知识库域
    Plugin,                  # 插件域
    ProcessDefinition,       # BPM域
    Subscription,            # 计费域
    FileReference,           # 文件域
    AuditLog,                # 审计域
)

# 方式 2：从子包导入（更清晰）
from api.app.models.auth import User, APIKey
from api.app.models.tenant import Organization, Team
from api.app.models.workflow import Workflow, Node
from api.app.models.bpm import ProcessDefinition, Task
```

### Services 导入

```python
# 统一导入（推荐）
from api.app.services import (
    ProcessService,      # BPM 流程服务
    TaskService,         # BPM 任务服务
    ApprovalService,     # BPM 审批服务
)

# 或单独导入
from api.app.services.bpm_process_service import ProcessService
from api.app.services.bpm_task_service import TaskService
```

### Schemas 导入

```python
# 统一导入（推荐）
from api.app.schemas import (
    ProcessInstanceCreate,
    TaskResponse,
    ApprovalRequest,
)

# 或单独导入
from api.app.schemas.bpm_process_schemas import ProcessInstanceCreate
from api.app.schemas.bpm_task_schemas import TaskResponse
```

### API 路由导入

```python
# 在 main.py 中注册
from api.app.api.v1 import router as v1_router

app.include_router(v1_router)
```

## 🎯 API 端点

### BPM API 端点（添加了 /bpm 前缀）

```bash
# 流程管理
POST   /api/v1/bpm/processes/start          # 启动流程
GET    /api/v1/bpm/processes/{id}           # 查询流程
POST   /api/v1/bpm/processes/{id}/cancel    # 取消流程

# 任务管理
GET    /api/v1/bpm/tasks/my-tasks           # 我的待办
POST   /api/v1/bpm/tasks/{id}/claim         # 认领任务
POST   /api/v1/bpm/tasks/{id}/complete      # 完成任务
GET    /api/v1/bpm/tasks/{id}               # 任务详情

# 审批管理
POST   /api/v1/bpm/approvals/{id}/approve   # 审批通过
POST   /api/v1/bpm/approvals/{id}/reject    # 审批拒绝
```

## ✨ 重构优势总结

### 1. 结构统一
- 所有模型按业务域分组（11个域）
- 所有服务在 `services/` 目录（BPM 文件有前缀）
- 所有 API 在 `api/v1/` 目录（BPM 文件有前缀）
- 符合 FastAPI 标准结构

### 2. 识别性强
```python
# Models：通过子目录识别
models/auth/          # 认证相关
models/bpm/           # BPM相关

# Services/Schemas/API：通过文件名前缀识别
services/bpm_process_service.py   # BPM服务
schemas/bpm_task_schemas.py       # BPM Schemas
api/v1/bpm_tasks.py               # BPM API
```

### 3. 业务边界清晰
- 11个业务域，职责明确
- 每个域独立管理
- 便于团队协作

### 4. 易于维护
- 文件更聚焦，职责单一
- 便于查找和修改
- 减少命名冲突

### 5. 易于扩展
```python
# 新增业务域示例
models/
├── crm/              # 新增 CRM 域
│   ├── customer.py
│   └── order.py
services/
└── crm_service.py    # CRM 服务
api/v1/
└── crm.py            # CRM API
```

## 📝 重构历史

### 第一次重构（2024-12-02）
- ✅ 将 BPM 模块从独立目录拆解到 app 同名模块
- ✅ 移动 16 个文件
- ✅ 更新 16 处导入路径

### 第二次重构（2024-12-02）
- ✅ 为 BPM 文件添加 `bpm_` 前缀
- ✅ 重命名 9 个文件
- ✅ 更新 6 处导入路径
- ✅ API 端点添加 `/bpm` 前缀

### 第三次重构（2024-12-02）
- ✅ Models 模块按业务域分组
- ✅ 创建 10 个业务域子目录
- ✅ 移动 18 个模型文件
- ✅ 保持向后兼容性

## 🎉 总结

经过三次重构，项目结构已经达到最佳状态：

1. **Models 层**：按业务域分组（11个域，37张表）
2. **Services 层**：统一目录，BPM 文件有前缀
3. **Schemas 层**：统一目录，BPM 文件有前缀
4. **API 层**：统一目录，BPM 文件有前缀，端点有 `/bpm` 前缀
5. **Engine 层**：按功能分组（workflow/, bpm/）

**项目特点**：
- 结构清晰，易于理解
- 识别性强，避免混淆
- 业务边界明确
- 便于维护和扩展
- 符合最佳实践

---

**最后更新**: 2024-12-02  
**总表数**: 37张（31张主业务表 + 6张BPM表）  
**业务域数**: 11个  
**重构次数**: 3次  
**状态**: ✅ 完成
