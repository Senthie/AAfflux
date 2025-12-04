# 元数据引擎使用示例

## 概述

本文档提供了元数据引擎的详细使用示例，展示如何通过配置创建数据模型、生成数据库表和 API。

## 示例 1：创建客户管理模型

### 1.1 定义客户模型

```json
{
  "name": "customer",
  "display_name": "客户",
  "description": "客户信息管理系统",
  "table_name": "customers",
  "category": "crm",
  "icon": "user-group",
  "enable_audit": true,
  "enable_soft_delete": true,
  "permissions": {
    "create": ["admin", "sales"],
    "read": ["admin", "sales", "support"],
    "update": ["admin", "sales"],
    "delete": ["admin"]
  },
  "fields": [
    {
      "name": "name",
      "display_name": "客户名称",
      "description": "客户的全称或公司名称",
      "field_type": "string",
      "is_required": true,
      "is_indexed": true,
      "validation_rules": {
        "min_length": 2,
        "max_length": 100,
        "pattern": "^[\\u4e00-\\u9fa5a-zA-Z0-9\\s]+$"
      },
      "ui_config": {
        "widget": "input",
        "placeholder": "请输入客户名称",
        "help_text": "支持中文、英文和数字",
        "width": "100%"
      },
      "position": 1
    },
    {
      "name": "email",
      "display_name": "邮箱地址",
      "description": "客户的主要联系邮箱",
      "field_type": "email",
      "is_required": true,
      "is_unique": true,
      "is_indexed": true,
      "validation_rules": {
        "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      },
      "ui_config": {
        "widget": "email-input",
        "placeholder": "example@company.com",
        "help_text": "用于发送重要通知"
      },
      "position": 2
    },
    {
      "name": "phone",
      "display_name": "联系电话",
      "description": "客户的主要联系电话",
      "field_type": "phone",
      "is_required": false,
      "validation_rules": {
        "pattern": "^1[3-9]\\d{9}$"
      },
      "ui_config": {
        "widget": "phone-input",
        "placeholder": "13800138000",
        "help_text": "请输入11位手机号码"
      },
      "position": 3
    },
    {
      "name": "company",
      "display_name": "公司名称",
      "description": "客户所属公司",
      "field_type": "string",
      "is_required": false,
      "validation_rules": {
        "max_length": 200
      },
      "ui_config": {
        "widget": "input",
        "placeholder": "请输入公司名称"
      },
      "position": 4
    },
    {
      "name": "industry",
      "display_name": "所属行业",
      "description": "客户所在的行业分类",
      "field_type": "string",
      "is_required": false,
      "validation_rules": {
        "enum": [
          "technology",
          "finance",
          "healthcare",
          "education",
          "manufacturing",
          "retail",
          "other"
        ]
      },
      "ui_config": {
        "widget": "select",
        "options": [
          {"label": "科技", "value": "technology"},
          {"label": "金融", "value": "finance"},
          {"label": "医疗", "value": "healthcare"},
          {"label": "教育", "value": "education"},
          {"label": "制造", "value": "manufacturing"},
          {"label": "零售", "value": "retail"},
          {"label": "其他", "value": "other"}
        ]
      },
      "position": 5
    },
    {
      "name": "status",
      "display_name": "客户状态",
      "description": "客户的当前状态",
      "field_type": "string",
      "is_required": true,
      "is_indexed": true,
      "default_value": "'active'",
      "validation_rules": {
        "enum": ["active", "inactive", "pending", "blocked"]
      },
      "ui_config": {
        "widget": "radio",
        "options": [
          {"label": "活跃", "value": "active", "color": "green"},
          {"label": "停用", "value": "inactive", "color": "gray"},
          {"label": "待审核", "value": "pending", "color": "orange"},
          {"label": "已屏蔽", "value": "blocked", "color": "red"}
        ]
      },
      "position": 6
    },
    {
      "name": "address",
      "display_name": "联系地址",
      "description": "客户的详细地址",
      "field_type": "text",
      "is_required": false,
      "validation_rules": {
        "max_length": 500
      },
      "ui_config": {
        "widget": "textarea",
        "placeholder": "请输入详细地址",
        "rows": 3
      },
      "position": 7
    },
    {
      "name": "tags",
      "display_name": "客户标签",
      "description": "用于分类和筛选的标签",
      "field_type": "json",
      "is_required": false,
      "ui_config": {
        "widget": "tag-input",
        "placeholder": "添加标签",
        "help_text": "按回车键添加标签"
      },
      "position": 8
    },
    {
      "name": "notes",
      "display_name": "备注信息",
      "description": "关于客户的额外信息",
      "field_type": "text",
      "is_required": false,
      "ui_config": {
        "widget": "rich-editor",
        "placeholder": "添加备注信息..."
      },
      "position": 9
    },
    {
      "name": "last_contact_date",
      "display_name": "最后联系时间",
      "description": "最近一次与客户联系的时间",
      "field_type": "datetime",
      "is_required": false,
      "ui_config": {
        "widget": "datetime-picker",
        "format": "YYYY-MM-DD HH:mm:ss"
      },
      "position": 10
    }
  ]
}
```

