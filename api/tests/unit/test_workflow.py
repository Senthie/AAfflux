"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-30 10:23:25
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-02 15:12:01
FilePath: /api/tests/unit/test_workflow.py
Description:模拟真实的AI传入传出的流程


Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

import logging
from random import randint
from uuid import uuid4

from hypothesis import given, settings, strategies as st
import pytest

# 配置 logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('test_workflow.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
from app.engine.execution_context import ExecutionContext

# 导入 registry 并注册所有节点
from app.engine.nodes import register_all_nodes
from app.engine.nodes.base.emum import NodeTypeEnum
from app.engine.topological_sorter import TopologicalSorter

# 注册所有节点执行器
register_all_nodes()

# 导入模型
from app.models.workflow.workflow import Connection, ExecutionRecord, Node, Workflow

# ============ Ollama 配置 ============
OLLAMA_API_KEY = 'ollama'
OLLAMA_BASE_URL = 'http://14.12.0.172:19516'
OLLAMA_MODEL_ID = 'qwen3:8b'


@pytest.fixture
def workflow():
    """创建测试工作流"""
    return Workflow(
        id=uuid4(),
        name='Test Workflow',
        workspace_id=uuid4(),
        created_by=uuid4(),
    )


@pytest.fixture
def execution_record(workflow):
    """创建执行记录"""
    return ExecutionRecord(
        id=uuid4(),
        workflow_id=workflow.id,
        inputs={},
        status='PENDING',
    )


@pytest.fixture
def context(workflow, execution_record):
    """创建执行上下文"""
    return ExecutionContext(workflow, execution_record, {})


