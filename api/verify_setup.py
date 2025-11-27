#!/usr/bin/env python3
"""验证项目初始化和基础设施搭建是否完成。"""

import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """检查文件是否存在。"""
    path = Path(filepath)
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists


def check_directory_exists(dirpath: str, description: str) -> bool:
    """检查目录是否存在。"""
    path = Path(dirpath)
    exists = path.is_dir()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {dirpath}")
    return exists


def main():
    """主验证函数。"""
    print("=" * 70)
    print("项目初始化和基础设施搭建验证")
    print("=" * 70)

    all_checks = []

    # 1. 检查目录结构
    print("\n📁 目录结构检查:")
    directories = [
        ("app/api/v1", "API v1 目录"),
        ("app/core", "核心配置目录"),
        ("app/models", "数据模型目录"),
        ("app/schemas", "Schemas 目录"),
        ("app/services", "服务层目录"),
        ("app/repositories", "数据访问层目录"),
        ("app/middleware", "中间件目录"),
        ("app/engine/nodes", "工作流节点目录"),
        ("app/tasks", "Celery 任务目录"),
        ("app/utils/llm", "LLM 工具目录"),
        ("tests", "测试目录"),
    ]

    for dirpath, description in directories:
        all_checks.append(check_directory_exists(dirpath, description))

    # 2. 检查核心配置文件
    print("\n⚙️  核心配置文件检查:")
    core_files = [
        ("app/core/config.py", "配置管理"),
        ("app/core/database.py", "PostgreSQL 连接"),
        ("app/core/mongodb.py", "MongoDB 连接"),
        ("app/core/redis.py", "Redis 连接"),
        ("app/core/logging.py", "日志配置"),
        ("app/core/sentry.py", "Sentry 配置"),
        ("app/core/celery.py", "Celery 配置"),
    ]

    for filepath, description in core_files:
        all_checks.append(check_file_exists(filepath, description))

    # 3. 检查应用文件
    print("\n🚀 应用文件检查:")
    app_files = [
        ("app/main.py", "FastAPI 应用"),
        ("app/__init__.py", "App 包初始化"),
    ]

    for filepath, description in app_files:
        all_checks.append(check_file_exists(filepath, description))

    # 4. 检查配置文件
    print("\n📝 配置文件检查:")
    config_files = [
        (".env", "环境变量文件"),
        (".env.example", "环境变量示例"),
        ("pyproject.toml", "项目配置"),
    ]

    for filepath, description in config_files:
        all_checks.append(check_file_exists(filepath, description))

    # 5. 检查测试文件
    print("\n🧪 测试文件检查:")
    test_files = [
        ("tests/__init__.py", "测试包初始化"),
        ("tests/conftest.py", "Pytest 配置"),
        ("tests/test_infrastructure.py", "基础设施测试"),
    ]

    for filepath, description in test_files:
        all_checks.append(check_file_exists(filepath, description))

    # 6. 检查 Docker 文件
    print("\n🐳 Docker 文件检查:")
    docker_files = [
        ("Dockerfile", "Docker 镜像配置"),
        ("docker-compose.yml", "Docker Compose 配置"),
        (".dockerignore", "Docker 忽略文件"),
    ]

    for filepath, description in docker_files:
        all_checks.append(check_file_exists(filepath, description))

    # 7. 检查文档文件
    print("\n📚 文档文件检查:")
    doc_files = [
        ("README.md", "项目说明文档"),
        ("SETUP.md", "设置完成报告"),
        (".gitignore", "Git 忽略文件"),
    ]

    for filepath, description in doc_files:
        all_checks.append(check_file_exists(filepath, description))

    # 总结
    print("\n" + "=" * 70)
    total = len(all_checks)
    passed = sum(all_checks)
    failed = total - passed

    print(f"总计: {total} 项检查")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")

    if failed == 0:
        print("\n🎉 恭喜！项目初始化和基础设施搭建已完成！")
        print("=" * 70)
        return 0
    else:
        print(f"\n⚠️  警告：有 {failed} 项检查未通过，请检查缺失的文件或目录。")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
