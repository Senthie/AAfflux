# 元数据引擎集成设计文档

## 概述

本设计文档描述了如何将元数据引擎集成到现有的 AAfflux 低代码平台中，实现动态数据模型管理、自动化 DDL 生成、动态 ORM 和 API 生成等功能。

## 设计目标

### 核心目标
- 在现有 37 张系统表基础上，增加元数据管理能力
- 支持用户通过配置创建自定义业务模型
- 自动生成数据库表、ORM 模型和 CRUD API
- 保持与现有代码驱动模型的兼容性
- 支持多租户隔离和权限控制

### 设计原则
- **渐进式集成**：不影响现有系统功能
- **配置优于代码**：通过元数据配置定义业务模型
- **租户隔离**：所有动态模型都支持工作空间隔离
- **版本控制**：支持模型结构的版本管理
- **性能优化**：支持缓存和热加载

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AAfflux + Metadata Engine                │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Frontend Layer                           │  │
│  │  - Model Designer (模型设计器)                        │  │
│  │  - Field Configuration (字段配置)                     │  │
│  │  - Dynamic Forms (动态表单)                           │  │
│  │  - Data Management (数据管理)                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Layer                                │  │
│  │  - Static APIs (现有 37 张表的 API)                   │  │
│  │  - Dynamic APIs (元数据驱动的 API)                    │  │
│  │  - Metadata Management APIs                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Service Layer                            │  │
│  │  - Static Services (现有业务服务)                     │  │
│  │  - Generic CRUD Service (通用 CRUD)                   │  │
│  │  - Metadata Service (元数据管理)                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Metadata Engine Core                     │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │ DDL        │  │ ORM        │  │ API        │     │  │
│  │  │ Generator  │  │ Generator  │  │ Generator  │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Data Layer                               │  │
│  │  - System Tables (现有 37 张表)                       │  │
│  │  - Metadata Tables (新增 6 张元数据表)                │  │
│  │  - Dynamic Business Tables (动态业务表)               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 数据层设计

### 现有系统表（37张）
保持不变，包括：
- 认证域：users, refresh_tokens, password_resets, api_keys
- 租户域：organizations, teams, workspaces, team_members, team_invitations
- 工作流域：workflows, nodes, connections, execution_records, node_execution_results
- 应用域：applications, llm_providers, prompt_templates, prompt_template_versions
- 对话域：conversations, messages, message_annotations, message_feedbacks, end_users
- 知识库域：datasets, documents, document_segments, dataset_application_joins
- 插件域：plugins, installed_plugins
- BPM域：bpm_process_definitions, bmp_process_instances, bmp_tasks, bmp_approvals, bmp_form_definitions, bmp_form_data
- 计费域：subscriptions, usage_records
- 文件域：file_references
- 审计域：audit_logs

### 新增元数据表（6张）

#### 1. 元数据模型表 (metadata_models)
存储数据模型的定义信息
- 模型基本信息（名称、描述、表名）
- 版本控制（version, is_latest）
- 状态管理（draft, published, archived）
- 配置选项（审计、软删除等）

#### 2. 元数据字段表 (metadata_fields)
存储模型字段的详细配置
- 字段基本信息（名称、类型、描述）
- 数据库属性（类型、约束、默认值）
- 验证规则（长度、格式、枚举值等）
- UI配置（组件类型、占位符、帮助文本）

#### 3. 元数据关系表 (metadata_relations)
存储模型之间的关系定义
- 关系类型（一对一、一对多、多对多）
- 外键配置
- 级联操作

#### 4. 元数据索引表 (metadata_indexes)
存储自定义索引配置
- 单字段索引
- 复合索引
- 唯一索引

#### 5. 元数据版本表 (metadata_versions)
存储元数据的版本历史
- 版本快照
- 变更日志
- 回滚支持

#### 6. 元数据页面表 (metadata_pages)
存储动态页面配置
- 页面布局
- 组件配置
- 数据绑定

## 模型设计

### 元数据模型

基于现有的 BaseModel 和 Mixin 设计：

