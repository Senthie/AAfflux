"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-02 08:21:39
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-04 07:38:56
FilePath: /api/setup_database.py
Description: Database setup and migration script.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from pathlib import Path
import subprocess
import sys

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_command(command: str, description: str) -> bool:
    """Run a shell command and return success status."""
    print(f'🔄 {description}...')
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f'✅ {description} - 成功')
        if result.stdout.strip():
            # Only show first few lines to avoid clutter
            lines = result.stdout.strip().split('\n')
            if len(lines) <= 3:
                print(f'   输出: {result.stdout.strip()}')
            else:
                print(f'   输出: {lines[0]}... (共 {len(lines)} 行)')
        return True
    except subprocess.CalledProcessError as e:
        print(f'❌ {description} - 失败')
        if e.stdout:
            print(f'   输出: {e.stdout}')
        if e.stderr:
            print(f'   错误: {e.stderr}')
        return False


def main():
    """Main setup function."""
    print('🚀 数据库设置和迁移')
    print('=' * 50)

    # Load environment variables
    print('📁 加载环境变量...')
    load_dotenv()
    print('✅ 环境变量已从 .env 文件加载')

    # Verify configuration
    print('\n🔧 验证配置...')
    if not run_command('python verify_config.py', '配置验证'):
        print('❌ 配置验证失败，请检查 .env 文件')
        return False

    # Check current migration status
    print('\n📋 检查迁移状态...')
    run_command('alembic current', '当前迁移状态')

    # Run migrations
    print('\n🔄 运行数据库迁移...')
    if not run_command('alembic upgrade head', '数据库迁移'):
        print('❌ 数据库迁移失败')
        return False

    print('\n' + '=' * 50)
    print('🎉 数据库设置完成！')
    print('\n📋 下一步:')
    print('  1. 启动应用: uvicorn app.main:app --reload')
    print('  2. 访问 API 文档: http://localhost:8000/docs')
    print('  3. 查看数据库状态: alembic current')
    print('  4. 验证连接: python verify_config.py')

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
