# 任务 2-8 实施计划

## 当前项目完成情况

### ✅ 已完成的任务

#### 任务 1: 项目初始化和基础设施搭建
- ✅ 目录结构完整
- ✅ 核心配置模块（config.py, database.py, mongodb.py, redis.py）
- ✅ 日志和监控（logging.py, sentry.py）
- ✅ FastAPI 应用初始化（main.py）
- ✅ 环境配置（.env.example）

#### 任务 2: 数据模型实现
- ✅ 基础模型（BaseModel, TimestampMixin, WorkspaceMixin, AuditMixin）
- ✅ 用户认证模型（User, Token, ApiKey）
- ✅ 租户模型（Organization, Team, Workspace）
- ✅ 应用模型（Application, LLMProvider, PromptTemplate）
- ✅ 工作流模型（Workflow, Node, Connection）
- ✅ 审计日志（AuditLog）
- ✅ 文件引用（FileReference）
- ✅ BPM 模型（Process, Task, Approval, Form）
- ✅ 对话模型（Conversation, EndUser, Annotation）
- ✅ 数据集模型（Dataset）
- ✅ 元数据模型（MetadataModel）

#### 任务 3: 认证和授权模块
- ✅ AuthService（注册、登录、令牌管理）
- ✅ Token 工具（JWT 生成和验证）
- ✅ Password 工具（密码哈希和验证）
- ✅ 认证中间件（auth.py）
- ✅ 权限检查器（permission_checker.py）
- ✅ 认证 Schemas（auth_schema.py）

### ❌ 待完成的任务（2-8）

## 任务 4: 用户管理模块

### 目标
实现用户资料管理、密码修改、头像上传等功能。

### 需要实现的文件

#### 1. `app/services/user_service.py`
```python
"""用户管理服务

功能：
- 获取用户信息
- 更新用户资料（姓名、邮箱）
- 修改密码
- 上传/更新头像
- 删除用户
"""

class UserService:
    async def get_user(self, user_id: UUID) -> User
    async def update_profile(self, user_id: UUID, data: UserUpdateSchema) -> User
    async def change_password(self, user_id: UUID, old_password: str, new_password: str) -> bool
    async def upload_avatar(self, user_id: UUID, file: UploadFile) -> str
    async def delete_user(self, user_id: UUID) -> bool
```

#### 2. `app/schemas/user.py`
```python
"""用户相关的 Pydantic Schemas

- UserResponse: 用户信息响应
- UserUpdateSchema: 用户资料更新请求
- PasswordChangeSchema: 密码修改请求
- UserListResponse: 用户列表响应
"""
```

#### 3. `app/api/v1/users.py`
```python
"""用户管理 API 端点

- GET /api/v1/users/me - 获取当前用户信息
- PUT /api/v1/users/me - 更新用户资料
- POST /api/v1/users/me/password - 修改密码
- POST /api/v1/users/me/avatar - 上传头像
- DELETE /api/v1/users/me - 删除账户
"""
```

### 依赖关系
- ✅ AuthService（已完成）
- ✅ Token 验证（已完成）
- ❌ FileStorageService（任务 5 需要实现）

### 验证需求
- 需求 2.1: 资料更新持久化
- 需求 2.2: 密码修改往返
- 需求 2.3: 头像上传验证

---

## 任务 5: 文件存储模块

### 目标
实现文件上传、下载、删除功能，支持小文件和 GridFS 大文件存储。

### 需要实现的文件

#### 1. `app/services/file_storage_service.py`
```python
"""文件存储服务

功能：
- 上传文件（自动选择存储方式）
- 下载文件
- 删除文件
- 列出文件
- 获取文件元数据
"""

class FileStorageService:
    async def upload_file(self, file: UploadFile, workspace_id: UUID, user_id: UUID) -> FileReference
    async def download_file(self, file_id: UUID) -> StreamingResponse
    async def delete_file(self, file_id: UUID) -> bool
    async def list_files(self, workspace_id: UUID, filters: dict) -> List[FileReference]
    async def get_file_metadata(self, file_id: UUID) -> FileReference
```

#### 2. `app/utils/mongodb_client.py`
```python
"""MongoDB 客户端封装

功能：
- GridFS 文件上传
- GridFS 文件下载
- GridFS 文件删除
- 文件元数据管理
"""
```

#### 3. `app/schemas/file.py`
```python
"""文件相关的 Pydantic Schemas

- FileUploadResponse: 文件上传响应
- FileMetadataResponse: 文件元数据响应
- FileListResponse: 文件列表响应
"""
```

#### 4. `app/api/v1/files.py`
```python
"""文件管理 API 端点

- POST /api/v1/files - 上传文件
- GET /api/v1/files/{file_id} - 下载文件
- DELETE /api/v1/files/{file_id} - 删除文件
- GET /api/v1/files - 列出文件
- GET /api/v1/files/{file_id}/metadata - 获取文件元数据
"""
```

### 配置要求
- 文件大小限制：100MB（可配置）
- GridFS 阈值：16MB（可配置）
- 支持的文件类型：图片、文档、视频等

