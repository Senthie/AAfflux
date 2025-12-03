# 模型基类重构设计文档

## 概述

本设计文档描述了如何重构现有的数据模型架构，通过引入基类和混入（Mixin）模式来消除代码重复，提高可维护性。当前项目使用 SQLModel 框架，我们将在此基础上构建一个层次化的基类系统。

## 架构

### 当前架构问题

1. **代码重复**: 每个模型都重复定义 `id`、`created_at`、`updated_at` 字段
2. **维护困难**: 通用字段的修改需要在多个文件中同步
3. **类型不一致**: 相同功能的字段可能有不同的类型定义
4. **缺乏通用行为**: 没有统一的模型操作接口

### 新架构设计

```
BaseModel (抽象基类)
├── TimestampMixin (时间戳混入)
├── SoftDeleteMixin (软删除混入)
├── AuditMixin (审计混入)
└── 具体模型类
    ├── User
    ├── Organization
    ├── Workflow
    └── ...
```

## 组件和接口

### 1. BaseModel 基类

```python
class BaseModel(SQLModel):
    """所有数据模型的抽象基类"""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # 抽象方法和通用行为
    def to_dict(self) -> dict
    def update_from_dict(self, data: dict) -> None
    def __eq__(self, other) -> bool
```

### 2. TimestampMixin 混入

```python
class TimestampMixin:
    """提供时间戳字段的混入类"""
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def touch(self) -> None  # 更新 updated_at
```

### 3. SoftDeleteMixin 混入

```python
class SoftDeleteMixin:
    """提供软删除功能的混入类"""
    
    deleted_at: Optional[datetime] = Field(default=None)
    is_deleted: bool = Field(default=False)
    
    def soft_delete(self) -> None
    def restore(self) -> None
```

### 4. AuditMixin 混入

```python
class AuditMixin:
    """提供审计字段的混入类"""
    
    created_by: UUID = Field(foreign_key="user.id")
    updated_by: Optional[UUID] = Field(default=None, foreign_key="user.id")
```

### 5. 工作空间隔离混入

```python
class WorkspaceMixin:
    """提供工作空间隔离的混入类"""
    
    workspace_id: UUID = Field(foreign_key="workspace.id", index=True)
```

## 数据模型

### 模型继承层次

```python
# 基础用户相关模型
class User(BaseModel, TimestampMixin, table=True):
    email: str = Field(unique=True, index=True)
    password_hash: str
    name: str
    avatar_url: Optional[str] = None

# 组织相关模型
class Organization(BaseModel, TimestampMixin, AuditMixin, table=True):
    name: str
    description: Optional[str] = None
    settings: dict = Field(default_factory=dict, sa_column=Column(JSON))

# 工作空间相关模型
class Workflow(BaseModel, TimestampMixin, WorkspaceMixin, table=True):
    name: str
    description: Optional[str] = None
    input_schema: dict = Field(default_factory=dict, sa_column=Column(JSON))
    output_schema: dict = Field(default_factory=dict, sa_column=Column(JSON))
```

## 正确性属性

*属性是应该在系统的所有有效执行中保持为真的特征或行为——本质上是关于系统应该做什么的正式陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: 基类字段继承一致性

*对于任何*继承自 BaseModel 的模型类，该类应该包含 id 字段且类型为 UUID
**验证: 需求 1.2**

### 属性 2: 时间戳创建时自动设置

*对于任何*使用 TimestampMixin 的模型实例，当创建时 created_at 和 updated_at 应该被自动设置为当前时间
**验证: 需求 1.4**

### 属性 3: 更新操作时间戳管理

*对于任何*使用 TimestampMixin 的模型实例，当执行更新操作时，updated_at 应该被更新为当前时间而 created_at 保持不变
**验证: 需求 1.3, 3.2**

### 属性 4: 混入组合兼容性

*对于任何*组合多个混入的模型类，不应该存在字段名冲突，且所有混入的功能都应该正常工作
**验证: 需求 2.4**

### 属性 5: 序列化类型安全一致性

*对于任何*模型实例，序列化操作（包括 to_dict()）应该返回包含所有字段的正确类型表示，且 UUID 和 datetime 类型应该被正确处理并保持类型安全
**验证: 需求 3.1, 3.4, 5.5**

### 属性 6: 软删除状态一致性

*对于任何*使用 SoftDeleteMixin 的模型实例，当调用 soft_delete() 后，is_deleted 应该为 True 且 deleted_at 应该被设置
**验证: 需求 2.2**

### 属性 7: 模型相等性判断一致性

*对于任何*两个模型实例，相等性判断应该基于所有字段值的比较，且相同数据的实例应该被判断为相等
**验证: 需求 3.3**

### 属性 8: 向后兼容性保持

*对于任何*现有的模型使用方式，重构后的模型应该提供相同的接口和行为
**验证: 需求 4.1**

## 错误处理

### 1. 字段冲突处理

- 当混入之间存在同名字段时，使用 Python 的 MRO（方法解析顺序）
- 提供明确的错误消息指导开发者解决冲突

### 2. 类型验证

- 使用 Pydantic 的类型验证确保字段类型正确
- 在模型初始化时验证必需字段

### 3. 数据库约束

- 保持现有的数据库约束（唯一性、外键等）
- 在迁移过程中验证数据完整性

## 测试策略

### 单元测试方法

单元测试将验证具体的示例和边界情况：

- **基类功能测试**: 验证 BaseModel 的基本功能
- **混入组合测试**: 测试不同混入的组合效果
- **迁移兼容性测试**: 确保重构不破坏现有功能
- **类型提示测试**: 验证 IDE 支持和类型检查

### 属性测试方法

属性测试将验证跨所有输入的通用属性，使用 **Hypothesis** 作为属性测试库：

- 每个属性测试运行最少 100 次迭代
- 每个属性测试必须用注释明确引用设计文档中的正确性属性
- 使用格式: `# Feature: model-base-refactor, Property {number}: {property_text}`
- 每个正确性属性必须由单个属性测试实现

**属性测试要求**:

- 生成随机模型实例来测试继承行为
- 验证时间戳在各种操作下的一致性
- 测试混入组合的所有可能情况
- 确保序列化/反序列化的往返一致性

**双重测试方法**: 单元测试捕获具体错误，属性测试验证通用正确性，两者结合提供全面覆盖。

## 实现计划

### 阶段 1: 基础架构

1. 创建 BaseModel 抽象基类
2. 实现 TimestampMixin
3. 创建基础测试框架

### 阶段 2: 混入实现

1. 实现 SoftDeleteMixin
2. 实现 AuditMixin
3. 实现 WorkspaceMixin

### 阶段 3: 模型迁移

1. 逐个迁移现有模型
2. 更新导入和引用
3. 验证功能完整性

### 阶段 4: 优化和清理

1. 移除重复代码
2. 优化性能
3. 完善文档

## 迁移策略

### 1. 渐进式迁移

- 一次迁移一个模型文件
- 保持向后兼容性
- 逐步移除旧代码

### 2. 数据库迁移

- 使用 Alembic 生成迁移脚本
- 验证数据完整性
- 提供回滚方案

### 3. 测试验证

- 在每个迁移步骤后运行完整测试套件
- 验证 API 兼容性
- 检查性能影响