### 1.2 创建模型 API 调用

```python
import httpx
import asyncio

async def create_customer_model():
    """创建客户模型"""
    
    # 模型定义（如上所示）
    model_data = { ... }
    
    # 调用 API 创建模型
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/metadata/models",
            json=model_data,
            headers={
                "Authorization": "Bearer your-token",
                "X-Workspace-ID": "your-workspace-id"
            }
        )
        
        if response.status_code == 201:
            model = response.json()
            print(f"✅ 客户模型创建成功: {model['id']}")
            return model
        else:
            print(f"❌ 创建失败: {response.text}")
            return None

# 运行示例
model = await create_customer_model()
```

### 1.3 发布模型

```python
async def publish_customer_model(model_id: str):
    """发布客户模型"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/api/v1/metadata/models/{model_id}/publish",
            headers={
                "Authorization": "Bearer your-token",
                "X-Workspace-ID": "your-workspace-id"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 模型发布成功!")
            print(f"   - 数据库表: {result['table_name']}")
            print(f"   - API 端点: {result['api_endpoints']}")
            return True
        else:
            print(f"❌ 发布失败: {response.text}")
            return False

# 发布模型
await publish_customer_model(model['id'])
```

发布后会自动：
1. 生成数据库表 `tenant_{workspace_id}_customers`
2. 创建标准 CRUD API 端点
3. 生成动态 ORM 模型
4. 更新模型状态为 `published`

### 1.4 使用动态生成的 API

```python
async def test_customer_api():
    """测试客户 API"""
    
    workspace_id = "your-workspace-id"
    base_url = "http://localhost:8000/api/v1/data/customer"
    
    async with httpx.AsyncClient() as client:
        
        # 1. 创建客户
        customer_data = {
            "name": "张三科技有限公司",
            "email": "contact@zhangsan-tech.com",
            "phone": "13800138000",
            "company": "张三科技有限公司",
            "industry": "technology",
            "status": "active",
            "address": "北京市朝阳区科技园区1号楼",
            "tags": ["VIP客户", "技术合作", "长期合作"],
            "notes": "重要合作伙伴，技术实力强",
            "last_contact_date": "2024-12-03T10:30:00"
        }
        
        response = await client.post(
            f"{base_url}?workspace_id={workspace_id}",
            json=customer_data,
            headers={"Authorization": "Bearer your-token"}
        )
        
        if response.status_code == 201:
            customer = response.json()
            print(f"✅ 客户创建成功: {customer['id']}")
            customer_id = customer['id']
        else:
            print(f"❌ 创建失败: {response.text}")
            return
        
        # 2. 查询客户列表
        response = await client.get(
            f"{base_url}?workspace_id={workspace_id}&page=1&page_size=10&status=active",
            headers={"Authorization": "Bearer your-token"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 查询成功，共 {result['total']} 个客户")
            for customer in result['items']:
                print(f"   - {customer['name']} ({customer['email']})")
        
        # 3. 获取客户详情
        response = await client.get(
            f"{base_url}/{customer_id}?workspace_id={workspace_id}",
            headers={"Authorization": "Bearer your-token"}
        )
        
        if response.status_code == 200:
            customer = response.json()
            print(f"✅ 客户详情: {customer['name']}")
        
        # 4. 更新客户
        update_data = {
            "status": "inactive",
            "notes": "客户暂停合作"
        }
        
        response = await client.put(
            f"{base_url}/{customer_id}?workspace_id={workspace_id}",
            json=update_data,
            headers={"Authorization": "Bearer your-token"}
        )
        
        if response.status_code == 200:
            print("✅ 客户更新成功")
        
        # 5. 删除客户（软删除）
        response = await client.delete(
            f"{base_url}/{customer_id}?workspace_id={workspace_id}",
            headers={"Authorization": "Bearer your-token"}
        )
        
        if response.status_code == 200:
            print("✅ 客户删除成功")

# 测试 API
await test_customer_api()
```