### 验证需求
- 需求 2.3: 文件上传和存储

---

## 任务 6: 团队和企业管理模块

### 目标
实现多租户架构的核心功能：企业、团队、工作空间管理。

### 需要实现的文件

#### 1. `app/services/organization_service.py`
```python
"""企业管理服务

功能：
- 创建企业
- 更新企业信息
- 删除企业（级联删除团队和工作空间）
- 获取企业信息
- 企业配置管理
- 使用统计
"""

class OrganizationService:
    async def create_organization(self, data: OrganizationCreateSchema, creator_id: UUID) -> Organization
    async def update_organization(self, org_id: UUID, data: OrganizationUpdateSchema) -> Organization
    async def delete_organization(self, org_id: UUID) -> bool
    async def get_organization(self, org_id: UUID) -> Organization
    async def get_usage_stats(self, org_id: UUID) -> dict
```

#### 2. `app/services/team_service.py`
```python
"""团队管理服务

功能：
- 创建团队
- 更新团队信息
- 删除团队
- 添加成员
- 移除成员
- 更新成员角色
- 发送邀请
- 接受邀请
"""

class TeamService:
    async def create_team(self, data: TeamCreateSchema, creator_id: UUID) -> Team
    async def add_member(self, team_id: UUID, user_id: UUID, role: str) -> TeamMember
    async def remove_member(self, team_id: UUID, user_id: UUID) -> bool
    async def update_member_role(self, team_id: UUID, user_id: UUID, new_role: str) -> TeamMember
    async def send_invitation(self, team_id: UUID, email: str, role: str) -> Invitation
    async def accept_invitation(self, invitation_id: UUID, user_id: UUID) -> TeamMember
```

#### 3. `app/services/workspace_service.py`
```python
"""工作空间管理服务

功能：
- 创建工作空间
- 更新工作空间
- 删除工作空间（级联删除资源）
- 移动资源到其他工作空间
- 获取工作空间资源列表
"""

class WorkspaceService:
    async def create_workspace(self, data: WorkspaceCreateSchema, team_id: UUID) -> Workspace
    async def update_workspace(self, workspace_id: UUID, data: WorkspaceUpdateSchema) -> Workspace
    async def delete_workspace(self, workspace_id: UUID) -> bool
    async def move_resource(self, resource_id: UUID, resource_type: str, target_workspace_id: UUID) -> bool
    async def list_resources(self, workspace_id: UUID) -> dict
```

#### 4. Schemas
- `app/schemas/organization.py`
- `app/schemas/team.py`
- `app/schemas/workspace.py`

#### 5. API 端点
- `app/api/v1/organizations.py`
- `app/api/v1/teams.py`
- `app/api/v1/workspaces.py`

### 验证需求
- 需求 3.1-3.5: 团队管理
- 需求 4.1-4.5: 企业管理
- 需求 6.1-6.5: 工作空间管理

---

## 任务 7: 权限控制系统

### 目标
实现基于角色的访问控制（RBAC）和租户隔离。

### 需要实现的文件

#### 1. `app/utils/rbac.py`
```python
"""角色定义和权限映射

角色：
- ADMIN: 完全权限（CRUD）
- MEMBER: 创建和读取权限
- VIEWER: 只读权限

权限映射：
- 资源类型 -> 操作 -> 允许的角色
"""

class Role(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class Permission(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

ROLE_PERMISSIONS = {
    Role.ADMIN: [Permission.CREATE, Permission.READ, Permission.UPDATE, Permission.DELETE],
    Role.MEMBER: [Permission.CREATE, Permission.READ],
    Role.VIEWER: [Permission.READ],
}
```

#### 2. `app/utils/tenant_context.py`
```python
"""租户上下文管理

功能：
- 从请求中提取租户信息
- 验证用户是否属于租户
- 获取用户在租户中的角色
"""

class TenantContext:
    def __init__(self, workspace_id: UUID, user_id: UUID, role: str)
    async def verify_access(self) -> bool
    async def get_user_role(self) -> str
```

#### 3. `app/middleware/permission.py`
```python
"""权限验证中间件

功能：
- 拦截请求
- 验证用户权限
- 检查租户隔离
"""
```

#### 4. 增强 `app/services/permission_checker.py`
```python
"""权限检查器

功能：
- 检查用户是否有权限执行操作
- 检查资源是否属于用户的工作空间
- 缓存权限信息
"""

class PermissionChecker:
    async def check_permission(self, user_id: UUID, resource_type: str, operation: str, workspace_id: UUID) -> bool
    async def check_resource_access(self, user_id: UUID, resource_id: UUID, resource_type: str) -> bool
    async def get_user_role(self, user_id: UUID, workspace_id: UUID) -> str
```

### 验证需求
- 需求 5.1-5.5: 权限控制
- 需求 6.2-6.5: 工作空间资源隔离

---

## 任务 8: 检查点

### 目标
确保任务 4-7 的所有功能正常工作。

### 检查项
1. ✅ 所有单元测试通过
2. ✅ 所有属性测试通过
3. ✅ API 端点可以正常访问
4. ✅ 权限控制正常工作
5. ✅ 租户隔离正常工作
6. ✅ 文件上传下载正常工作

