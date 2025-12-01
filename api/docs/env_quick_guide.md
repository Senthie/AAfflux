# .env 文件读取 - 快速指南

## 🎯 核心答案

项目使用 **`pydantic-settings`** 库自动读取 `.env` 文件。

## 📝 简单三步

### 1️⃣ 定义配置类 (`app/core/config.py`)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 👇 这里告诉 Pydantic 读取 .env 文件
    model_config = SettingsConfigDict(
        env_file=".env",              # 📁 .env 文件路径
        env_file_encoding="utf-8",    # 📝 UTF-8 编码
        case_sensitive=False,         # 🔤 不区分大小写
        extra="ignore",               # ⚠️ 忽略额外变量
    )
    
    # 定义配置字段
    app_name: str = "Low-Code Platform Backend"
    database_url: str
    jwt_secret_key: str
```

### 2️⃣ 创建配置实例

```python
# app/core/config.py 最后一行
settings = Settings()  # 👈 这一行触发 .env 文件读取！
```

**当执行 `Settings()` 时，Pydantic 自动：**

1. 查找 `.env` 文件
2. 解析文件内容
3. 读取系统环境变量
4. 合并配置
5. 验证数据类型
6. 返回配置对象

### 3️⃣ 使用配置

```python
# 在任何地方导入并使用
from app.core.config import settings

print(settings.app_name)      # "Low-Code Platform Backend"
print(settings.database_url)  # "postgresql+asyncpg://..."
```

## 🔄 完整流程

```
启动应用
   ↓
导入 config.py
   ↓
执行 settings = Settings()
   ↓
Pydantic 自动读取 .env
   ↓
配置可用！
```

## 📁 .env 文件格式

```bash
# 注释
APP_NAME="Low-Code Platform Backend"
DEBUG=true
PORT=8000
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db
```

## 🎨 配置优先级

```
默认值 < .env 文件 < 环境变量 < 构造参数
```

示例：

```python
# 1. 默认值
class Settings(BaseSettings):
    port: int = 8000  # 默认 8000

# 2. .env 文件
# PORT=9000

# 3. 环境变量
# export PORT=10000

# 4. 构造参数
settings = Settings(port=11000)

# 结果：port = 11000 (构造参数优先级最高)
```

## ✅ 验证读取成功

```python
from app.core.config import settings

# 打印配置
print(f"App Name: {settings.app_name}")
print(f"Database: {settings.database_url}")
print(f"Debug: {settings.debug}")
```

## 🔍 关键代码位置

| 文件 | 作用 |
|------|------|
| `app/core/config.py` | 配置类定义 |
| `.env` | 环境变量文件 |
| `app/main.py` | 使用配置 |

## 💡 重要提示

1. **自动读取**：不需要手动调用任何读取函数
2. **单例模式**：`settings` 是全局单例，整个应用共享
3. **类型安全**：自动验证和转换数据类型
4. **验证规则**：支持 `Field()` 验证器

## 🛠️ 调试技巧

检查 .env 是否被读取：

```python
from app.core.config import settings

# 方法 1：打印配置
print(settings.model_dump())

# 方法 2：检查特定值
print(f"Database URL: {settings.database_url}")

# 方法 3：检查文件是否存在
from pathlib import Path
print(f".env exists: {Path('.env').exists()}")
```

## 📚 更多信息

- 详细文档：`docs/env_configuration.md`
- 配置文件：`app/core/config.py`
- 示例文件：`.env.example`