## 示例 2：创建订单管理模型

### 2.1 定义订单模型

```json
{
  "name": "order",
  "display_name": "订单",
  "description": "订单管理系统",
  "table_name": "orders",
  "category": "sales",
  "icon": "shopping-cart",
  "enable_audit": true,
  "enable_soft_delete": true,
  "fields": [
    {
      "name": "order_number",
      "display_name": "订单号",
      "field_type": "string",
      "is_required": true,
      "is_unique": true,
      "is_indexed": true,
      "validation_rules": {
        "pattern": "^ORD\\d{8}$"
      },
      "ui_config": {
        "widget": "input",
        "placeholder": "ORD20241203",
        "help_text": "格式：ORD + 8位数字"
      }
    },
    {
      "name": "customer_id",
      "display_name": "客户",
      "field_type": "foreign_key",
      "is_required": true,
      "is_indexed": true,
      "relation_config": {
        "target_model": "customer",
        "relation_type": "many_to_one",
        "on_delete": "RESTRICT",
        "display_field": "name"
      },
      "ui_config": {
        "widget": "select",
        "searchable": true,
        "help_text": "选择客户"
      }
    },
    {
      "name": "order_date",
      "display_name": "订单日期",
      "field_type": "date",
      "is_required": true,
      "is_indexed": true,
      "default_value": "CURRENT_DATE",
      "ui_config": {
        "widget": "date-picker"
      }
    },
    {
      "name": "status",
      "display_name": "订单状态",
      "field_type": "string",
      "is_required": true,
      "is_indexed": true,
      "default_value": "'pending'",
      "validation_rules": {
        "enum": ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
      },
      "ui_config": {
        "widget": "select",
        "options": [
          {"label": "待确认", "value": "pending", "color": "orange"},
          {"label": "已确认", "value": "confirmed", "color": "blue"},
          {"label": "处理中", "value": "processing", "color": "purple"},
          {"label": "已发货", "value": "shipped", "color": "cyan"},
          {"label": "已送达", "value": "delivered", "color": "green"},
          {"label": "已取消", "value": "cancelled", "color": "red"}
        ]
      }
    },
    {
      "name": "total_amount",
      "display_name": "订单总额",
      "field_type": "decimal",
      "db_type": "DECIMAL(10,2)",
      "is_required": true,
      "validation_rules": {
        "min": 0,
        "max": 999999.99
      },
      "ui_config": {
        "widget": "number-input",
        "prefix": "¥",
        "precision": 2
      }
    },
    {
      "name": "items",
      "display_name": "订单商品",
      "field_type": "json",
      "is_required": true,
      "ui_config": {
        "widget": "json-editor",
        "schema": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "product_id": {"type": "string"},
              "product_name": {"type": "string"},
              "quantity": {"type": "number"},
              "unit_price": {"type": "number"},
              "subtotal": {"type": "number"}
            }
          }
        }
      }
    },
    {
      "name": "shipping_address",
      "display_name": "收货地址",
      "field_type": "json",
      "is_required": true,
      "ui_config": {
        "widget": "address-input",
        "schema": {
          "type": "object",
          "properties": {
            "recipient": {"type": "string"},
            "phone": {"type": "string"},
            "province": {"type": "string"},
            "city": {"type": "string"},
            "district": {"type": "string"},
            "detail": {"type": "string"}
          }
        }
      }
    },
    {
      "name": "notes",
      "display_name": "订单备注",
      "field_type": "text",
      "is_required": false,
      "ui_config": {
        "widget": "textarea",
        "placeholder": "订单备注信息..."
      }
    }
  ]
}
```

### 2.2 定义关系

