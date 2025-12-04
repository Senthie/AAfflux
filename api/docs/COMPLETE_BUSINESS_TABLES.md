# 完整业务表结构（类 Dify 架构）

## 📊 总览

**总计：31张核心表 + MongoDB文件存储**

---

## 🎯 业务流程

```sh
B端（租户用户）sh                          C端（终端用户）
    ↓                                       ↓
创建工作流/Agent                        访问已发布应用
    ↓                                       ↓
构建知识库                              创建对话会话
    ↓                                       ↓
配置LLM提供商                           发送消息
    ↓                                       ↓
发布应用                                 接收AI回复
    ↓                                       ↓
安装插件                                 评价反馈
    ↓                                       ↓
标注优化                                 继续对话
```

---

## 🗂️ 完整表结构（31张表）

### 1. 用户认证层（3张表）

#### 1.1 `users` - 租户用户（B端）

- 租户侧的用户（开发者、管理员）
- 创建和管理工作流、应用、知识库

#### 1.2 `refresh_tokens` - 刷新令牌

- JWT刷新令牌管理

#### 1.3 `password_resets` - 密码重置

- 密码重置流程

---

### 2. 租户管理层（5张表）

#### 2.1 `organizations` - 企业

#### 2.2 `teams` - 团队

#### 2.3 `workspaces` - 工作空间（租户隔离单位）

#### 2.4 `team_members` - 团队成员

#### 2.5 `team_invitations` - 团队邀请

---

### 3. 终端用户层（1张表）⭐ 新增

#### 3.1 `end_users` - 终端用户（C端）

**文件**: `app/models/end_user.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| workspace_id | UUID | 工作空间ID（租户隔离） |
| session_id | VARCHAR(255) | 会话标识符 |
| external_user_id | VARCHAR(255) | 外部系统用户ID |
| name | VARCHAR(255) | 用户名称 |
| email | VARCHAR(255) | 用户邮箱 |
| phone | VARCHAR(50) | 用户手机号 |
| avatar_url | VARCHAR(500) | 头像URL |
| metadata | JSONB | 自定义元数据 |
| is_anonymous | BOOLEAN | 是否匿名用户 |
| last_active_at | TIMESTAMP | 最后活跃时间 |
| created_at | TIMESTAMP | 创建时间 |

**业务用途**:

- 使用已发布应用的最终用户
- 支持匿名用户和注册用户
- 与外部系统集成

---

### 4. 工作流层（5张表）

#### 4.1 `workflows` - 工作流定义

#### 4.2 `nodes` - 节点

#### 4.3 `connections` - 连接

#### 4.4 `execution_records` - 执行记录

#### 4.5 `node_execution_results` - 节点执行结果

---

### 5. 对话层（2张表）⭐ 新增

#### 5.1 `conversations` - 对话会话

**文件**: `app/models/conversation.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| workspace_id | UUID | 工作空间ID（租户隔离） |
| application_id | UUID | 关联的应用ID |
| end_user_id | UUID | 终端用户ID |
| title | VARCHAR(500) | 对话标题 |
| status | VARCHAR(20) | 对话状态 |
| summary | TEXT | 对话摘要 |
| message_count | INTEGER | 消息数量 |
| metadata | JSONB | 自定义元数据 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**业务用途**:

- 管理终端用户的对话会话
- 支持多轮对话
- 对话历史管理

---

#### 5.2 `messages` - 消息

**文件**: `app/models/conversation.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| conversation_id | UUID | 所属对话ID |
| application_id | UUID | 关联的应用ID |
| workflow_run_id | UUID | 工作流执行ID |
| role | VARCHAR(20) | 消息角色（user/assistant/system） |
| content | TEXT | 消息内容 |
| query | TEXT | 用户查询 |
| answer | TEXT | AI回答 |
| inputs | JSONB | 输入参数 |
| outputs | JSONB | 输出结果 |
| model_provider | VARCHAR(100) | 模型提供商 |
| model_name | VARCHAR(100) | 模型名称 |
| prompt_tokens | INTEGER | 提示词Token数 |
| completion_tokens | INTEGER | 完成Token数 |
| total_tokens | INTEGER | 总Token数 |
| latency | FLOAT | 响应延迟 |
| status | VARCHAR(20) | 消息状态 |
| error | TEXT | 错误信息 |
| metadata | JSONB | 自定义元数据 |
| created_at | TIMESTAMP | 创建时间 |

**业务用途**:

- 存储对话中的每条消息
- 记录Token使用和成本
- 关联工作流执行

---

### 6. 标注层（2张表）⭐ 新增

#### 6.1 `message_annotations` - 消息标注

**文件**: `app/models/annotation.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| message_id | UUID | 关联的消息ID |
| conversation_id | UUID | 所属对话ID |
| application_id | UUID | 关联的应用ID |
| content | TEXT | 标注内容 |
| annotation_type | VARCHAR(50) | 标注类型 |
| annotated_by | UUID | 标注者用户ID（租户用户） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**业务用途**:

- 租户用户标注AI回复
- 修正错误回复
- 构建训练数据

---

#### 6.2 `message_feedbacks` - 消息反馈

**文件**: `app/models/annotation.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| message_id | UUID | 关联的消息ID |
| conversation_id | UUID | 所属对话ID |
| application_id | UUID | 关联的应用ID |
| end_user_id | UUID | 终端用户ID |
| rating | VARCHAR(20) | 评分（like/dislike） |
| content | TEXT | 反馈内容 |
| created_at | TIMESTAMP | 创建时间 |

**业务用途**:

- 终端用户评价AI回复
- 收集用户反馈
- 效果评估

---

### 7. 知识库层（4张表）⭐ 新增

#### 7.1 `datasets` - 知识库

**文件**: `app/models/dataset.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| workspace_id | UUID | 工作空间ID（租户隔离） |
| name | VARCHAR(255) | 知识库名称 |
| description | TEXT | 知识库描述 |
| icon | VARCHAR(255) | 知识库图标 |
| embedding_model | VARCHAR(100) | 嵌入模型 |
| embedding_model_provider | VARCHAR(100) | 嵌入模型提供商 |
| retrieval_model_config | JSONB | 检索模型配置 |
| indexing_technique | VARCHAR(50) | 索引技术 |
| document_count | INTEGER | 文档数量 |
| word_count | INTEGER | 总字数 |
| created_by | UUID | 创建者用户ID |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**业务用途**:

- RAG检索增强生成
- 文档知识管理
- 向量化和检索

---

#### 7.2 `documents` - 文档

**文件**: `app/models/dataset.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| dataset_id | UUID | 所属知识库ID |
| name | VARCHAR(255) | 文档名称 |
| data_source_type | VARCHAR(50) | 数据源类型 |
| data_source_info | JSONB | 数据源信息 |
| file_id | UUID | 文件ID |
| position | INTEGER | 显示位置 |
| word_count | INTEGER | 字数 |
| tokens | INTEGER | Token数 |
| indexing_status | VARCHAR(50) | 索引状态 |
| error | TEXT | 错误信息 |
| enabled | BOOLEAN | 是否启用 |
| disabled_at | TIMESTAMP | 禁用时间 |
| disabled_by | UUID | 禁用者用户ID |
| archived | BOOLEAN | 是否归档 |
| created_by | UUID | 创建者用户ID |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**业务用途**:

- 上传到知识库的文档
- 支持多种数据源
- 文档索引管理

---

#### 7.3 `document_segments` - 文档段落

**文件**: `app/models/dataset.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| document_id | UUID | 所属文档ID |
| dataset_id | UUID | 所属知识库ID |
| position | INTEGER | 段落位置 |
| content | TEXT | 段落内容 |
| word_count | INTEGER | 字数 |
| tokens | INTEGER | Token数 |
| keywords | JSONB | 关键词列表 |
| index_node_id | VARCHAR(255) | 向量索引节点ID |
| index_node_hash | VARCHAR(255) | 向量索引哈希值 |
| hit_count | INTEGER | 命中次数 |
| enabled | BOOLEAN | 是否启用 |
| disabled_at | TIMESTAMP | 禁用时间 |
| disabled_by | UUID | 禁用者用户ID |
| status | VARCHAR(50) | 段落状态 |
| error | TEXT | 错误信息 |
| created_by | UUID | 创建者用户ID |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**业务用途**:

- 文档分段处理
- 向量化存储
- 检索命中统计

---

#### 7.4 `dataset_application_joins` - 知识库应用关联

**文件**: `app/models/dataset.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| dataset_id | UUID | 知识库ID |
| application_id | UUID | 应用ID |
| created_at | TIMESTAMP | 创建时间 |

**业务用途**:

- 应用关联知识库
- 多对多关系
- RAG检索

---

### 8. 插件层（2张表）⭐ 新增

#### 8.1 `plugins` - 插件

**文件**: `app/models/plugin.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(255) | 插件名称（唯一） |
| display_name | VARCHAR(255) | 显示名称 |
| description | TEXT | 插件描述 |
| version | VARCHAR(50) | 插件版本 |
| author | VARCHAR(255) | 插件作者 |
| icon | VARCHAR(500) | 插件图标 |
| category | VARCHAR(50) | 插件分类 |
| plugin_type | VARCHAR(50) | 插件类型 |
| manifest | JSONB | 插件清单 |
| source_url | VARCHAR(500) | 源代码URL |
| documentation_url | VARCHAR(500) | 文档URL |
| install_count | INTEGER | 安装次数 |
| rating | FLOAT | 评分 |
| is_active | BOOLEAN | 是否激活 |
| is_verified | BOOLEAN | 是否已验证 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**业务用途**:

- 插件市场
- 扩展系统功能
- 自定义节点和工具

---

#### 8.2 `installed_plugins` - 已安装插件

