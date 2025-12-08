# 实施计划

- [x] 1. 项目初始化和基础设施搭建
  - 创建 app/ 目录结构（api/, core/, models/, schemas/, services/, repositories/, middleware/, utils/）
  - 实现 app/core/config.py（使用 pydantic-settings 管理环境变量）
  - 实现 app/core/database.py（PostgreSQL 连接和会话管理）
  - 实现 app/core/mongodb.py（MongoDB 连接和 GridFS 支持）
  - 实现 app/core/redis.py（Redis 连接和缓存管理）
  - 实现 app/core/logging.py（structlog 配置）
  - 实现 app/core/sentry.py（Sentry 错误追踪配置）
  - 实现 app/main.py（FastAPI 应用初始化，中间件配置，路由注册）
  - 创建 .env.example 文件
  - _需求: 16.1, 14.1_

- [ ]* 1.1 编写项目初始化的单元测试
  - 测试数据库连接x
  - 测试配置加载
  - _需求: 16.1_

- [x] 2. 实现数据模型（SQLModel）
  - 实现 app/models/user.py（User, Organization, Team, TeamMember, Workspace）
  - 实现 app/models/workflow.py（Workflow, Node, Connection）
  - 实现 app/models/execution.py（ExecutionRecord, NodeExecutionResult）
  - 实现 app/models/template.py（PromptTemplate, PromptTemplateVersion）
  - 实现 app/models/provider.py（LLMProvider）
  - 实现 app/models/application.py（Application）
  - 实现 app/models/file.py（FileReference）
  - 配置 Alembic 并创建初始迁移
  - _需求: 所有需求的数据持久化基础_

- [x] 3. 实现认证和授权模块
  - 实现 app/services/auth_service.py（注册、登录、令牌管理）
  - 实现 app/utils/token.py（JWT 令牌生成和验证）
  - 实现 app/utils/password.py（密码哈希和验证）
  - 实现 app/middleware/auth.py（认证中间件）
  - 实现 app/services/permission_checker.py（权限检查器）
  - 实现 app/schemas/auth.py（认证相关的 Pydantic schemas）
  - _需求: 1.1, 1.2, 1.4, 1.5, 2.4, 2.5_

- [ ]* 3.1 编写属性测试：注册验证一致性
  - **属性 1: 注册验证一致性**
  - **验证: 需求 1.1**

- [ ]* 3.2 编写属性测试：登录令牌生成
  - **属性 2: 登录令牌生成**
  - **验证: 需求 1.2**

- [ ]* 3.3 编写属性测试：令牌刷新往返
  - **属性 3: 令牌刷新往返**
  - **验证: 需求 1.4**

- [ ]* 3.4 编写属性测试：登出令牌撤销
  - **属性 4: 登出令牌撤销**
  - **验证: 需求 1.5**

- [ ] 4. 实现用户管理模块
  - 实现 app/services/user_service.py（资料更新、密码修改）
  - 实现 app/schemas/user.py（用户相关的 Pydantic schemas）
  - 实现 app/api/v1/users.py（用户管理 API 端点）
  - _需求: 2.1, 2.2, 2.3_

- [ ]* 4.1 编写属性测试：资料更新持久化
  - **属性 5: 资料更新持久化**
  - **验证: 需求 2.1**

- [ ]* 4.2 编写属性测试：密码修改往返
  - **属性 6: 密码修改往返**
  - **验证: 需求 2.2**

- [ ]* 4.3 编写属性测试：头像上传验证
  - **属性 7: 头像上传验证**
  - **验证: 需求 2.3**

- [ ] 5. 实现文件存储模块
  - 实现 app/services/file_storage_service.py（文件上传、下载、删除、列表）
  - 实现 app/utils/mongodb_client.py（MongoDB 客户端封装和 GridFS 支持）
  - 实现 app/schemas/file.py（文件相关的 Pydantic schemas）
  - 实现 app/api/v1/files.py（文件管理 API 端点）
  - _需求: 2.3_

- [ ]* 5.1 编写文件存储的单元测试
  - 测试小文件存储
  - 测试 GridFS 大文件存储
  - 测试文件权限验证
  - _需求: 2.3_

- [ ] 6. 实现团队和企业管理模块
  - 实现 app/services/team_service.py（团队创建、成员管理、邀请）
  - 实现 app/services/organization_service.py（企业创建和管理）
  - 实现 app/services/workspace_service.py（工作空间管理）
  - 实现 app/schemas/team.py（团队相关的 Pydantic schemas）
  - 实现 app/schemas/organization.py（企业相关的 Pydantic schemas）
  - 实现 app/schemas/workspace.py（工作空间相关的 Pydantic schemas）
  - 实现 app/api/v1/teams.py（团队管理 API 端点）
  - 实现 app/api/v1/organizations.py（企业管理 API 端点）
  - 实现 app/api/v1/workspaces.py（工作空间管理 API 端点）
  - _需求: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 6.1 编写属性测试：团队创建者权限
  - **属性 9: 团队创建者权限**
  - **验证: 需求 3.1**

