#!/usr/bin/env python3
"""演示如何读取 .env 文件的示例"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def demo_basic_usage():
    """基础用法演示"""
    print("=" * 70)
    print("1. 基础用法 - 自动读取 .env 文件")
    print("=" * 70)

    from app.core.config import settings

    print(f"✅ 应用名称: {settings.app_name}")
    print(f"✅ 调试模式: {settings.debug}")
    print(f"✅ 端口: {settings.port}")
    print(f"✅ 数据库 URL: {settings.database_url}")
    print(f"✅ JWT 密钥长度: {len(settings.jwt_secret_key)} 字符")
    print()


def demo_priority():
    """配置优先级演示"""
    print("=" * 70)
    print("2. 配置优先级演示")
    print("=" * 70)

    from pydantic_settings import BaseSettings, SettingsConfigDict

    class DemoSettings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            case_sensitive=False,
        )

        # 默认值
        demo_value: str = "default_value"

    # 场景 1: 只有默认值
    settings1 = DemoSettings()
    print(f"场景 1 (只有默认值): {settings1.demo_value}")

    # 场景 2: .env 文件中有值（假设 .env 中有 DEMO_VALUE=from_env）
    # settings2 = DemoSettings()
    # print(f"场景 2 (.env 文件): {settings2.demo_value}")

    # 场景 3: 通过构造函数传递（优先级最高）
    settings3 = DemoSettings(demo_value="from_constructor")
    print(f"场景 3 (构造函数): {settings3.demo_value}")
    print()


def demo_validation():
    """字段验证演示"""
    print("=" * 70)
    print("3. 字段验证演示")
    print("=" * 70)

    from pydantic import Field, ValidationError
    from pydantic_settings import BaseSettings

    class ValidatedSettings(BaseSettings):
        # 必填字段
        required_field: str = Field(..., description="必填字段")

        # 最小长度验证
        password: str = Field(..., min_length=8, description="至少 8 字符")

        # 数值范围验证
        port: int = Field(default=8000, ge=1, le=65535, description="端口号 1-65535")

    try:
        # ❌ 这会失败：密码太短
        settings = ValidatedSettings(required_field="test", password="short")  # 只有 5 字符
    except ValidationError as e:
        print("❌ 验证失败:")
        for error in e.errors():
            print(f"   - {error['loc'][0]}: {error['msg']}")

    # ✅ 这会成功
    settings = ValidatedSettings(required_field="test", password="long_enough_password")
    print(f"✅ 验证成功: password 长度 = {len(settings.password)}")
    print()


def demo_custom_validator():
    """自定义验证器演示"""
    print("=" * 70)
    print("4. 自定义验证器演示")
    print("=" * 70)

    from typing import Optional
    from pydantic import field_validator
    from pydantic_settings import BaseSettings

    class SmartSettings(BaseSettings):
        redis_url: str = "redis://localhost:6379"
        celery_broker_url: Optional[str] = None

        @field_validator("celery_broker_url", mode="before")
        @classmethod
        def set_celery_broker(cls, v: Optional[str], info) -> str:
            """如果未设置 celery_broker_url，自动使用 redis_url"""
            if v is None:
                redis_url = info.data.get("redis_url")
                if redis_url:
                    print(f"   ℹ️  celery_broker_url 未设置，自动使用 redis_url")
                    return redis_url
            return v or ""

    settings = SmartSettings()
    print(f"✅ Redis URL: {settings.redis_url}")
    print(f"✅ Celery Broker URL: {settings.celery_broker_url}")
    print(f"✅ 两者相同: {settings.redis_url == settings.celery_broker_url}")
    print()


def demo_env_file_check():
    """检查 .env 文件"""
    print("=" * 70)
    print("5. .env 文件检查")
    print("=" * 70)

    env_path = Path(".env")

    if env_path.exists():
        print(f"✅ .env 文件存在")
        print(f"   路径: {env_path.absolute()}")
        print(f"   大小: {env_path.stat().st_size} 字节")

        # 读取前几行
        print("\n   前 5 行内容:")
        with open(env_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if i > 5:
                    break
                line = line.strip()
                if line and not line.startswith("#"):
                    # 隐藏敏感信息
                    if "=" in line:
                        key, _ = line.split("=", 1)
                        print(f"   {i}. {key}=***")
                    else:
                        print(f"   {i}. {line}")
    else:
        print(f"❌ .env 文件不存在")
        print(f"   期望路径: {env_path.absolute()}")
    print()


def main():
    """主函数"""
    print("\n")
    print("🔧 环境变量配置演示")
    print("=" * 70)
    print()

    try:
        demo_env_file_check()
        demo_basic_usage()
        demo_priority()
        demo_validation()
        demo_custom_validator()

        print("=" * 70)
        print("✅ 所有演示完成！")
        print("=" * 70)
        print()
        print("💡 提示:")
        print("   - .env 文件在项目根目录")
        print("   - 配置类在 app/core/config.py")
        print("   - 详细文档在 docs/env_configuration.md")
        print()

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