```python
# app/models/metadata/model.py
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlmodel import Field, Column, JSON, Relationship
from enum import Enum

from app.models.base import BaseModel, TimestampMixin, AuditMixin, WorkspaceMixin

class ModelStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published" 
    ARCHIVED = "archived"

class FieldType(str, Enum):
    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    JSON = "json"
    UUID = "uuid"
    FOREIGN_KEY = "foreign_key"

class MetadataModel(BaseModel, TimestampMixin, AuditMixin, WorkspaceMixin, table=True):
    """元数据模型表"""
    __tablename__ = "metadata_models"
    
    name: str = Field(max_length=255, index=True)
    display_name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    table_name: str = Field(max_length=255)
    schema_definition: dict = Field(default_factory=dict, sa_column=Column(JSON))
    version: int = Field(default=1)
    is_latest: bool = Field(default=True)
    status: ModelStatus = Field(default=ModelStatus.DRAFT)
    enable_audit: bool = Field(default=True)
    enable_soft_delete: bool = Field(default=True)
    permissions: dict = Field(default_factory=dict, sa_column=Column(JSON))
    published_at: Optional[datetime] = Field(default=None)
    
    # 关系
    fields: List["MetadataField"] = Relationship(back_populates="model")

class MetadataField(BaseModel, TimestampMixin, table=True):
    """元数据字段表"""
    __tablename__ = "metadata_fields"
    
    model_id: UUID = Field(foreign_key="metadata_models.id", index=True)
    name: str = Field(max_length=255)
    display_name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    field_type: FieldType
    db_type: Optional[str] = Field(default=None, max_length=50)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_indexed: bool = Field(default=False)
    is_primary_key: bool = Field(default=False)
    default_value: Optional[str] = Field(default=None)
    validation_rules: dict = Field(default_factory=dict, sa_column=Column(JSON))
    ui_config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    relation_config: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    position: int = Field(default=0)
    
    # 关系
    model: MetadataModel = Relationship(back_populates="fields")
```

## 核心组件

### 1. DDL 生成器

```python
# app/engine/metadata/ddl_generator.py
class DDLGenerator:
    """DDL 生成器 - 根据元数据生成数据库表"""
    
    TYPE_MAPPING = {
        FieldType.STRING: "VARCHAR(255)",
        FieldType.TEXT: "TEXT",
        FieldType.INTEGER: "INTEGER",
        FieldType.FLOAT: "FLOAT",
        FieldType.DECIMAL: "DECIMAL(10,2)",
        FieldType.BOOLEAN: "BOOLEAN",
        FieldType.DATE: "DATE",
        FieldType.DATETIME: "TIMESTAMP",
        FieldType.EMAIL: "VARCHAR(255)",
        FieldType.URL: "VARCHAR(500)",
        FieldType.PHONE: "VARCHAR(50)",
        FieldType.JSON: "JSONB",
        FieldType.UUID: "UUID",
        FieldType.FOREIGN_KEY: "UUID",
    }
    
    async def generate_create_table(self, model_id: UUID) -> str:
        """生成 CREATE TABLE 语句"""
        # 1. 获取模型和字段元数据
        # 2. 生成租户隔离的表名：tenant_{workspace_id}_{table_name}
        # 3. 添加标准字段：id, workspace_id
        # 4. 添加业务字段
        # 5. 根据配置添加审计字段和软删除字段
        # 6. 生成索引
        pass
```

### 2. 动态 ORM 生成器

```python
# app/engine/metadata/orm_generator.py
class DynamicModelGenerator:
    """动态 ORM 生成器"""
    
    PYTHON_TYPE_MAPPING = {
        FieldType.STRING: str,
        FieldType.TEXT: str,
        FieldType.INTEGER: int,
        FieldType.FLOAT: float,
        FieldType.BOOLEAN: bool,
        FieldType.DATE: datetime,
        FieldType.DATETIME: datetime,
        FieldType.EMAIL: str,
        FieldType.UUID: UUID,
        FieldType.JSON: dict,
    }
    
    async def generate_model(self, model_id: UUID) -> Type[SQLModel]:
        """生成动态 SQLModel 类"""
        # 1. 获取元数据
        # 2. 构建字段定义
        # 3. 动态创建类
        # 4. 缓存模型类
        pass
```

### 3. 通用 CRUD 服务

```python
# app/services/generic_crud_service.py
class GenericCRUDService:
    """通用 CRUD 服务"""
    
    async def create(self, model_id: UUID, data: Dict, workspace_id: UUID, created_by: UUID):
        """创建记录"""
        pass
    
    async def list(self, model_id: UUID, workspace_id: UUID, **kwargs):
        """查询记录列表"""
        pass
    
    async def update(self, model_id: UUID, record_id: UUID, data: Dict, workspace_id: UUID):
        """更新记录"""
        pass
    
    async def delete(self, model_id: UUID, record_id: UUID, workspace_id: UUID, soft_delete: bool = True):
        """删除记录"""
        pass
```

## API 设计

### 元数据管理 API

```python
# app/api/v1/metadata.py
@router.post("/models", response_model=MetadataModelResponse)
async def create_model(data: CreateModelRequest):
    """创建数据模型"""
    pass

@router.get("/models", response_model=List[MetadataModelResponse])
async def list_models(workspace_id: UUID):
    """查询模型列表"""
    pass

@router.post("/models/{model_id}/publish")
async def publish_model(model_id: UUID):
    """发布模型（创建数据库表和 API）"""
    pass

@router.post("/models/{model_id}/fields", response_model=MetadataFieldResponse)
async def add_field(model_id: UUID, data: CreateFieldRequest):
    """添加字段"""
    pass
```

### 动态数据 API

