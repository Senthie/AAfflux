"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-30 17:03:32
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-31 11:45:45
FilePath: /api/tests/unit/test_http_node.py
Description: HTTP Node 的测试

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from random import randint
from uuid import uuid4

import httpx
import pytest

from app.engine.execution_context import ExecutionContext
from app.engine.nodes.base.emum import NodeTypeEnum
from app.engine.nodes.base.exc import NodeExecutionError
from app.engine.nodes.http.http_node import HTTPNodeExecutor
from app.models.workflow.workflow import ExecutionRecordModel, NodeModel, WorkflowModel


# ============ Fixtures ============
@pytest.fixture
def workflow():
    """创建测试工作流"""
    return WorkflowModel(
        name='Test Workflow',
    )


@pytest.fixture
def execution_record(workflow):
    """创建执行记录"""
    return ExecutionRecordModel(
        workflow_id=workflow.id,
        inputs={},
        status='PENDING',
    )


@pytest.fixture
def context(workflow, execution_record):
    """创建执行上下文"""
    return ExecutionContext(workflow, execution_record, {})


class TestHttpNode:
    """HTTP Node 测试类"""

    @pytest.fixture
    def http_executor(self):
        """创建 HTTP 执行器实例"""
        return HTTPNodeExecutor()

    def create_http_node(self, method: str, url: str, **kwargs) -> NodeModel:
        """创建 HTTP 节点的辅助方法"""
        config = {
            'title': f'{method} Request',
            'method': method,
            'url': url,
            'headers': kwargs.get('headers', {}),
            'params': kwargs.get('params', {}),
            'body': kwargs.get('body'),
            'timeout': kwargs.get('timeout', 30),
            'follow_redirects': kwargs.get('follow_redirects', True),
        }
        return NodeModel(
            workflow_id=uuid4(),
            type=NodeTypeEnum.HTTP.value,
            name=f'{method} Request',
            config=config,
            position={'x': 0, 'y': 0},
        )

    async def test_get_request(self, http_executor, context):
        """测试 GET 请求"""
        # 创建 GET 节点
        node = self.create_http_node('GET', 'https://httpbin.org/get')

        # Mock the _make_request method
        async def mock_make_request(*args, **kwargs):
            return {
                'status_code': 200,
                'headers': {'content-type': 'application/json'},
                'body': {'message': 'success'},
                'url': 'https://httpbin.org/get',
            }

        http_executor._make_request = mock_make_request

        # 执行节点
        result = await http_executor.execute(node, context)

        # 验证结果
        assert result['status_code'] == 200
        assert result['method'] == 'GET'
        assert result['success'] is True
        assert result['body'] == {'message': 'success'}
        assert result['url'] == 'https://httpbin.org/get'

    async def test_post_request_with_json(self, http_executor, context):
        """测试 POST 请求（JSON 数据）"""
        # 创建 POST 节点
        node = self.create_http_node(
            'POST',
            'https://httpbin.org/post',
            headers={'Content-Type': 'application/json'},
            body={'name': 'test', 'value': 123},
        )

        # Mock the _make_request method
        async def mock_make_request(*args, **kwargs):
            return {
                'status_code': 201,
                'headers': {'content-type': 'application/json'},
                'body': {'id': 1, 'created': True},
                'url': 'https://httpbin.org/post',
            }

        http_executor._make_request = mock_make_request

        # 执行节点
        result = await http_executor.execute(node, context)

        # 验证结果
        assert result['status_code'] == 201
        assert result['method'] == 'POST'
        assert result['success'] is True
        assert result['body'] == {'id': 1, 'created': True}

    async def test_put_request(self, http_executor, context):
        """测试 PUT 请求"""
        # 创建 PUT 节点
        node = self.create_http_node(
            'PUT', 'https://httpbin.org/put', body={'id': 1, 'name': 'updated'}
        )

        # Mock the _make_request method
        async def mock_make_request(*args, **kwargs):
            return {
                'status_code': 200,
                'headers': {'content-type': 'application/json'},
                'body': {'updated': True},
                'url': 'https://httpbin.org/put',
            }

        http_executor._make_request = mock_make_request

        # 执行节点
        result = await http_executor.execute(node, context)

        # 验证结果
        assert result['status_code'] == 200
        assert result['method'] == 'PUT'
        assert result['success'] is True
        assert result['body'] == {'updated': True}

    async def test_delete_request(self, http_executor, context):
        """测试 DELETE 请求"""
        # 创建 DELETE 节点
        node = self.create_http_node('DELETE', 'https://httpbin.org/delete')

        # Mock the _make_request method
        async def mock_make_request(*args, **kwargs):
            return {
                'status_code': 204,
                'headers': {'content-type': 'text/plain'},
                'body': '',
                'url': 'https://httpbin.org/delete',
            }

        http_executor._make_request = mock_make_request

        # 执行节点
        result = await http_executor.execute(node, context)

        # 验证结果
        assert result['status_code'] == 204
        assert result['method'] == 'DELETE'
        assert result['success'] is True

    async def test_patch_request(self, http_executor, context):
        """测试 PATCH 请求"""
        # 创建 PATCH 节点
        node = self.create_http_node(
            'PATCH', 'https://httpbin.org/patch', body={'field': 'new_value'}
        )

        # Mock the _make_request method
        async def mock_make_request(*args, **kwargs):
            return {
                'status_code': 200,
                'headers': {'content-type': 'application/json'},
                'body': {'patched': True},
                'url': 'https://httpbin.org/patch',
            }

        http_executor._make_request = mock_make_request

        # 执行节点
        result = await http_executor.execute(node, context)

        # 验证结果
        assert result['status_code'] == 200
        assert result['method'] == 'PATCH'
        assert result['success'] is True
        assert result['body'] == {'patched': True}

    async def test_request_with_headers_and_params(self, http_executor, context):
        """测试带请求头和查询参数的请求"""
        # 创建带参数的节点
        node = self.create_http_node(
            'GET',
            'https://httpbin.org/get',
            headers={'Authorization': 'Bearer token123', 'User-Agent': 'TestAgent'},
            params={'param1': 'value1', 'param2': 'value2'},
        )

        # Mock the _make_request method to capture arguments
        captured_args = {}

        async def mock_make_request(method, url, headers, params, body, timeout, follow_redirects):
            captured_args.update(
                {
                    'method': method,
                    'url': url,
                    'headers': headers,
                    'params': params,
                    'body': body,
                    'timeout': timeout,
                    'follow_redirects': follow_redirects,
                }
            )
            return {
                'status_code': 200,
                'headers': {'content-type': 'application/json'},
                'body': {'args': {'param1': 'value1'}},
                'url': 'https://httpbin.org/get?param1=value1',
            }

        http_executor._make_request = mock_make_request

        # 执行节点
        result = await http_executor.execute(node, context)

        # 验证结果
        assert result['status_code'] == 200
        assert result['success'] is True

        # 验证请求参数
        assert captured_args['method'] == 'GET'
        assert captured_args['headers']['Authorization'] == 'Bearer token123'
        assert captured_args['params']['param1'] == 'value1'

    async def test_template_rendering(self, http_executor, context):
        """测试模板渲染功能"""
        # 设置输入数据 - 使用 global_variables 而不是 node_inputs
        context.global_variables.update({'user_id': '123', 'api_key': 'secret123'})

        # 创建带模板的节点
        node = self.create_http_node(
            'GET',
            'https://api.example.com/users/{{user_id}}',
            headers={'Authorization': 'Bearer {{api_key}}'},
            params={'include': 'profile'},
        )

        # Mock the _make_request method to capture rendered values
        captured_args = {}

        async def mock_make_request(method, url, headers, params, body, timeout, follow_redirects):
            captured_args.update(
                {
                    'url': url,
                    'headers': headers,
                }
            )
            return {
                'status_code': 200,
                'headers': {'content-type': 'application/json'},
                'body': {'user': {'id': '123'}},
                'url': 'https://api.example.com/users/123',
            }

        http_executor._make_request = mock_make_request

        # 执行节点
        result = await http_executor.execute(node, context)

        # 验证结果
        assert result['status_code'] == 200
        assert result['success'] is True

        # 验证模板渲染
        assert captured_args['url'] == 'https://api.example.com/users/123'
        assert captured_args['headers']['Authorization'] == 'Bearer secret123'

    async def test_error_handling(self, http_executor, context):
        """测试错误处理"""
        # 创建节点
        node = self.create_http_node('GET', 'https://invalid-url.com')

        # Mock the _make_request method to raise an exception
        async def mock_make_request(*args, **kwargs):
            raise httpx.RequestError('Connection failed')

        http_executor._make_request = mock_make_request

        # 执行节点应该抛出异常

        with pytest.raises(NodeExecutionError):
            await http_executor.execute(node, context)

    async def test_non_success_status_code(self, http_executor, context):
        """测试非成功状态码"""
        # 创建节点
        node = self.create_http_node('GET', 'https://httpbin.org/status/404')

        # Mock the _make_request method
        async def mock_make_request(*args, **kwargs):
            return {
                'status_code': 404,
                'headers': {'content-type': 'application/json'},
                'body': {'error': 'Not found'},
                'url': 'https://httpbin.org/status/404',
            }

        http_executor._make_request = mock_make_request

        # 执行节点
        result = await http_executor.execute(node, context)

        # 验证结果
        assert result['status_code'] == 404
        assert result['success'] is False  # 404 不是成功状态码
        assert result['body'] == {'error': 'Not found'}

    def test_get_output_schema(self, http_executor):
        """测试输出模式"""
        schema = http_executor.get_output_schema()

        expected_keys = ['status_code', 'headers', 'body', 'url', 'method', 'success']
        assert all(key in schema for key in expected_keys)

        assert schema['status_code']['type'] == 'integer'
        assert schema['success']['type'] == 'boolean'

    def test_get_required_inputs(self, http_executor):
        """测试必需输入"""
        inputs = http_executor.get_required_inputs()
        assert isinstance(inputs, list)
        # HTTP 节点可以使用任何输入进行模板化，所以不需要特定的必需输入

    def test_validate_config(self, http_executor):
        """测试配置验证"""
        # 有效配置
        valid_config = {
            'title': 'Test Request',
            'method': 'GET',
            'url': 'https://httpbin.org/get',
            'headers': {},
            'params': {},
            'body': None,
            'timeout': 30,
            'follow_redirects': True,
        }
        assert http_executor.validate_config(valid_config) is True

        # 无效配置 - 缺少必需字段
        invalid_config = {
            'method': 'GET',
            'url': 'https://httpbin.org/get',
        }
        assert http_executor.validate_config(invalid_config) is False

        # 无效配置 - 错误的方法
        invalid_method_config = {
            'title': 'Test Request',
            'method': 'INVALID',
            'url': 'https://httpbin.org/get',
            'headers': {},
            'params': {},
            'body': None,
            'timeout': 30,
            'follow_redirects': True,
        }
        assert http_executor.validate_config(invalid_method_config) is False

    async def test_post_comfyui_prompt_with_json(self, http_executor, context):
        """测试 ComfyUI POST 请求（JSON 数据）"""
        # 创建 ComfyUI POST 节点
        node = self.create_http_node(
            'POST',
            'http://14.12.0.172:9898/prompt',
            headers={'Content-Type': 'application/json'},
            body={
                'client_id': '533ef3a3-39c0-4e39-9ced-37d290f371f8',
                'prompt': {
                    '9': {
                        'inputs': {
                            'ckpt_name': 'XL\\sd_xl_base_1.0.safetensors',
                            'config_name': 'Default',
                            'vae_name': 'sdxl_vae.safetensors',
                            'clip_skip': -2,
                            'lora_name': 'None',
                            'lora_model_strength': 1,
                            'lora_clip_strength': 1,
                            'resolution': '1024 x 1024',
                            'empty_latent_width': 512,
                            'empty_latent_height': 512,
                            'positive': '1girl sitting on a bus, (school uniform:1.3), park, head portrait, real photo, realistic, masterpiece, best quality,',
                            'positive_token_normalization': 'length+mean',
                            'positive_weight_interpretation': 'A1111',
                            'negative': ' text, watermark, nsfw',
                            'negative_token_normalization': 'length+mean',
                            'negative_weight_interpretation': 'A1111',
                            'batch_size': 1,
                            'a1111_prompt_style': False,
                        },
                        'class_type': 'easy fullLoader',
                        '_meta': {'title': 'EasyLoader (Full)'},
                    },
                    '10': {
                        'inputs': {
                            'steps': 20,
                            'cfg': 8,
                            'sampler_name': 'dpmpp_2m',
                            'scheduler': 'karras',
                            'denoise': 1,
                            'image_output': 'Preview',
                            'link_id': 0,
                            'save_prefix': 'ComfyUI',
                            'seed': randint(0, 100000000),
                            'pipe': ['9', 0],
                        },
                        'class_type': 'easy fullkSampler',
                        '_meta': {'title': 'EasyKSampler (Full)'},
                    },
                    '11': {
                        'inputs': {'images': ['10', 1]},
                        'class_type': 'PreviewImage',
                        '_meta': {'title': 'Preview Image'},
                    },
                },
            },
        )

        # 执行节点
        result = await http_executor.execute(node, context)

        # 验证结果
        assert result['status_code'] == 200
        assert result['method'] == 'POST'
        assert result['success'] is True
        assert 'prompt_id' in result['body']
        assert result['body'].get('prompt_id') is not None
        assert result['body']['number'] >= 1
        assert result['body']['node_errors'] == {}
        assert result['url'] == 'http://14.12.0.172:9898/prompt'

    async def test_post_comfyui_with_template_rendering(self, http_executor, context):
        """测试 ComfyUI POST 请求与模板渲染功能"""
        # 设置模板变量
        context.global_variables.update(
            {
                'comfyui_host': '127.0.0.1',
                'comfyui_port': '9898',
                'client_id': 'test-client-123',
                'positive_prompt': 'beautiful landscape, masterpiece, best quality',
                'negative_prompt': 'blurry, low quality, nsfw',
                'steps': 25,
                'cfg_scale': 7.5,
                'seed': 123456789,
            }
        )

        # 创建带模板的 ComfyUI 节点
        node = self.create_http_node(
            'POST',
            'http://{{comfyui_host}}:{{comfyui_port}}/prompt',
            headers={'Content-Type': 'application/json'},
            body={
                'client_id': '{{client_id}}',
                'prompt': {
                    '1': {
                        'inputs': {
                            'positive': '{{positive_prompt}}',
                            'negative': '{{negative_prompt}}',
                            'steps': '{{steps}}',
                            'cfg': '{{cfg_scale}}',
                            'seed': '{{seed}}',
                        },
                        'class_type': 'KSampler',
                        '_meta': {'title': 'KSampler'},
                    },
                },
            },
        )

        # Mock 请求以捕获渲染后的值
        captured_args = {}

        async def mock_make_request(method, url, headers, params, body, timeout, follow_redirects):
            captured_args.update(
                {
                    'method': method,
                    'url': url,
                    'headers': headers,
                    'body': body,
                }
            )
            return {
                'status_code': 200,
                'headers': {'content-type': 'application/json'},
                'body': {'prompt_id': 'template-test-prompt-id', 'number': 1, 'node_errors': {}},
                'url': url,
            }

        http_executor._make_request = mock_make_request

        # 执行节点
        result = await http_executor.execute(node, context)

        # 验证结果
        assert result['status_code'] == 200
        assert result['method'] == 'POST'
        assert result['success'] is True

        # 验证模板渲染
        assert captured_args['url'] == 'http://127.0.0.1:9898/prompt'
        assert captured_args['body']['client_id'] == 'test-client-123'
        assert (
            captured_args['body']['prompt']['1']['inputs']['positive']
            == 'beautiful landscape, masterpiece, best quality'
        )
        assert (
            captured_args['body']['prompt']['1']['inputs']['negative']
            == 'blurry, low quality, nsfw'
        )
        assert captured_args['body']['prompt']['1']['inputs']['steps'] == '25'
        assert captured_args['body']['prompt']['1']['inputs']['cfg'] == '7.5'
        assert captured_args['body']['prompt']['1']['inputs']['seed'] == '123456789'

    async def test_template_rendering_with_lists(self, http_executor, context):
        """测试模板渲染功能（包含列表）"""
        # 设置模板变量
        context.global_variables.update(
            {
                'api_endpoint': 'https://api.example.com',
                'user_name': 'test_user',
                'tag1': 'important',
                'tag2': 'urgent',
                'item_id': '12345',
            }
        )

        # 创建带列表模板的节点
        node = self.create_http_node(
            'POST',
            'https://api.example.com/users/{{user_name}}/items',
            headers={'Content-Type': 'application/json'},
            body={
                'user': '{{user_name}}',
                'items': [
                    {
                        'id': '{{item_id}}',
                        'tags': ['{{tag1}}', '{{tag2}}'],
                        'metadata': {
                            'created_by': '{{user_name}}',
                            'endpoint': 'https://api.example.com',
                        },
                    }
                ],
            },
        )

        # Mock 请求以捕获渲染后的值
        captured_args = {}

        async def mock_make_request(method, url, headers, params, body, timeout, follow_redirects):
            captured_args.update(
                {
                    'url': url,
                    'body': body,
                }
            )
            return {
                'status_code': 201,
                'headers': {'content-type': 'application/json'},
                'body': {'success': True, 'id': 'created-item-123'},
                'url': url,
            }

        http_executor._make_request = mock_make_request

        # 执行节点
        result = await http_executor.execute(node, context)

        # 验证结果
        assert result['status_code'] == 201
        assert result['success'] is True

        # 验证模板渲染
        assert captured_args['url'] == 'https://api.example.com/users/test_user/items'
        assert captured_args['body']['user'] == 'test_user'
        assert captured_args['body']['items'][0]['id'] == '12345'
        assert captured_args['body']['items'][0]['tags'] == ['important', 'urgent']
        assert captured_args['body']['items'][0]['metadata']['created_by'] == 'test_user'
        assert (
            captured_args['body']['items'][0]['metadata']['endpoint'] == 'https://api.example.com'
        )
        assert captured_args['body']['items'][0]['tags'] == ['important', 'urgent']
        assert captured_args['body']['items'][0]['metadata']['created_by'] == 'test_user'
        assert (
            captured_args['body']['items'][0]['metadata']['endpoint'] == 'https://api.example.com'
        )
