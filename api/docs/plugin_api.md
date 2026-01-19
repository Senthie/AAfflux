# Plugin API 文档

本文档描述了插件管理的 RESTful API 接口。

## 概述

插件系统支持两种类型的操作：

1. **Plugin（插件）** - 管理可用的插件定义
2. **InstalledPlugin（已安装插件）** - 管理工作空间中已安装的插件

## API 端点

### Plugin 管理

#### 1. 创建插件

```sh
POST /api/v1/plugins/
```

**请求体：**

```json
{
  "name": "chat",
  "display_name": "My Plugin",
  "description": "A custom plugin",
  "version": "0.0.1",
  "author": "AAflux",
  "icon": "https://example.com/icon.png",
  "category": "node",
  "plugin_type": "builtin",
  "manifest": {
    "internal": [
       {
      "type": "textinput",
      "key": "title",
      "label": "标题",
      "placeholder": "请输入标题",
      "default": "默认标题",
      "required": true,
      "maxLength": 50,
      "validation": {
        "regex": "^[a-zA-Z0-9_\\u4e00-\\u9fa5]+$",
        "message": "只能包含中英文、数字和下划线"
      }
    },{
      "type": "textinput",
      "key": "desc",
      "label": "描述",
      "placeholder": "节点描述",
      "default": "",
      "required": false,
      "maxLength": 50,
    },
    ],
    "parameters":[
      {
        "type": "textarea",
        "key": "prompt",
        "label": "Prompt (User Message)",
        "placeholder": "e.g. Hello, how can help me",
        "default": "",
        "required": true,
      }
    ]
  },
  "source_url": "https://github.com/user/plugin",
  "documentation_url": "https://docs.example.com",
  "is_active": true,
  "is_verified": false
}
```

**响应：**

```json
{
  "code": 200,
  "data": {
    "id": "uuid",
    "name": "my-plugin",
    "display_name": "My Plugin",
    "description": "A custom plugin",
    "version": "1.0.0",
    "author": "Author Name",
    "icon": "https://example.com/icon.png",
    "category": "tool",
    "plugin_type": "custom",
    "manifest": {},
    "source_url": "https://github.com/user/plugin",
    "documentation_url": "https://docs.example.com",
    "install_count": 0,
    "rating": 0.0,
    "is_active": true,
    "is_verified": false,
    "created_at": "2025-01-16T00:00:00Z",
    "updated_at": "2025-01-16T00:00:00Z"
  }
}
```

#### 2. 获取插件列表

```sh
GET /api/v1/plugins/?skip=0&limit=100&category=tool&plugin_type=custom&is_active=true&is_verified=false
```

**查询参数：**

- `skip`: 跳过的记录数（默认：0）
- `limit`: 返回的记录数（默认：100，最大：1000）
- `category`: 插件分类过滤（可选：tool, node, integration）
- `plugin_type`: 插件类型过滤（可选：builtin, custom, marketplace）
- `is_active`: 是否激活过滤（可选：true, false）
- `is_verified`: 是否已验证过滤（可选：true, false）

**响应：**

```json
{
  "code": 200,
  "data": {
    "plugins": [...],
    "total": 100,
    "page": 1,
    "page_size": 100
  }
}
```

#### 3. 获取插件详情

```sh
GET /api/v1/plugins/{plugin_id}
```

**响应：**

```json
{
  "code": 200,
  "data": {
    "id": "uuid",
    "name": "my-plugin",
    ...
  }
}
```

#### 4. 更新插件

```sh
PUT /api/v1/plugins/{plugin_id}
```

**请求体：**

```json
{
  "display_name": "Updated Plugin Name",
  "description": "Updated description",
  "is_active": false
}
```

**响应：**

```json
{
  "code": 200,
  "data": {
    "id": "uuid",
    "name": "my-plugin",
    "display_name": "Updated Plugin Name",
    ...
  }
}
```

#### 5. 删除插件

```sh
DELETE /api/v1/plugins/{plugin_id}
```

**响应：**

```json
{
  "code": 200,
  "data": {
    "success": true,
    "message": "Plugin deleted successfully",
    "plugin_id": "uuid"
  }
}
```

### InstalledPlugin 管理

#### 1. 安装插件到工作空间

```sh
POST /api/v1/plugins/install?workspace_id={workspace_id}
```

**请求体：**

```json
{
  "plugin_id": "uuid",
  "config": {
    "api_key": "xxx",
    "endpoint": "https://api.example.com"
  },
  "is_enabled": true
}
```

**响应：**

```json
{
  "code": 200,
  "data": {
    "id": "uuid",
    "workspace_id": "uuid",
    "plugin_id": "uuid",
    "config": {},
    "is_enabled": true,
    "installed_by": "uuid",
    "installed_at": "2025-01-16T00:00:00Z",
    "created_at": "2025-01-16T00:00:00Z",
    "updated_at": "2025-01-16T00:00:00Z",
    "plugin": {
      "id": "uuid",
      "name": "my-plugin",
      ...
    }
  }
}
```

#### 2. 获取工作空间已安装插件列表

