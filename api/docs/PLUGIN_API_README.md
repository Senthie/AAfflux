# Plugin API 实现说明

## 概述

已为 Plugin 模型创建完整的增删改查（CRUD）API，包括插件管理和已安装插件管理两部分功能。

## 创建的文件

### 1. `app/schemas/plugin.py`

定义了插件相关的 Pydantic schemas，包括：

- **Plugin schemas**: `PluginBase`, `PluginCreate`, `PluginUpdate`, `PluginResponse`, `PluginListResponse`, `PluginDeleteResponse`
- **InstalledPlugin schemas**: `InstalledPluginBase`, `InstalledPluginCreate`, `InstalledPluginUpdate`, `InstalledPluginResponse`, `InstalledPluginListResponse`, `InstalledPluginDeleteResponse`

### 2. `app/services/plugin_service.py`

实现了插件管理的业务逻辑，包括：

**Plugin 操作：**

- `create_plugin()` - 创建插件
- `get_plugin()` - 获取插件详情
- `list_plugins()` - 获取插件列表（支持多种过滤条件）
- `update_plugin()` - 更新插件
- `delete_plugin()` - 删除插件（软删除）

**InstalledPlugin 操作：**

- `install_plugin()` - 安装插件到工作空间
- `get_installed_plugin()` - 获取已安装插件详情
- `list_installed_plugins()` - 获取工作空间已安装插件列表
- `update_installed_plugin()` - 更新已安装插件配置
- `uninstall_plugin()` - 卸载插件（软删除）

### 3. `app/api/v1/plugins.py`

提供 RESTful API 端点，包括：

**Plugin 端点：**

- `POST /api/v1/plugins/` - 创建插件
- `GET /api/v1/plugins/` - 获取插件列表
- `GET /api/v1/plugins/{plugin_id}` - 获取插件详情
- `PUT /api/v1/plugins/{plugin_id}` - 更新插件
- `DELETE /api/v1/plugins/{plugin_id}` - 删除插件

**InstalledPlugin 端点：**

- `POST /api/v1/plugins/install` - 安装插件到工作空间
- `GET /api/v1/plugins/installed` - 获取工作空间已安装插件列表
- `GET /api/v1/plugins/installed/{installed_plugin_id}` - 获取已安装插件详情
- `PUT /api/v1/plugins/installed/{installed_plugin_id}` - 更新已安装插件配置
- `DELETE /api/v1/plugins/installed/{installed_plugin_id}` - 卸载插件

### 4. `docs/plugin_api.md`

完整的 API 文档，包括：

- API 端点说明
- 请求/响应示例
- 数据模型说明
- 错误处理
- 使用示例

## 修改的文件

### `app/api/v1/__init__.py`

添加了 plugins 路由注册：

```python
from app.api.v1 import plugins
router.include_router(plugins.router, tags=['Plugins'])
```

## 功能特性

### 1. 完整的 CRUD 操作

- 支持创建、读取、更新、删除插件
- 支持安装、查询、更新、卸载已安装插件

### 2. 高级查询功能

- 插件列表支持按分类、类型、激活状态、验证状态过滤
- 已安装插件列表支持按启用状态过滤
- 支持分页查询

### 3. 数据验证

- 使用 Pydantic 进行请求数据验证
- 验证插件分类（tool/node/integration）
- 验证插件类型（builtin/custom/marketplace）

### 4. 软删除

- 插件和已安装插件都使用软删除机制
- 保留历史数据，支持数据恢复

### 5. 关联查询

- 已安装插件响应中自动包含插件详情
- 减少客户端的额外请求

### 6. 统计功能

- 自动统计插件安装次数
- 支持插件评分

### 7. 工作空间隔离

- 已安装插件按工作空间隔离
- 每个工作空间可以独立配置插件

### 8. 错误处理

- 自定义异常类（`PluginNotFoundError`, `InstalledPluginNotFoundError`, `PluginAlreadyExistsError`）
- 统一的错误响应格式

## 使用方法

### 1. 启动应用

```bash
python main.py
```

### 2. 访问 API 文档

打开浏览器访问：

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

### 3. 测试 API

使用 Swagger UI 或 curl 命令测试 API 端点。详细示例请参考 `docs/plugin_api.md`。

## 数据库模型

API 基于以下数据库模型：

### Plugin 表

- 存储可用插件的信息和配置
- 支持内置、自定义和市场插件
- 记录安装次数和评分

### InstalledPlugin 表

- 记录工作空间安装的插件及其配置
- 每个工作空间可以独立安装和配置插件
- 支持启用/禁用已安装的插件

## 注意事项

1. **认证**: 所有 API 端点都需要 JWT 认证
2. **权限**: 需要确保用户有相应的工作空间权限
3. **软删除**: 删除操作不会真正删除数据，只是标记为已删除
4. **类型安全**: 使用了 `# type: ignore` 注释来处理 SQLModel 的类型检查问题

## 下一步

可以考虑添加以下功能：

1. 插件版本管理
2. 插件依赖管理
3. 插件市场功能
4. 插件评分和评论系统
5. 插件使用统计
6. 插件权限管理
7. 插件自动更新
8. 插件测试和验证