```python
async def create_order_customer_relation():
    """创建订单-客户关系"""
    
    relation_data = {
        "source_model_id": "order_model_id",
        "target_model_id": "customer_model_id", 
        "name": "customer",
        "relation_type": "many_to_one",
        "foreign_key_field": "customer_id",
        "on_delete": "RESTRICT",
        "on_update": "CASCADE"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/metadata/relations",
            json=relation_data,
            headers={"Authorization": "Bearer your-token"}
        )
        
        if response.status_code == 201:
            print("✅ 关系创建成功")
        else:
            print(f"❌ 关系创建失败: {response.text}")
```

## 示例 3：创建动态页面

### 3.1 定义客户管理页面

```json
{
  "name": "customer_management",
  "display_name": "客户管理",
  "description": "客户信息管理页面",
  "route_path": "/customers",
  "layout_config": {
    "type": "grid",
    "columns": 24,
    "gutter": 16
  },
  "components": [
    {
      "id": "search_form",
      "type": "SearchForm",
      "props": {
        "fields": [
          {
            "name": "name",
            "label": "客户名称",
            "type": "input",
            "placeholder": "请输入客户名称"
          },
          {
            "name": "status",
            "label": "状态",
            "type": "select",
            "options": [
              {"label": "全部", "value": ""},
              {"label": "活跃", "value": "active"},
              {"label": "停用", "value": "inactive"}
            ]
          }
        ]
      },
      "layout": {
        "span": 24,
        "order": 1
      }
    },
    {
      "id": "customer_table",
      "type": "DataTable",
      "props": {
        "columns": [
          {
            "key": "name",
            "title": "客户名称",
            "width": 200,
            "sortable": true
          },
          {
            "key": "email", 
            "title": "邮箱",
            "width": 250
          },
          {
            "key": "phone",
            "title": "电话",
            "width": 150
          },
          {
            "key": "company",
            "title": "公司",
            "width": 200
          },
          {
            "key": "status",
            "title": "状态",
            "width": 100,
            "render": "status_tag"
          },
          {
            "key": "created_at",
            "title": "创建时间",
            "width": 180,
            "render": "datetime"
          },
          {
            "key": "actions",
            "title": "操作",
            "width": 150,
            "render": "actions"
          }
        ],
        "pagination": true,
        "selection": true
      },
      "layout": {
        "span": 24,
        "order": 2
      }
    }
  ],
  "data_binding": {
    "customer_table": {
      "source": "api",
      "api": "/api/v1/data/customer",
      "method": "GET",
      "params": {
        "workspace_id": "{{workspace_id}}",
        "page": "{{pagination.current}}",
        "page_size": "{{pagination.pageSize}}",
        "name": "{{search_form.name}}",
        "status": "{{search_form.status}}"
      }
    }
  },
  "permissions": {
    "view": ["admin", "sales", "support"],
    "create": ["admin", "sales"],
    "update": ["admin", "sales"],
    "delete": ["admin"]
  }
}
```

### 3.2 创建页面

```python
async def create_customer_page():
    """创建客户管理页面"""
    
    page_data = { ... }  # 如上所示
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/metadata/pages",
            json=page_data,
            headers={
                "Authorization": "Bearer your-token",
                "X-Workspace-ID": "your-workspace-id"
            }
        )
        
        if response.status_code == 201:
            page = response.json()
            print(f"✅ 页面创建成功: {page['route_path']}")
            return page
        else:
            print(f"❌ 页面创建失败: {response.text}")
            return None
```

## 示例 4：模型版本管理

### 4.1 更新模型字段

```python
async def update_customer_model():
    """更新客户模型 - 添加新字段"""
    
    # 添加新字段：客户等级
    new_field = {
        "name": "level",
        "display_name": "客户等级",
        "field_type": "string",
        "is_required": false,
        "default_value": "'bronze'",
        "validation_rules": {
            "enum": ["bronze", "silver", "gold", "platinum"]
        },
        "ui_config": {
            "widget": "select",
            "options": [
                {"label": "青铜", "value": "bronze"},
                {"label": "白银", "value": "silver"},
                {"label": "黄金", "value": "gold"},
                {"label": "铂金", "value": "platinum"}
            ]
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/api/v1/metadata/models/{model_id}/fields",
            json=new_field,
            headers={"Authorization": "Bearer your-token"}
        )
        
        if response.status_code == 201:
            print("✅ 字段添加成功")
            
            # 重新发布模型以应用数据库变更
            await republish_model(model_id)
        else:
            print(f"❌ 字段添加失败: {response.text}")

async def republish_model(model_id: str):
    """重新发布模型"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/api/v1/metadata/models/{model_id}/republish",
            headers={"Authorization": "Bearer your-token"}
        )
        
        if response.status_code == 200:
            print("✅ 模型重新发布成功")
        else:
            print(f"❌ 重新发布失败: {response.text}")
```