- [ ]* 6.2 编写属性测试：团队邀请接受
  - **属性 10: 团队邀请接受**
  - **验证: 需求 3.3**

- [ ]* 6.3 编写属性测试：成员移除权限撤销
  - **属性 11: 成员移除权限撤销**
  - **验证: 需求 3.4**

- [ ]* 6.4 编写属性测试：角色更改立即生效
  - **属性 12: 角色更改立即生效**
  - **验证: 需求 3.5**

- [ ]* 6.5 编写属性测试：企业创建者权限
  - **属性 13: 企业创建者权限**
  - **验证: 需求 4.1**

- [ ]* 6.6 编写属性测试：团队继承企业配置
  - **属性 14: 团队继承企业配置**
  - **验证: 需求 4.2**

- [ ]* 6.7 编写属性测试：企业配置传播
  - **属性 15: 企业配置传播**
  - **验证: 需求 4.3**

- [ ]* 6.8 编写属性测试：使用统计汇总正确性
  - **属性 16: 使用统计汇总正确性**
  - **验证: 需求 4.4**

- [ ]* 6.9 编写属性测试：企业团队级联删除
  - **属性 17: 企业团队级联删除**
  - **验证: 需求 4.5**

- [ ] 7. 实现权限控制系统
  - 实现 app/services/permission_checker.py（权限检查逻辑）
  - 实现 app/utils/tenant_context.py（租户上下文管理）
  - 实现 app/middleware/permission.py（权限验证中间件）
  - 实现 app/utils/rbac.py（角色定义和权限映射）
  - _需求: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 7.1 编写属性测试：权限验证一致性
  - **属性 18: 权限验证一致性**
  - **验证: 需求 5.1**

- [ ]* 7.2 编写属性测试：未授权操作拒绝
  - **属性 19: 未授权操作拒绝**
  - **验证: 需求 5.2**

- [ ]* 7.3 编写属性测试：管理员完全权限
  - **属性 20: 管理员完全权限**
  - **验证: 需求 5.3**

- [ ]* 7.4 编写属性测试：成员权限限制
  - **属性 21: 成员权限限制**
  - **验证: 需求 5.4**

- [ ]* 7.5 编写属性测试：访客只读权限
  - **属性 22: 访客只读权限**
  - **验证: 需求 5.5**

- [ ]* 7.6 编写属性测试：工作空间资源关联
  - **属性 23: 工作空间资源关联**
  - **验证: 需求 6.2**

- [ ]* 7.7 编写属性测试：工作空间资源隔离
  - **属性 24: 工作空间资源隔离**
  - **验证: 需求 6.3**

- [ ]* 7.8 编写属性测试：资源移动更新关联
  - **属性 25: 资源移动更新关联**
  - **验证: 需求 6.4**

- [ ]* 7.9 编写属性测试：工作空间级联删除
  - **属性 26: 工作空间级联删除**
  - **验证: 需求 6.5**

- [ ] 8. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户

- [x] 9. 实现工作流验证和序列化
  - 实现 app/services/workflow_validator.py（完整性检查、循环依赖检测）
  - 实现 app/services/workflow_serializer.py（JSON 序列化/反序列化）
  - 实现 app/utils/dag.py（DAG 相关工具函数）
  - _需求: 7.1, 7.2, 7.3, 7.4, 15.1, 15.2, 15.3, 15.4_

- [ ]* 9.1 编写属性测试：工作流初始状态
  - **属性 27: 工作流初始状态**
  - **验证: 需求 7.1**

- [ ]* 9.2 编写属性测试：节点配置验证
  - **属性 28: 节点配置验证**
  - **验证: 需求 7.2**

- [ ]* 9.3 编写属性测试：循环依赖检测
  - **属性 29: 循环依赖检测**
  - **验证: 需求 7.3**

- [ ]* 9.4 编写属性测试：工作流序列化往返
  - **属性 30: 工作流序列化往返**
  - **验证: 需求 7.4, 15.1, 15.2**

- [ ]* 9.5 编写属性测试：序列化完整性
  - **属性 57: 序列化完整性**
  - **验证: 需求 15.3**

- [ ]* 9.6 编写属性测试：反序列化验证
  - **属性 58: 反序列化验证**
  - **验证: 需求 15.4**

- [ ] 10. 实现工作流管理服务
  - 实现 app/services/workflow_service.py（工作流 CRUD、节点管理、连接管理）
  - 实现 app/schemas/workflow.py（工作流相关的 Pydantic schemas）
  - 实现 app/api/v1/workflows.py（工作流管理 API 端点）
  - _需求: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 10.1 编写属性测试：工作流删除级联
  - **属性 31: 工作流删除级联**
  - **验证: 需求 7.5**

