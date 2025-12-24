"""
节点执行器单元测试

合并自:
- test_agent_node.py
- test_ollama_node.py
- test_node_executors.py

测试内容:
- AgentNode 和 OllamaNode
- ConditionNode 条件节点
- CodeNode 代码节点
- TransformNode 转换节点
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.engine.execution_context import ExecutionContext
from app.engine.nodes.agent.agent import AgentNode
from app.engine.nodes.code_node import CodeNodeExecutor
from app.engine.nodes.condition_node import ConditionNodeExecutor
from app.engine.nodes.ollama_node import OllamaNodeExecutor
from app.engine.nodes.provider.ollama_node import (
    MessageCache,
    OllamaNode,
)
from app.engine.nodes.transform_node import TransformNodeExecutor
from app.engine.topological_sorter import TopologicalSorter
from app.models.workflow.workflow import Connection, ExecutionRecord, Node, Workflow

# ============ Ollama 配置 ============
OLLAMA_API_KEY = 'ollama'
OLLAMA_BASE_URL = 'http://14.12.0.172:11434'
OLLAMA_MODEL_ID = 'deepseek-r1:14b'


# ============ Fixtures ============
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
    return ExecutionContext(workflow, execution_record, {'input': 'test input'})


@pytest.fixture
def ollama_executor():
    """Create an Ollama node executor instance."""
    return OllamaNodeExecutor()


@pytest.fixture
def mock_node():
    """Create a mock node."""
    node = MagicMock()
    node.id = uuid4()
    node.config = {}
    return node


@pytest.fixture
def mock_context():
    """Create a mock execution context."""
    context = MagicMock()
    context.get_node_input = MagicMock(return_value={})
    return context


# ============ MessageCache Tests ============
class TestMessageCache:
    """消息缓存测试"""

    def test_add_message(self):
        """测试添加消息"""
        cache = MessageCache(max_messages=10)
        cache.add_user_message('Hello')
        cache.add_assistant_message('Hi there')

        messages = cache.get_messages()
        assert len(messages) == 2
        assert messages[0].role == 'user'
        assert messages[1].role == 'assistant'

    def test_add_system_message(self):
        """测试添加系统消息"""
        cache = MessageCache()
        cache.add_system_message('You are a helpful assistant')
        messages = cache.get_messages()
        assert len(messages) == 1
        assert messages[0].role == 'system'

    def test_max_messages_limit(self):
        """测试消息数量限制"""
        cache = MessageCache(max_messages=5)
        for i in range(10):
            cache.add_user_message(f'Message {i}')
        messages = cache.get_messages()
        assert len(messages) <= 5

    def test_clear_messages(self):
        """测试清空消息"""
        cache = MessageCache()
        cache.add_user_message('Hello')
        cache.clear()
        assert len(cache.get_messages()) == 0


# ============ OllamaNode Tests ============
class TestOllamaNode:
    """Ollama节点测试"""

    def test_init_node_data(self):
        """测试节点数据初始化"""
        node = OllamaNode()
        data = {
            'title': 'Test Ollama',
            'base_url': 'http://localhost:11434',
            'model': 'llama2',
            'timeout': 60,
        }
        node.init_node_data(data)
        assert node._node_data.title == 'Test Ollama'
        assert node._node_data.model == 'llama2'

    def test_validate_config(self):
        """测试配置验证"""
        node = OllamaNode()
        assert node.validate_config({'model': 'llama2'}) is True
        assert node.validate_config({}) is False

    @pytest.mark.asyncio
    async def test_execute_stores_provider_in_context(self, workflow, execution_record, context):
        """测试执行后将provider存储到context"""
        ollama_node = OllamaNode()
        node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='OLLAMA',
            name='Ollama Provider',
            config={
                'title': 'Ollama',
                'base_url': 'http://localhost:11434',
                'model': 'llama2',
            },
        )
        result = await ollama_node.execute(node, context)
        assert result['status'] == 'initialized'
        assert result['model'] == 'llama2'


# ============ OllamaNodeExecutor Tests ============
class TestOllamaNodeExecutor:
    """Ollama节点执行器测试"""

    def test_validate_config_valid(self, ollama_executor):
        """Test validation with valid config."""
        config = {
            'model': 'llama2',
            'base_url': 'http://localhost:11434',
            'temperature': 0.7,
        }
        assert ollama_executor.validate_config(config) is True

    def test_validate_config_missing_model(self, ollama_executor):
        """Test validation fails without model."""
        config = {'base_url': 'http://localhost:11434'}
        assert ollama_executor.validate_config(config) is False

    def test_render_prompt_simple(self, ollama_executor):
        """Test simple prompt rendering."""
        template = 'Hello, {{name}}!'
        inputs = {'name': 'World'}
        result = ollama_executor._render_prompt(template, inputs)
        assert result == 'Hello, World!'


# ============ AgentNode Tests ============
class TestAgentNode:
    """Agent节点测试"""

    def test_init_node_data(self):
        """测试节点数据初始化"""
        agent = AgentNode()
        data = {
            'title': 'Test Agent',
            'agent_strategy_provider_name': 'ollama',
            'agent_strategy_name': 'chat',
        }
        agent.init_node_data(data)
        assert agent._node_data.title == 'Test Agent'

    def test_validate_config(self):
        """测试配置验证"""
        agent = AgentNode()
        assert agent.validate_config({'agent_strategy_name': 'chat'}) is True
        assert agent.validate_config({}) is False

    @pytest.mark.asyncio
    async def test_execute_without_provider(self, workflow, execution_record, context):
        """测试没有provider时执行失败"""
        agent = AgentNode()
        node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='LLM',
            name='Test Agent',
            config={
                'title': 'Agent',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'chat',
            },
        )
        result = await agent.execute(node, context)
        assert 'error' in result


# ============ ConditionNode Tests ============
class TestConditionNodeExecutor:
    """条件节点执行器测试"""

    @pytest.mark.asyncio
    async def test_basic_condition_evaluation(self):
        """Test basic condition evaluation functionality."""
        executor = ConditionNodeExecutor()
        workflow = Workflow(
            id=uuid4(),
            name='Test Workflow',
            workspace_id=uuid4(),
            created_by=uuid4(),
        )
        execution_record = ExecutionRecord(
            id=uuid4(), workflow_id=workflow.id, inputs={}, status='PENDING'
        )
        context = ExecutionContext(workflow, execution_record, {'x': 5, 'y': 3})

        node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='CONDITION',
            name='Test Condition',
            config={
                'condition': 'x > y',
                'true_branch': 'success_path',
                'false_branch': 'failure_path',
            },
        )
        result = await executor.execute(node, context)
        assert result['result'] is True
        assert result['branch'] == 'success_path'

    def test_condition_node_config_validation(self):
        """Test condition node configuration validation."""
        executor = ConditionNodeExecutor()
        valid_config = {'condition': 'x > 0', 'true_branch': 'success', 'false_branch': 'failure'}
        assert executor.validate_config(valid_config) is True

        invalid_config = {'true_branch': 'success', 'false_branch': 'failure'}
        assert executor.validate_config(invalid_config) is False


# ============ CodeNode Tests ============
class TestCodeNodeExecutor:
    """代码节点执行器测试"""

    @pytest.mark.asyncio
    async def test_basic_code_execution(self):
        """Test basic code execution functionality."""
        executor = CodeNodeExecutor()
        workflow = Workflow(
            id=uuid4(),
            name='Test Workflow',
            workspace_id=uuid4(),
            created_by=uuid4(),
        )
        execution_record = ExecutionRecord(
            id=uuid4(), workflow_id=workflow.id, inputs={}, status='PENDING'
        )
        context = ExecutionContext(workflow, execution_record, {'x': 10, 'y': 5})

        node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='CODE',
            name='Test Code',
            config={'code': 'result = x + y'},
        )
        result = await executor.execute(node, context)
        assert result['result'] == 15

    def test_code_node_config_validation(self):
        """Test code node configuration validation."""
        executor = CodeNodeExecutor()
        valid_config = {'code': 'result = x + 1', 'timeout': 30}
        assert executor.validate_config(valid_config) is True

        invalid_config = {'timeout': 30}
        assert executor.validate_config(invalid_config) is False


# ============ TransformNode Tests ============
class TestTransformNodeExecutor:
    """转换节点执行器测试"""

    @pytest.mark.asyncio
    async def test_basic_json_path_extraction(self):
        """Test basic JSON path extraction functionality."""
        executor = TransformNodeExecutor()
        workflow = Workflow(
            id=uuid4(),
            name='Test Workflow',
            workspace_id=uuid4(),
            created_by=uuid4(),
        )
        execution_record = ExecutionRecord(
            id=uuid4(), workflow_id=workflow.id, inputs={}, status='PENDING'
        )
        test_data = {
            'user': {'name': 'John', 'age': 30},
            'items': [{'id': 1}, {'id': 2}],
        }
        context = ExecutionContext(workflow, execution_record, test_data)

        node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='TRANSFORM',
            name='Test Transform',
            config={'operation': 'extract', 'transformations': [{'path': '$.user.name'}]},
        )
        result = await executor.execute(node, context)
        assert result['result'] == 'John'


# ============ Integration Tests ============
@pytest.mark.integration
@pytest.mark.asyncio
class TestRealOllamaIntegration:
    """真实Ollama服务集成测试 - 运行: pytest -m integration"""

    async def test_real_ollama_simple_chat(self, workflow, execution_record):
        """测试真实Ollama简单对话"""
        context = ExecutionContext(workflow, execution_record, {'question': '1+1等于几？'})

        ollama_node = OllamaNode()
        ollama_config_node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='OLLAMA',
            name='Real Ollama Provider',
            config={
                'title': 'Ollama',
                'base_url': OLLAMA_BASE_URL,
                'api_key': OLLAMA_API_KEY,
                'model': OLLAMA_MODEL_ID,
                'timeout': 120,
            },
        )

        agent = AgentNode()
        agent_node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='LLM',
            name='Math Agent',
            config={
                'title': 'Math Agent',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'math_chat',
                'system_prompt': '你是一个数学助手，请简洁回答问题。',
                'user_prompt': '{question}',
                'temperature': 0.1,
            },
        )

        conn = Connection(
            id=uuid4(),
            workflow_id=workflow.id,
            source_node_id=ollama_config_node.id,
            target_node_id=agent_node.id,
            source_output='output',
            target_input='input',
        )
        sorter = TopologicalSorter([ollama_config_node, agent_node], [conn])
        sorted_nodes = sorter.sort()

        ollama_result = await ollama_node.execute(ollama_config_node, context)
        assert ollama_result['status'] == 'initialized'

        agent_node.config['provider_key'] = ollama_result['provider_key']
        result = await agent.execute(agent_node, context)

        assert 'error' not in result
        assert '2' in result['content']