---

## 实施准备

### 1. 环境准备

#### 确认虚拟环境
```bash
cd api
uv run python --version  # 应该是 3.12.7
uv run python -c "import sys; print(sys.prefix)"  # 应该指向 .venv
```

#### 确认依赖安装
```bash
uv sync --extra dev
```

#### 启动数据库服务
```bash
docker-compose up -d
```

### 2. 代码质量工具

#### 运行代码检查
```bash
uv run ruff check --fix .
uv run ruff format .
```

#### 运行类型检查
```bash
uv run mypy app
```

### 3. 测试准备

#### 创建测试目录结构
```
tests/
├── unit/
│   ├── services/
│   ├── utils/
│   └── api/
├── integration/
└── property/
```

#### 运行现有测试
```bash
uv run pytest tests/ -v
```

### 4. 数据库迁移

#### 创建新的迁移
```bash
uv run alembic revision --autogenerate -m "Add missing tables"
```

#### 应用迁移
```bash
uv run alembic upgrade head
```

---

## 实施顺序建议

### 阶段 1: 基础服务（1-2 天）
1. **任务 5: 文件存储模块**（先实现，因为任务 4 依赖它）
   - 实现 FileStorageService
   - 实现 MongoDB GridFS 封装
   - 实现文件 API 端点
   - 编写单元测试

2. **任务 4: 用户管理模块**
   - 实现 UserService
   - 实现用户 Schemas
   - 实现用户 API 端点
   - 编写属性测试

### 阶段 2: 多租户架构（2-3 天）
3. **任务 7: 权限控制系统**（先实现，因为任务 6 依赖它）
   - 实现 RBAC 角色定义
   - 实现租户上下文管理
   - 实现权限检查器增强
   - 实现权限中间件
   - 编写属性测试

4. **任务 6: 团队和企业管理模块**
   - 实现 OrganizationService
   - 实现 TeamService
   - 实现 WorkspaceService
   - 实现相关 Schemas 和 API 端点
   - 编写属性测试

### 阶段 3: 验证和测试（1 天）
5. **任务 8: 检查点**
   - 运行所有测试
   - 修复发现的问题
   - 验证 API 文档
   - 进行集成测试

---

## 开发规范

### 代码风格
- 使用 Ruff 进行代码检查和格式化
- 行长度：100 字符
- 使用单引号
- 使用类型注解

### 文档规范
- 每个函数/类都要有 docstring
- API 端点要有详细的描述和示例
- 使用 FastAPI 的自动文档生成

### 测试规范
- 单元测试覆盖率 > 80%
- 每个服务方法都要有测试
- 使用 pytest fixtures 管理测试数据
- 使用 Hypothesis 进行属性测试

### Git 提交规范
- `feat: 添加新功能`
- `fix: 修复bug`
- `refactor: 重构代码`
- `test: 添加测试`
- `docs: 更新文档`

---

## 常见问题

### Q1: 如何测试文件上传？
使用 FastAPI 的 TestClient 和 UploadFile：
```python
from fastapi.testclient import TestClient
from io import BytesIO

client = TestClient(app)
files = {"file": ("test.txt", BytesIO(b"test content"), "text/plain")}
response = client.post("/api/v1/files", files=files)
```

### Q2: 如何测试权限控制？
使用不同角色的用户进行测试：
```python
# 测试管理员权限
admin_token = create_test_token(user_id, role="admin")
response = client.delete(f"/api/v1/resources/{resource_id}", headers={"Authorization": f"Bearer {admin_token}"})
assert response.status_code == 200

# 测试访客权限
viewer_token = create_test_token(user_id, role="viewer")
response = client.delete(f"/api/v1/resources/{resource_id}", headers={"Authorization": f"Bearer {viewer_token}"})
assert response.status_code == 403
```

### Q3: 如何处理级联删除？
在 Service 层实现级联删除逻辑：
```python
async def delete_organization(self, org_id: UUID) -> bool:
    # 1. 删除所有团队
    teams = await self.get_organization_teams(org_id)
    for team in teams:
        await self.team_service.delete_team(team.id)
    
    # 2. 删除企业
    await self.repository.delete(org_id)
    return True
```

---

## 下一步行动

1. **立即开始**: 从任务 5（文件存储模块）开始实现
2. **每日检查**: 运行测试确保代码质量
3. **及时提交**: 完成一个功能就提交一次
4. **文档同步**: 更新 API 文档和 README

---

## 总结

当前项目已完成：
- ✅ 基础设施（任务 1）
- ✅ 数据模型（任务 2）
- ✅ 认证授权（任务 3）

待完成任务（2-8）：
- ❌ 用户管理（任务 4）
- ❌ 文件存储（任务 5）
- ❌ 团队企业管理（任务 6）
- ❌ 权限控制（任务 7）
- ❌ 检查点（任务 8）

预计完成时间：**4-6 天**

建议按照阶段 1 → 阶段 2 → 阶段 3 的顺序实施，每个阶段完成后进行测试验证。