**文件**: `app/models/plugin.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| workspace_id | UUID | 工作空间ID（租户隔离） |
| plugin_id | UUID | 插件ID |
| config | JSONB | 插件配置 |
| is_enabled | BOOLEAN | 是否启用 |
| installed_by | UUID | 安装者用户ID |
| installed_at | TIMESTAMP | 安装时间 |
| updated_at | TIMESTAMP | 更新时间 |

**业务用途**:

- 工作空间插件管理
- 插件配置
- 启用/禁用控制

---

### 9. 其他核心表

#### 9.1 提示词层（2张表）

- `prompt_templates` - 提示词模板
- `prompt_template_versions` - 模板版本

#### 9.2 LLM层（1张表）

- `llm_providers` - LLM提供商配置

#### 9.3 应用层（2张表）

- `applications` - 应用
- `api_keys` - API密钥

#### 9.4 审计层（1张表）

- `audit_logs` - 审计日志

#### 9.5 文件层（1张表）

- `file_references` - 文件引用

---

## 📊 表数量统计

| 分类 | 表数量 | 说明 |
|------|--------|------|
| 用户认证层 | 3 | users, refresh_tokens, password_resets |
| 租户管理层 | 5 | organizations, teams, workspaces, team_members, team_invitations |
| 终端用户层 | 1 | end_users ⭐ |
| 工作流层 | 5 | workflows, nodes, connections, execution_records, node_execution_results |
| 对话层 | 2 | conversations, messages ⭐ |
| 标注层 | 2 | message_annotations, message_feedbacks ⭐ |
| 知识库层 | 4 | datasets, documents, document_segments, dataset_application_joins ⭐ |
| 插件层 | 2 | plugins, installed_plugins ⭐ |
| 提示词层 | 2 | prompt_templates, prompt_template_versions |
| LLM层 | 1 | llm_providers |
| 应用层 | 2 | applications, api_keys |
| 审计层 | 1 | audit_logs |
| 文件层 | 1 | file_references |
| **总计** | **31** | **完整业务架构** |

---

## 🎯 核心业务流程

### 1. B端（租户）流程

```sh
租户用户注册登录
    ↓
创建企业/团队/工作空间
    ↓
邀请团队成员
    ↓
创建工作流（DAG编排）
    ↓
构建知识库（上传文档）
    ↓
配置LLM提供商
    ↓
安装插件（扩展功能）
    ↓
创建应用（关联工作流和知识库）
    ↓
发布应用（生成API端点）
```

### 2. C端（终端用户）流程

```sh
终端用户访问应用
    ↓
创建对话会话
    ↓
发送消息（用户输入）
    ↓
系统执行工作流
    ↓
检索知识库（RAG）
    ↓
调用LLM生成回复
    ↓
返回AI回复
    ↓
用户评价反馈（点赞/点踩）
    ↓
继续多轮对话
```

### 3. 标注优化流程

```sh
租户用户查看对话
    ↓
发现不准确的AI回复
    ↓
标注修正回复
    ↓
系统记录标注数据
    ↓
用于模型微调和优化
```

---

## ✅ 完整性验证

### 核心功能覆盖

- ✅ 多租户管理（B端）
- ✅ 终端用户管理（C端）
- ✅ 工作流编排（DAG）
- ✅ 对话管理（多轮对话）
- ✅ 消息管理（用户输入+AI回复）
- ✅ 知识库管理（RAG）
- ✅ 文档管理（上传、分段、向量化）
- ✅ 插件系统（扩展功能）
- ✅ 标注功能（人工修正）
- ✅ 反馈功能（用户评价）
- ✅ LLM集成（多提供商）
- ✅ 应用发布（API端点）
- ✅ 审计日志（操作追踪）

### 类 Dify 功能对比

| 功能 | Dify | 本系统 | 状态 |
|------|------|--------|------|
| 工作流编排 | ✅ | ✅ | 完整 |
| 知识库 | ✅ | ✅ | 完整 |
| 对话管理 | ✅ | ✅ | 完整 |
| 标注功能 | ✅ | ✅ | 完整 |
| 插件系统 | ✅ | ✅ | 完整 |
| 多租户 | ✅ | ✅ | 完整 |
| 终端用户 | ✅ | ✅ | 完整 |
| RAG检索 | ✅ | ✅ | 完整 |

---

## 🎉 总结

**Models 模块已完成！包含31张核心表，完整支持类 Dify 的业务架构。**

✅ **B端租户管理** - 企业/团队/工作空间  
✅ **C端用户管理** - 终端用户和会话  
✅ **工作流编排** - DAG可视化编排  
✅ **对话系统** - 多轮对话和消息  
✅ **知识库** - 文档上传、分段、向量化  
✅ **标注功能** - 人工修正和反馈  
✅ **插件系统** - 扩展和自定义  
✅ **完整隔离** - 租户级别数据隔离  

**可以开始实现服务层和API层了！** 🚀
