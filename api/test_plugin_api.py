"""
Plugin API 测试脚本

这个脚本用于测试 Plugin API 的基本功能。
需要先启动应用，然后运行此脚本。

使用方法：
    python test_plugin_api.py
"""

import json
from uuid import uuid4

import requests

# 配置
BASE_URL = 'http://localhost:8000/api/v1'
# 注意：需要替换为实际的 JWT token
TOKEN = 'your_jwt_token_here'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}

# 测试用的 workspace_id（需要替换为实际的 workspace_id）
WORKSPACE_ID = str(uuid4())


def test_create_plugin():
    """测试创建插件"""
    print('\n=== 测试创建插件 ===')

    plugin_data = {
        'name': f'test-plugin-{uuid4().hex[:8]}',
        'display_name': 'Test Plugin',
        'description': 'A test plugin for API testing',
        'version': '1.0.0',
        'author': 'Test Author',
        'icon': 'https://example.com/icon.png',
        'category': 'tool',
        'plugin_type': 'custom',
        'manifest': {'config_schema': {}, 'capabilities': ['test']},
        'source_url': 'https://github.com/test/plugin',
        'documentation_url': 'https://docs.example.com',
        'is_active': True,
        'is_verified': False,
    }

    response = requests.post(f'{BASE_URL}/plugins/', headers=HEADERS, json=plugin_data)

    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}')

    if response.status_code == 200:
        return response.json()['data']['id']
    return None


def test_list_plugins():
    """测试获取插件列表"""
    print('\n=== 测试获取插件列表 ===')

    response = requests.get(f'{BASE_URL}/plugins/?skip=0&limit=10', headers=HEADERS)

    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}')


def test_get_plugin(plugin_id):
    """测试获取插件详情"""
    print(f'\n=== 测试获取插件详情 (ID: {plugin_id}) ===')

    response = requests.get(f'{BASE_URL}/plugins/{plugin_id}', headers=HEADERS)

    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}')


def test_update_plugin(plugin_id):
    """测试更新插件"""
    print(f'\n=== 测试更新插件 (ID: {plugin_id}) ===')

    update_data = {
        'display_name': 'Updated Test Plugin',
        'description': 'Updated description',
        'is_active': False,
    }

    response = requests.put(f'{BASE_URL}/plugins/{plugin_id}', headers=HEADERS, json=update_data)

    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}')


def test_install_plugin(plugin_id):
    """测试安装插件"""
    print(f'\n=== 测试安装插件 (Plugin ID: {plugin_id}, Workspace ID: {WORKSPACE_ID}) ===')

    install_data = {
        'plugin_id': plugin_id,
        'config': {'api_key': 'test_key', 'endpoint': 'https://api.example.com'},
        'is_enabled': True,
    }

    response = requests.post(
        f'{BASE_URL}/plugins/install?workspace_id={WORKSPACE_ID}',
        headers=HEADERS,
        json=install_data,
    )

    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}')

    if response.status_code == 200:
        return response.json()['data']['id']
    return None


def test_list_installed_plugins():
    """测试获取已安装插件列表"""
    print(f'\n=== 测试获取已安装插件列表 (Workspace ID: {WORKSPACE_ID}) ===')

    response = requests.get(
        f'{BASE_URL}/plugins/installed?workspace_id={WORKSPACE_ID}&skip=0&limit=10', headers=HEADERS
    )

    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}')


def test_update_installed_plugin(installed_plugin_id):
    """测试更新已安装插件"""
    print(f'\n=== 测试更新已安装插件 (ID: {installed_plugin_id}) ===')

    update_data = {
        'config': {'api_key': 'new_test_key', 'endpoint': 'https://new-api.example.com'},
        'is_enabled': False,
    }

    response = requests.put(
        f'{BASE_URL}/plugins/installed/{installed_plugin_id}?workspace_id={WORKSPACE_ID}',
        headers=HEADERS,
        json=update_data,
    )

    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}')


def test_uninstall_plugin(installed_plugin_id):
    """测试卸载插件"""
    print(f'\n=== 测试卸载插件 (ID: {installed_plugin_id}) ===')

    response = requests.delete(
        f'{BASE_URL}/plugins/installed/{installed_plugin_id}?workspace_id={WORKSPACE_ID}',
        headers=HEADERS,
    )

    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}')


def test_delete_plugin(plugin_id):
    """测试删除插件"""
    print(f'\n=== 测试删除插件 (ID: {plugin_id}) ===')

    response = requests.delete(f'{BASE_URL}/plugins/{plugin_id}', headers=HEADERS)

    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}')


def main():
    """运行所有测试"""
    print('=' * 60)
    print('Plugin API 测试')
    print('=' * 60)
    print('\n注意：请确保已启动应用并替换 TOKEN 和 WORKSPACE_ID')
    print(f'BASE_URL: {BASE_URL}')
    print(f'TOKEN: {TOKEN[:20]}...' if len(TOKEN) > 20 else f'TOKEN: {TOKEN}')
    print(f'WORKSPACE_ID: {WORKSPACE_ID}')

    # 1. 创建插件
    plugin_id = test_create_plugin()
    if not plugin_id:
        print('\n❌ 创建插件失败，停止测试')
        return

    # 2. 获取插件列表
    test_list_plugins()

    # 3. 获取插件详情
    test_get_plugin(plugin_id)

    # 4. 更新插件
    test_update_plugin(plugin_id)

    # 5. 安装插件
    installed_plugin_id = test_install_plugin(plugin_id)
    if not installed_plugin_id:
        print('\n❌ 安装插件失败')
    else:
        # 6. 获取已安装插件列表
        test_list_installed_plugins()

        # 7. 更新已安装插件
        test_update_installed_plugin(installed_plugin_id)

        # 8. 卸载插件
        test_uninstall_plugin(installed_plugin_id)

    # 9. 删除插件
    test_delete_plugin(plugin_id)

    print('\n' + '=' * 60)
    print('测试完成')
    print('=' * 60)


if __name__ == '__main__':
    main()