class TestWorkflow:
    def create_http_node(self, method: str, url: str, **kwargs) -> Node:
        """创建 HTTP 节点的辅助方法"""
        config = {
            'title': 'Http Request',
            'method': method,
            'url': url,
            'headers': kwargs.get('headers', {}),
            'params': kwargs.get('params', {}),
            'body_is_expr': True,
            'body': kwargs.get('body'),
            'timeout': kwargs.get('timeout', 30),
            'follow_redirects': kwargs.get('follow_redirects', True),
        }
        return Node(
            workflow_id=uuid4(),
            type=NodeTypeEnum.HTTP.value,
            name='Http Request',
            config=config,
            position={'x': 0, 'y': 0},
        )

    @pytest.mark.timeout(500)
    @settings(max_examples=100, deadline=None)
    @given(
        left=st.integers(min_value=0, max_value=100),
        right=st.integers(min_value=0, max_value=100),
    )
    @pytest.mark.asyncio
    async def test_base_chat_Agent_by_entities(self, left, right):
        """
        测试节点是否能如期运行
        """
        # 创建工作流
        workflow = Workflow(
            id=uuid4(),
            name='Test Workflow',
            workspace_id=uuid4(),
            created_by=uuid4(),
        )
        # 创建执行记录
        execution_record = ExecutionRecord(
            id=uuid4(),
            workflow_id=workflow.id,
            inputs={},
            status='PENDING',
        )
        # 创建执行上下文
        context = ExecutionContext(workflow, execution_record, {})

        # 创建 ChatNode 实例
        chat_node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type=NodeTypeEnum.CHAT.value,
            name='Test Chat Node',
            config={'prompt': f'{left} + {right} = ?', 'title': 'Test Chat Node'},
        )
        # 创建 Ollama provider 示例
        ollama_node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type=NodeTypeEnum.OLLAMA.value,
            name='Real Ollama Provider',
            config={
                'title': 'Real Ollama Provider',
                'base_url': OLLAMA_BASE_URL,
                'api_key': OLLAMA_API_KEY,
                'model': OLLAMA_MODEL_ID,
                'timeout': 120,
            },
        )
        agent_node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type=NodeTypeEnum.AGENT.value,
            name='Math Agent',
            config={
                'title': 'Math Agent',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'math_chat',
                'agent_strategy_label': 'Noe',
                'prompt_is_expr': True,
                'prompt': '你是一个数学助手，请简洁回答问题。\n{{ $.outputs.Test Chat Node.outputs.prompt }}',
                'temperature': 0.1,
            },
        )
        conn1 = Connection(
            id=uuid4(),
            workflow_id=workflow.id,
            source_node_id=ollama_node.id,
            target_node_id=agent_node.id,
            source_output='output',
            target_input='input',
        )

        conn2 = Connection(
            id=uuid4(),
            workflow_id=workflow.id,
            source_node_id=chat_node.id,
            target_node_id=agent_node.id,
            source_output='output',
            target_input='input',
        )

        context.set_connections([conn1, conn2])
        # 对节点进行排序
        sorter = TopologicalSorter([chat_node, ollama_node, agent_node], [conn1, conn2])
        sorted_nodes = sorter.sort()

        # 执行工作流 使用 node_executor_registry
        from app.engine.node_executor import node_executor_registry

        for node in sorted_nodes:
            executor = node_executor_registry.get_executor(node.type)
            result = await executor.execute(node, context)
            context.set_node_output(node, result)
            logger.info(f'节点 [{node.name}] 执行完成，输出: {result}')

        # 验证 agent 节点有输出 (使用 jsonpath 语法，节点名中空格会被替换为下划线)
        agent_output = context.get_node_output('$.outputs.Math_Agent')
        assert agent_output is not None
        assert 'content' in agent_output.get('outputs', {})
        # assert f'{left + right}' in agent_output.get('outputs', {}).get('content', '')

    @pytest.mark.timeout(500)
    @pytest.mark.asyncio
    async def test_base_comfyui(self):
        """
        测试节点是否能如期运行
        """
        # 创建工作流
        workflow = Workflow(
            id=uuid4(),
            name='Test Workflow',
            workspace_id=uuid4(),
            created_by=uuid4(),
        )
        # 创建执行记录
        execution_record = ExecutionRecord(
            id=uuid4(),
            workflow_id=workflow.id,
            inputs={},
            status='PENDING',
        )
        # 创建执行上下文
        context = ExecutionContext(workflow, execution_record, {})

        # 创建 ChatNode 实例
        chat_node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type=NodeTypeEnum.CHAT.value,
            name='Test Chat Node',
            config={'prompt': '公交站里的女孩', 'title': 'Test Chat Node'},
        )
        # 创建 Ollama provider 示例
        ollama_node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type=NodeTypeEnum.OLLAMA.value,
            name='Real Ollama Provider',
            config={
                'title': 'Real Ollama Provider',
                'base_url': OLLAMA_BASE_URL,
                'api_key': OLLAMA_API_KEY,
                'model': OLLAMA_MODEL_ID,
                'timeout': 120,
            },
        )
        agent_node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type=NodeTypeEnum.AGENT.value,
            name='Math Agent',
            config={
                'title': 'Math Agent',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'math_chat',
                'agent_strategy_label': 'Noe',
                'prompt_is_expr': True,
                'prompt': '你是一个 Stable Diffusion 绘画专家，我会提供给你画面描述，你将输出ai绘画提示词，只需要提供正向英文提示词，不需要输出Enhanced Notes和Positive Prompt。\n{{ $.outputs.Test Chat Node.outputs.prompt }}',
                'temperature': 0.1,
            },
        )
        # 创建 ComfyUI POST 节点
        comfyui_node = self.create_http_node(
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
                            'positive': '{{ $.outputs.Math Agent.outputs.content }}',
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
        conn1 = Connection(
            id=uuid4(),
            workflow_id=workflow.id,
            source_node_id=ollama_node.id,
            target_node_id=agent_node.id,
            source_output='output',
            target_input='input',
        )

        conn2 = Connection(
            id=uuid4(),
            workflow_id=workflow.id,
            source_node_id=chat_node.id,
            target_node_id=agent_node.id,
            source_output='output',
            target_input='input',
        )

        conn3 = Connection(
            id=uuid4(),
            workflow_id=workflow.id,
            source_node_id=agent_node.id,
            target_node_id=comfyui_node.id,
            source_output='output',
            target_input='input',
        )

        context.set_connections([conn1, conn2])
        # 对节点进行排序
        sorter = TopologicalSorter(
            [chat_node, ollama_node, agent_node, comfyui_node], [conn1, conn2, conn3]
        )
        sorted_nodes = sorter.sort()

        # 执行工作流 使用 node_executor_registry
        from app.engine.node_executor import node_executor_registry

        for node in sorted_nodes:
            executor = node_executor_registry.get_executor(node.type)
            result = await executor.execute(node, context)
            context.set_node_output(node, result)
            logger.info(f'节点 [{node.name}] 执行完成，输出: {result}')

        # 验证 agent 节点有输出 (使用 jsonpath 语法，节点名中空格会被替换为下划线)
        agent_output = context.get_node_output('$.outputs.Math_Agent')
        assert agent_output is not None
        assert 'content' in agent_output.get('outputs', {})
        http_output = context.get_node_output('$.outputs.Http Request')
        assert http_output is not None
        assert http_output['outputs']['body']['prompt_id']