- [ ] 11. 实现工作流执行引擎
  - 实现 app/engine/topological_sorter.py（拓扑排序）
  - 实现 app/engine/execution_context.py（执行上下文管理）
  - 实现 app/engine/node_executor.py（节点执行器基类和注册机制）
  - 实现 app/engine/workflow_engine.py（工作流执行引擎）
  - 实现 app/tasks/workflow_tasks.py（Celery 异步任务）
  - 配置 Celery（app/core/celery.py）
  - _需求: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 11.1 编写属性测试：输入参数验证
  - **属性 32: 输入参数验证**
  - **验证: 需求 8.1**

- [ ]* 11.2 编写属性测试：拓扑排序执行顺序
  - **属性 33: 拓扑排序执行顺序**
  - **验证: 需求 8.2**

- [ ]* 11.3 编写属性测试：节点数据传递
  - **属性 34: 节点数据传递**
  - **验证: 需求 8.3**

- [ ]* 11.4 编写属性测试：执行记录创建
  - **属性 35: 执行记录创建**
  - **验证: 需求 8.4**

- [ ] 12. 实现节点类型
  - 实现 app/engine/nodes/llm_node.py（LLM 调用节点）
  - 实现 app/engine/nodes/condition_node.py（条件判断节点）
  - 实现 app/engine/nodes/code_node.py（Python 代码执行节点）
  - 实现 app/engine/nodes/http_node.py（HTTP 请求节点）
  - 实现 app/engine/nodes/transform_node.py（数据转换节点）
  - 实现 app/engine/nodes/**init**.py（注册所有节点类型）
  - _需求: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ]* 12.1 编写属性测试：LLM 节点配置完整性
  - **属性 53: LLM 节点配置完整性**
  - **验证: 需求 13.1**

- [ ]* 12.2 编写属性测试：条件节点分支路由
  - **属性 54: 条件节点分支路由**
  - **验证: 需求 13.2**

- [ ]* 12.3 编写属性测试：代码节点执行
  - **属性 55: 代码节点执行**
  - **验证: 需求 13.3**

- [ ]* 12.4 编写属性测试：数据转换节点
  - **属性 56: 数据转换节点**
  - **验证: 需求 13.5**

- [ ] 13. 实现提示词模板模块
  - 实现 app/services/prompt_template_service.py（模板 CRUD、版本管理、引用检查）
  - 实现 app/utils/template_renderer.py（模板渲染和变量解析）
  - 实现 app/schemas/template.py（模板相关的 Pydantic schemas）
  - 实现 app/api/v1/templates.py（模板管理 API 端点）
  - _需求: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ]* 13.1 编写属性测试：模板语法验证
  - **属性 36: 模板语法验证**
  - **验证: 需求 9.1**

- [ ]* 13.2 编写属性测试：变量占位符解析
  - **属性 37: 变量占位符解析**
  - **验证: 需求 9.2**

- [ ]* 13.3 编写属性测试：模板渲染替换
  - **属性 38: 模板渲染替换**
  - **验证: 需求 9.3**

- [ ]* 13.4 编写属性测试：模板版本保留
  - **属性 39: 模板版本保留**
  - **验证: 需求 9.4**

- [ ]* 13.5 编写属性测试：模板引用检查
  - **属性 40: 模板引用检查**
  - **验证: 需求 9.5**

- [ ] 14. 实现 LLM 提供商管理模块
  - 实现 app/services/llm_provider_service.py（提供商配置管理、引用检查）
  - 实现 app/utils/llm/base_client.py（LLM 客户端抽象基类）
  - 实现 app/utils/llm/openai_client.py（OpenAI 客户端）
  - 实现 app/utils/llm/anthropic_client.py（Anthropic 客户端）
  - 实现 app/utils/llm/retry.py（重试机制）
  - 实现 app/schemas/provider.py（提供商相关的 Pydantic schemas）
  - 实现 app/api/v1/providers.py（提供商管理 API 端点）
  - _需求: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 14.1 编写属性测试：模型列表查询
  - **属性 41: 模型列表查询**
  - **验证: 需求 10.2**

- [ ]* 14.2 编写属性测试：LLM 调用重试
  - **属性 42: LLM 调用重试**
  - **验证: 需求 10.4**

- [ ]* 14.3 编写属性测试：提供商引用检查
  - **属性 43: 提供商引用检查**
  - **验证: 需求 10.5**

- [ ] 15. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户

- [ ] 16. 实现执行记录模块
  - 实现 app/services/execution_record_service.py（记录创建、查询、清理）
  - 实现 app/schemas/execution.py（执行记录相关的 Pydantic schemas）
  - 实现 app/api/v1/executions.py（执行记录查询 API 端点）
  - 实现 app/tasks/cleanup_tasks.py（定期清理过期记录的 Celery 任务）
  - _需求: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ]* 16.1 编写属性测试：执行记录查询
  - **属性 44: 执行记录查询**
  - **验证: 需求 11.1**

- [ ]* 16.2 编写属性测试：执行记录完整性
  - **属性 45: 执行记录完整性**
  - **验证: 需求 11.2**

- [ ]* 16.3 编写属性测试：时间范围筛选
  - **属性 46: 时间范围筛选**
  - **验证: 需求 11.4**

- [ ]* 16.4 编写属性测试：过期记录清理
  - **属性 47: 过期记录清理**
  - **验证: 需求 11.5**

- [ ] 17. 实现应用管理模块
  - 实现 app/services/application_service.py（应用 CRUD、发布、API 密钥管理）
  - 实现 app/utils/api_key.py（API 密钥生成和验证）
  - 实现 app/schemas/application.py（应用相关的 Pydantic schemas）
  - 实现 app/api/v1/applications.py（应用管理 API 端点）
  - 实现 app/api/v1/app_runtime.py（应用运行时 API 端点，供外部调用）
  - _需求: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ]* 17.1 编写属性测试：应用工作流关联
  - **属性 48: 应用工作流关联**
  - **验证: 需求 12.1**

- [ ]* 17.2 编写属性测试：API 端点生成
  - **属性 49: API 端点生成**
  - **验证: 需求 12.2**

- [ ]* 17.3 编写属性测试：API 密钥验证
  - **属性 50: API 密钥验证**
  - **验证: 需求 12.3**

- [ ]* 17.4 编写属性测试：应用配置立即生效
  - **属性 51: 应用配置立即生效**
  - **验证: 需求 12.4**

- [ ]* 17.5 编写属性测试：应用删除端点撤销
  - **属性 52: 应用删除端点撤销**
  - **验证: 需求 12.5**

- [ ] 18. 整合所有 API 路由
  - 实现 app/api/v1/**init**.py（注册所有 v1 API 路由）
  - 实现 app/api/v1/auth.py（认证 API 端点：注册、登录、登出、刷新令牌）
  - 在 app/main.py 中注册所有 API 路由
  - 实现统一的错误处理器（app/api/errors.py）
  - 实现统一的响应格式（app/schemas/response.py）
  - _需求: 16.1, 16.2, 16.3, 16.4, 16.5_

- [ ]* 18.1 编写属性测试：API 请求验证
  - **属性 60: API 请求验证**
  - **验证: 需求 16.1**

- [ ]* 18.2 编写属性测试：API 成功响应格式
  - **属性 61: API 成功响应格式**
  - **验证: 需求 16.2**

- [ ] 19. 实现数据迁移支持
  - 实现 app/utils/migration.py（数据格式版本管理和迁移逻辑）
  - 创建 Alembic 迁移脚本模板
  - _需求: 15.5_

- [ ]* 19.1 编写属性测试：数据迁移向后兼容
  - **属性 59: 数据迁移向后兼容**
  - **验证: 需求 15.5**

- [ ] 20. 实现错误处理和监控
  - 实现 app/middleware/error_handler.py（统一错误处理中间件）
  - 实现 app/middleware/request_logger.py（请求日志中间件）
  - 完善 app/core/logging.py（结构化日志配置）
  - 完善 app/core/sentry.py（Sentry 集成）
  - _需求: 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ]* 20.1 编写错误处理的单元测试
  - 测试各种错误类型的响应格式
  - 测试错误日志记录
  - _需求: 14.1, 14.2, 14.3_

- [ ] 21. 实现缓存策略
  - 实现 app/utils/cache.py（缓存装饰器和工具函数）
  - 在 AuthService 中实现用户会话缓存
  - 在 WorkflowService 中实现工作流定义缓存
  - 在 PermissionChecker 中实现权限信息缓存
  - _需求: 性能优化_

- [ ]* 21.1 编写缓存功能的单元测试
  - 测试缓存命中和失效
  - 测试缓存更新策略

- [ ] 22. 最终检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户

- [ ] 23. 完善文档和部署配置
  - 在 FastAPI 路由中添加详细的 docstrings（自动生成 OpenAPI 文档）
  - 创建 Dockerfile
  - 创建 docker-compose.yml（包含 PostgreSQL、MongoDB、Redis）
  - 更新 README.md 添加部署说明
  - 创建 .env.example 文件

- [ ]* 24. 集成测试
  - 编写端到端的工作流执行测试
  - 编写多租户隔离测试
  - 编写权限控制集成测试
  - 编写文件上传下载集成测试