### 4.2 查看版本历史

```python
async def get_model_versions(model_id: str):
    """查看模型版本历史"""
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/api/v1/metadata/models/{model_id}/versions",
            headers={"Authorization": "Bearer your-token"}
        )
        
        if response.status_code == 200:
            versions = response.json()
            print(f"模型版本历史（共 {len(versions)} 个版本）:")
            
            for version in versions:
                print(f"  版本 {version['version']}:")
                print(f"    创建时间: {version['created_at']}")
                print(f"    创建者: {version['created_by_name']}")
                print(f"    变更说明: {version['change_log']}")
                print()
        else:
            print(f"❌ 获取版本历史失败: {response.text}")
```

## 示例 5：批量数据操作

### 5.1 批量导入客户数据

```python
async def bulk_import_customers():
    """批量导入客户数据"""
    
    customers_data = [
        {
            "name": "阿里巴巴集团",
            "email": "contact@alibaba.com",
            "phone": "13800000001",
            "company": "阿里巴巴集团",
            "industry": "technology",
            "status": "active",
            "tags": ["大客户", "互联网", "电商"]
        },
        {
            "name": "腾讯科技",
            "email": "contact@tencent.com", 
            "phone": "13800000002",
            "company": "腾讯科技有限公司",
            "industry": "technology",
            "status": "active",
            "tags": ["大客户", "互联网", "游戏"]
        },
        {
            "name": "字节跳动",
            "email": "contact@bytedance.com",
            "phone": "13800000003", 
            "company": "字节跳动有限公司",
            "industry": "technology",
            "status": "active",
            "tags": ["大客户", "互联网", "短视频"]
        }
    ]
    
    workspace_id = "your-workspace-id"
    
    async with httpx.AsyncClient() as client:
        success_count = 0
        
        for customer_data in customers_data:
            response = await client.post(
                f"http://localhost:8000/api/v1/data/customer?workspace_id={workspace_id}",
                json=customer_data,
                headers={"Authorization": "Bearer your-token"}
            )
            
            if response.status_code == 201:
                success_count += 1
                print(f"✅ {customer_data['name']} 导入成功")
            else:
                print(f"❌ {customer_data['name']} 导入失败: {response.text}")
        
        print(f"\n批量导入完成，成功 {success_count}/{len(customers_data)} 条记录")
```

### 5.2 批量更新数据

```python
async def bulk_update_customer_status():
    """批量更新客户状态"""
    
    workspace_id = "your-workspace-id"
    
    async with httpx.AsyncClient() as client:
        # 1. 查询需要更新的客户
        response = await client.get(
            f"http://localhost:8000/api/v1/data/customer?workspace_id={workspace_id}&status=pending",
            headers={"Authorization": "Bearer your-token"}
        )
        
        if response.status_code != 200:
            print("❌ 查询客户失败")
            return
        
        customers = response.json()['items']
        print(f"找到 {len(customers)} 个待审核客户")
        
        # 2. 批量更新状态
        update_count = 0
        for customer in customers:
            update_response = await client.put(
                f"http://localhost:8000/api/v1/data/customer/{customer['id']}?workspace_id={workspace_id}",
                json={"status": "active"},
                headers={"Authorization": "Bearer your-token"}
            )
            
            if update_response.status_code == 200:
                update_count += 1
                print(f"✅ {customer['name']} 状态更新成功")
            else:
                print(f"❌ {customer['name']} 状态更新失败")
        
        print(f"\n批量更新完成，成功 {update_count}/{len(customers)} 条记录")
```

## 总结

通过以上示例，我们可以看到元数据引擎的强大功能：

1. **快速建模**：通过 JSON 配置快速定义数据模型
2. **自动化**：自动生成数据库表、ORM 和 API
3. **灵活配置**：支持丰富的字段类型和验证规则
4. **UI 集成**：自动生成表单和页面组件
5. **版本管理**：支持模型版本控制和变更追踪
6. **批量操作**：支持批量数据导入和更新

这些功能大大提高了开发效率，使业务人员也能参与到数据模型的设计中来。