动态生成的 API 路由格式：
```
POST   /api/v1/data/{model_name}          # 创建记录
GET    /api/v1/data/{model_name}          # 查询记录列表
GET    /api/v1/data/{model_name}/{id}     # 获取记录详情
PUT    /api/v1/data/{model_name}/{id}     # 更新记录
DELETE /api/v1/data/{model_name}/{id}     # 删除记录
```

## 使用示例

### 1. 创建客户模型

```json
{
  "name": "customer",
  "display_name": "客户",
  "description": "客户信息管理",
  "table_name": "customers",
  "enable_audit": true,
  "enable_soft_delete": true,
  "fields": [
    {
      "name": "name",
      "display_name": "客户名称",
      "field_type": "string",
      "is_required": true,
      "validation_rules": {"min_length": 2, "max_length": 100}
    },
    {
      "name": "email",
      "display_name": "邮箱",
      "field_type": "email",
      "is_required": true,
      "is_unique": true
    },
    {
      "name": "status",
      "display_name": "状态",
      "field_type": "string",
      "default_value": "'active'",
      "validation_rules": {"enum": ["active", "inactive"]}
    }
  ]
}
```

### 2. 发布模型

```bash
POST /api/v1/metadata/models/{model_id}/publish
```

发布后会自动：
1. 生成并执行 CREATE TABLE SQL
2. 生成动态 ORM 模型
3. 生成并注册 CRUD API 路由
4. 更新模型状态为 published

### 3. 使用动态 API

```bash
# 创建客户记录
POST /api/v1/data/customer?workspace_id={workspace_id}
{
  "name": "张三",
  "email": "zhangsan@example.com",
  "status": "active"
}

# 查询客户列表
GET /api/v1/data/customer?workspace_id={workspace_id}&page=1&page_size=20
```

## 正确性属性

### 属性 1: 元数据模型继承一致性
*对于任何*元数据模型，都应该继承 BaseModel 并使用相应的 Mixin
**验证**: 所有元数据模型都包含 id, workspace_id, created_at, updated_at 字段

### 属性 2: 动态表租户隔离
*对于任何*动态生成的业务表，都应该包含 workspace_id 字段并建立外键约束
**验证**: 生成的表名格式为 tenant_{workspace_id}_{table_name}

### 属性 3: DDL 生成幂等性
*对于任何*相同的元数据配置，生成的 DDL 应该是一致的
**验证**: 多次生成相同模型的 DDL 结果相同

### 属性 4: 动态 API 一致性
*对于任何*发布的模型，都应该生成标准的 CRUD API 端点
**验证**: 每个模型都有 POST, GET, PUT, DELETE 端点

### 属性 5: 缓存一致性
*对于任何*模型更新，相关的缓存应该被正确清理和更新
**验证**: 模型更新后，ORM 缓存和 API 路由都应该更新

## 实施计划

### 第一阶段（2周）：基础设施
- [ ] 创建 6 张元数据表
- [ ] 实现元数据模型（MetadataModel, MetadataField 等）
- [ ] 创建数据库迁移脚本
- [ ] 更新模型导出和注册

### 第二阶段（2周）：核心引擎
- [ ] 实现 DDL 生成器
- [ ] 实现动态 ORM 生成器
- [ ] 实现通用 CRUD 服务
- [ ] 添加缓存机制

### 第三阶段（2周）：API 层
- [ ] 实现元数据管理 API
- [ ] 实现动态 API 生成器
- [ ] 集成到现有路由系统
- [ ] 添加权限控制

### 第四阶段（2周）：测试和优化
- [ ] 编写单元测试和集成测试
- [ ] 性能优化和缓存调优
- [ ] 文档编写
- [ ] 错误处理和日志

### 第五阶段（2周）：前端集成
- [ ] 模型设计器界面
- [ ] 字段配置组件
- [ ] 动态表单生成
- [ ] 数据管理界面

## 风险和缓解

### 风险 1: 性能影响
**风险**: 动态生成可能影响性能
**缓解**: 
- 使用多级缓存（内存缓存 + Redis）
- 预编译常用模型
- 异步生成和加载

### 风险 2: 数据一致性
**风险**: 元数据和实际表结构不一致
**缓解**:
- 版本控制和变更追踪
- 数据库 schema 验证
- 回滚机制

### 风险 3: 复杂性增加
**风险**: 系统复杂性显著增加
**缓解**:
- 渐进式实施
- 充分的测试覆盖
- 详细的文档和监控

## 总结

元数据引擎的集成将为 AAfflux 平台带来强大的动态建模能力，使用户能够通过配置快速创建业务模型，而无需编写代码。通过与现有架构的深度集成，确保了系统的一致性和可维护性。

关键优势：
- **快速开发**: 通过配置创建模型，无需编码
- **租户隔离**: 天然支持多租户架构
- **向后兼容**: 不影响现有功能
- **标准化**: 遵循现有的设计模式和规范
- **可扩展**: 支持复杂的业务场景和自定义需求