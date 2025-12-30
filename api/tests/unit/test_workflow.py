"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-30 10:23:25
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-30 15:28:47
FilePath: /api/tests/unit/test_workflow.py
Description:模拟真实的AI传入传出的流程


Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

import logging
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
OLLAMA_BASE_URL = 'http://14.12.0.172:11434'
OLLAMA_MODEL_ID = 'deepseek-r1:14b'


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
        assert f'{left + right}' in agent_output.get('outputs', {}).get('content', '')
