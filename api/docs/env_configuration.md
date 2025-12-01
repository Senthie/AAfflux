# 环境变量配置详解 - .env 文件是如何被读取的

## 🔍 核心机制

项目使用 **`pydantic-settings`** 库自动读取 `.env` 文件。

## 📋 完整流程

### 1. 配置类定义 (`app/core/config.py`)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """应用配置类"""
    
    # 🔑 关键配置：告诉 Pydantic 如何读取 .env
    model_config = SettingsConfigDict(
        env_file=".env",              # 📁 指定 .env 文件路径
        env_file_encoding="utf-8",    # 📝 文件编码
        case_sensitive=False,         # 🔤 不区分大小写
        extra="ignore",               # ⚠️ 忽略额外的环境变量
    )
    
    # 定义配置字段
    app_name: str = "Low-Code Platform Backend"
    database_url: str = Field(..., description="PostgreSQL connection URL")
    # ... 更多字段
```

### 2. 自动读取过程

```
启动应用
   ↓
导入 config.py
   ↓
创建 Settings() 实例
   ↓
Pydantic 自动执行：
   1. 读取 .env 文件
   2. 读取系统环境变量
   3. 合并配置（环境变量优先级更高）
   4. 验证数据类型
   5. 返回配置对象
   ↓
settings 对象可用
```

### 3. 实例化配置 (`app/core/config.py` 最后一行)

```python
# 全局配置实例 - 在导入时自动创建
settings = Settings()
```

**这一行代码触发了整个读取过程！**

## 🎯 详细说明

### SettingsConfigDict 参数详解

```python
model_config = SettingsConfigDict(
    env_file=".env",              # 1️⃣ .env 文件路径
    env_file_encoding="utf-8",    # 2️⃣ 文件编码
    case_sensitive=False,         # 3️⃣ 变量名大小写
    extra="ignore",               # 4️⃣ 额外变量处理
)
```

#### 1️⃣ `env_file=".env"`

- 指定要读取的环境变量文件
- 相对于项目根目录
- 可以指定多个文件：`env_file=[".env", ".env.local"]`

#### 2️⃣ `env_file_encoding="utf-8"`

- 文件编码格式
- 支持中文等特殊字符

#### 3️⃣ `case_sensitive=False`

- 不区分大小写
- `.env` 中的 `DATABASE_URL` 和 `database_url` 都能匹配

#### 4️⃣ `extra="ignore"`

- 忽略 `.env` 中未定义的变量
- 防止意外的配置项导致错误

## 📝 .env 文件格式

### 基本格式

```bash
# 注释
KEY=value
KEY_WITH_UNDERSCORE=value
KEY_WITH_SPACES="value with spaces"
```

### 实际例子 (`.env`)

```bash
# Application
APP_NAME="Low-Code Platform Backend"
DEBUG=true
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/lowcode_platform

# Security
JWT_SECRET_KEY=dev-secret-key-change-in-production-min-32-chars
```

## 🔄 配置优先级

Pydantic Settings 按以下顺序读取配置（后者覆盖前者）：

```
1. 类中的默认值
   ↓
2. .env 文件中的值
   ↓
3. 系统环境变量
   ↓
4. 传递给构造函数的参数
```

### 示例

```python
# 1. 默认值
class Settings(BaseSettings):
    app_name: str = "Default App"  # 默认值

# 2. .env 文件
# APP_NAME="My App from .env"

# 3. 系统环境变量
# export APP_NAME="My App from ENV"

# 4. 构造函数参数
settings = Settings(app_name="My App from Code")

# 最终结果：app_name = "My App from Code"
# 因为构造函数参数优先级最高
```

## 🚀 实际使用流程

### 步骤 1: 应用启动

```python
# app/main.py
from app.core.config import settings  # 👈 导入时自动读取 .env

print(settings.app_name)        # 输出: "Low-Code Platform Backend"
print(settings.database_url)    # 输出: "postgresql+asyncpg://..."
```

### 步骤 2: 在其他模块中使用

```python
# app/core/database.py
from app.core.config import settings

# 使用配置
engine = create_async_engine(
    settings.database_url,      # 👈 从 .env 读取
    pool_size=settings.database_pool_size,
)
```

### 步骤 3: 配置验证

```python
class Settings(BaseSettings):
    # 必填字段（没有默认值）
    database_url: str = Field(..., description="PostgreSQL connection URL")
    
    # 带验证的字段
    jwt_secret_key: str = Field(..., min_length=32)  # 至少 32 字符
    
    # 可选字段
    sentry_dsn: Optional[str] = None
