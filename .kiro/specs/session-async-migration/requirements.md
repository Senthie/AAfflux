# Session异步迁移需求文档

## 介绍

当前项目中存在多个服务使用同步Session而非AsyncSession的问题，这导致了架构不一致性和潜在的性能问题。需要将所有服务统一迁移到AsyncSession，确保整个应用的异步一致性。

## 术语表

- **AsyncSession**: SQLModel/SQLAlchemy的异步数据库会话类
- **Session**: SQLModel/SQLAlchemy的同步数据库会话类  
- **Service**: 业务逻辑服务层类
- **BPM**: 业务流程管理(Business Process Management)
- **LLM**: 大语言模型(Large Language Model)

## 需求

### 需求1

**用户故事:** 作为系统架构师，我希望所有服务都使用AsyncSession，以确保应用的异步一致性和性能优化。

#### 验收标准

1. WHEN 检查所有服务类 THEN 系统应该使用AsyncSession而非同步Session
2. WHEN 服务执行数据库操作 THEN 系统应该使用await关键字进行异步调用
3. WHEN 导入Session类型 THEN 系统应该从sqlmodel.ext.asyncio.session导入AsyncSession
4. WHEN 服务构造函数接收session参数 THEN 系统应该声明类型为AsyncSession
5. WHEN 执行数据库查询 THEN 系统应该使用await session.execute()而非session.execute()

### 需求2

**用户故事:** 作为开发者，我希望BPM相关服务使用AsyncSession，以确保业务流程管理的异步处理能力。

#### 验收标准

1. WHEN BPMTaskService执行任务操作 THEN 系统应该使用AsyncSession进行异步数据库访问
2. WHEN BPMProcessService执行流程操作 THEN 系统应该使用AsyncSession进行异步数据库访问  
3. WHEN BPMApprovalService执行审批操作 THEN 系统应该使用AsyncSession进行异步数据库访问
4. WHEN TaskDispatcher和ProcessExecutor被调用 THEN 系统应该传递AsyncSession参数
5. WHEN BPM服务方法被调用 THEN 系统应该返回awaitable对象

### 需求3

**用户故事:** 作为开发者，我希望LLM提供商服务使用AsyncSession，以确保AI服务的异步处理能力。

#### 验收标准

1. WHEN LLMProviderService执行提供商管理操作 THEN 系统应该使用AsyncSession进行异步数据库访问
2. WHEN 创建、更新、删除LLM提供商 THEN 系统应该使用异步数据库操作
3. WHEN 查询LLM提供商列表 THEN 系统应该使用异步查询方法
4. WHEN LLM服务方法被调用 THEN 系统应该返回awaitable对象

### 需求4

**用户故事:** 作为开发者，我希望权限检查服务使用AsyncSession，以确保权限验证的异步处理能力。

#### 验收标准

1. WHEN PermissionChecker执行权限检查 THEN 系统应该使用AsyncSession进行异步数据库访问
2. WHEN 验证用户权限 THEN 系统应该使用异步查询方法
3. WHEN 检查团队成员权限 THEN 系统应该使用异步数据库操作
4. WHEN 权限检查方法被调用 THEN 系统应该返回awaitable对象

### 需求5

**用户故事:** 作为开发者，我希望所有依赖这些服务的API端点和引擎组件都能正确处理异步调用。

#### 验收标准

1. WHEN API端点调用迁移后的服务 THEN 系统应该使用await关键字
2. WHEN 引擎组件使用迁移后的服务 THEN 系统应该正确处理异步调用
3. WHEN 测试文件测试迁移后的服务 THEN 系统应该使用异步测试方法
4. WHEN 依赖注入提供session THEN 系统应该提供AsyncSession实例
5. WHEN 服务间相互调用 THEN 系统应该保持异步调用链的一致性