```sh
GET /api/v1/plugins/installed?workspace_id={workspace_id}&skip=0&limit=100&is_enabled=true
```

**查询参数：**

- `workspace_id`: 工作空间ID（必需）
- `skip`: 跳过的记录数（默认：0）
- `limit`: 返回的记录数（默认：100，最大：1000）
- `is_enabled`: 是否启用过滤（可选：true, false）

**响应：**

```json
{
  "code": 200,
  "data": {
    "installed_plugins": [...],
    "total": 10,
    "page": 1,
    "page_size": 100
  }
}
```

#### 3. 获取已安装插件详情

```sh
GET /api/v1/plugins/installed/{installed_plugin_id}?workspace_id={workspace_id}
```

**响应：**

```json
{
  "code": 200,
  "data": {
    "id": "uuid",
    "workspace_id": "uuid",
    "plugin_id": "uuid",
    "config": {},
    "is_enabled": true,
    "installed_by": "uuid",
    "installed_at": "2025-01-16T00:00:00Z",
    "created_at": "2025-01-16T00:00:00Z",
    "updated_at": "2025-01-16T00:00:00Z",
    "plugin": {
      "id": "uuid",
      "name": "my-plugin",
      ...
    }
  }
}
```

#### 4. 更新已安装插件配置

```sh
PUT /api/v1/plugins/installed/{installed_plugin_id}?workspace_id={workspace_id}
```

**请求体：**

```json
{
  "config": {
    "api_key": "new_key",
    "endpoint": "https://new-api.example.com"
  },
  "is_enabled": false
}
```

**响应：**

```json
{
  "code": 200,
  "data": {
    "id": "uuid",
    "workspace_id": "uuid",
    "plugin_id": "uuid",
    "config": {
      "api_key": "new_key",
      "endpoint": "https://new-api.example.com"
    },
    "is_enabled": false,
    ...
  }
}
```

#### 5. 卸载插件

```sh
DELETE /api/v1/plugins/installed/{installed_plugin_id}?workspace_id={workspace_id}
```

**响应：**

```json
{
  "code": 200,
  "data": {
    "success": true,
    "message": "Plugin uninstalled successfully",
    "installed_plugin_id": "uuid"
  }
}
```

## 数据模型

### Plugin 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|

| id | UUID | 是 | 插件唯一标识符 |
| name | string | 是 | 插件名称（唯一） |
| display_name | string | 是 | 显示名称 |
| description | string | 是 | 插件描述 |
| version | string | 是 | 插件版本 |
| author | string | 是 | 插件作者 |
| icon | string | 否 | 插件图标URL |
| category | string | 是 | 插件分类（tool/node/integration） |
| plugin_type | string | 是 | 插件类型（builtin/custom/marketplace） |
| manifest | object | 是 | 插件清单（配置schema等） |
| source_url | string | 否 | 源代码URL |
| documentation_url | string | 否 | 文档URL |
| install_count | integer | 是 | 安装次数 |
| rating | float | 是 | 评分（0-5） |
| is_active | boolean | 是 | 是否激活 |
| is_verified | boolean | 是 | 是否已验证 |
| created_at | datetime | 是 | 创建时间 |
| updated_at | datetime | 是 | 更新时间 |

### InstalledPlugin 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|

| id | UUID | 是 | 安装记录唯一标识符 |
| workspace_id | UUID | 是 | 工作空间ID |
| plugin_id | UUID | 是 | 插件ID |
| config | object | 是 | 插件配置 |
| is_enabled | boolean | 是 | 是否启用 |
| installed_by | UUID | 是 | 安装者用户ID |
| installed_at | datetime | 是 | 安装时间 |
| created_at | datetime | 是 | 创建时间 |
| updated_at | datetime | 是 | 更新时间 |
| plugin | Plugin | 否 | 插件详情（仅在响应中） |

## 错误响应

所有 API 在发生错误时返回统一的错误格式：

```json
{
  "code": 400,
  "message": "错误信息",
  "data": "详细错误描述"
}
```

常见错误码：

- `400` - 请求参数错误
- `404` - 资源不存在
- `500` - 服务器内部错误

## 认证

所有 API 端点都需要 JWT 认证。在请求头中添加：

```sh
Authorization: Bearer <your_jwt_token>
```

## 使用示例

### 创建并安装插件

1. 创建插件：

```bash
curl -X POST "http://localhost:8000/api/v1/plugins/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-custom-tool",
    "display_name": "My Custom Tool",
    "description": "A custom tool plugin",
    "version": "1.0.0",
    "author": "John Doe",
    "category": "tool",
    "plugin_type": "custom",
    "manifest": {}
  }'
```

1. 安装插件到工作空间：

```bash
curl -X POST "http://localhost:8000/api/v1/plugins/install?workspace_id=<workspace_id>" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "plugin_id": "<plugin_id>",
    "config": {
      "setting1": "value1"
    },
    "is_enabled": true
  }'
```

1. 查看已安装插件：

```bash
curl -X GET "http://localhost:8000/api/v1/plugins/installed?workspace_id=<workspace_id>" \
  -H "Authorization: Bearer <token>"
```