```

如果 `.env` 中缺少必填字段，启动时会报错：

```
ValidationError: 1 validation error for Settings
database_url
  Field required [type=missing]
```

## 🔧 高级功能

### 1. 自定义验证器

```python
class Settings(BaseSettings):
    celery_broker_url: Optional[str] = None
    redis_url: str
    
    @field_validator("celery_broker_url", mode="before")
    @classmethod
    def set_celery_broker(cls, v: Optional[str], info) -> str:
        """如果未设置，自动使用 Redis URL"""
        if v is None:
            redis_url = info.data.get("redis_url")
            if redis_url:
                return redis_url
        return v or ""
```

### 2. 嵌套配置

```python
class DatabaseSettings(BaseSettings):
    url: str
    pool_size: int = 5

class Settings(BaseSettings):
    database: DatabaseSettings
```

### 3. 多环境配置

```python
# 开发环境
settings = Settings(_env_file=".env.development")

# 生产环境
settings = Settings(_env_file=".env.production")
```

## 📊 配置读取流程图

```
┌─────────────────────────────────────┐
│   应用启动 (python app/main.py)     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   导入 config.py                     │
│   from app.core.config import ...   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   执行: settings = Settings()       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Pydantic Settings 自动执行:       │
│   1. 查找 .env 文件                 │
│   2. 解析文件内容                   │
│   3. 读取系统环境变量               │
│   4. 合并配置                       │
│   5. 类型验证                       │
│   6. 字段验证 (min_length 等)      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   返回 settings 对象                │
│   - settings.app_name               │
│   - settings.database_url           │
│   - settings.jwt_secret_key         │
│   - ...                             │
└─────────────────────────────────────┘
```

## 🛠️ 调试技巧

### 1. 查看当前配置

```python
from app.core.config import settings

# 打印所有配置
print(settings.model_dump())

# 打印特定配置
print(f"Database URL: {settings.database_url}")
print(f"Debug Mode: {settings.debug}")
```

### 2. 验证 .env 是否被读取

```python
# 在 config.py 中添加调试代码
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(f"✅ Config loaded: app_name={self.app_name}")
```

### 3. 检查 .env 文件路径

```python
import os
from pathlib import Path

# 检查 .env 文件是否存在
env_path = Path(".env")
print(f".env exists: {env_path.exists()}")
print(f".env absolute path: {env_path.absolute()}")
```

## ⚠️ 常见问题

### 问题 1: .env 文件没有被读取

**原因**：

- .env 文件不在项目根目录
- 文件名拼写错误（`.env` vs `env`）
- 文件编码问题

**解决**：

```bash
# 检查文件位置
ls -la .env

# 检查文件内容
cat .env
```

### 问题 2: 配置值不正确

**原因**：

- 系统环境变量覆盖了 .env 中的值
- .env 文件格式错误

**解决**：

```bash
# 检查系统环境变量
echo $DATABASE_URL

# 取消设置环境变量
unset DATABASE_URL
```

### 问题 3: 验证错误

**错误信息**：

```
ValidationError: 1 validation error for Settings
jwt_secret_key
  String should have at least 32 characters
```

**解决**：
确保 .env 中的值符合验证规则：

```bash
# ❌ 错误：太短
JWT_SECRET_KEY=short

# ✅ 正确：至少 32 字符
JWT_SECRET_KEY=dev-secret-key-change-in-production-min-32-chars
```

## 📚 总结

1. **自动读取**：`pydantic-settings` 在创建 `Settings()` 实例时自动读取 `.env`
2. **配置优先级**：默认值 < .env 文件 < 环境变量 < 构造参数
3. **类型安全**：自动验证和转换数据类型
4. **验证规则**：支持 `Field()` 验证器（min_length, regex 等）
5. **全局单例**：`settings = Settings()` 创建全局配置对象

## 🔗 相关文件

- `app/core/config.py` - 配置类定义
- `.env` - 开发环境配置
- `.env.example` - 配置模板

## 📖 参考资料

- [Pydantic Settings 文档](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [环境变量最佳实践](https://12factor.net/config)
