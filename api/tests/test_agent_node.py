"""
Tests for AgentNode and OllamaNode.

测试Agent节点和Ollama Provider节点的功能。
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.engine.execution_context import ExecutionContext
from app.engine.nodes.agent.agent import AgentNode
from app.engine.nodes.provider.ollama_node import (
    MessageCache,
    OllamaNode,
    OllamaNodeData,
)
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
        assert messages[0].content == 'Hello'
        assert messages[1].role == 'assistant'
        assert messages[1].content == 'Hi there'

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

        # 添加超过限制的消息
        for i in range(10):
            cache.add_user_message(f'Message {i}')

        messages = cache.get_messages()
        assert len(messages) <= 5

    def test_system_message_preserved(self):
        """测试系统消息在裁剪时被保留"""
        cache = MessageCache(max_messages=3)
        cache.add_system_message('System prompt')

        for i in range(5):
            cache.add_user_message(f'User {i}')

        messages = cache.get_messages()
        # 系统消息应该被保留
        system_msgs = [m for m in messages if m.role == 'system']
        assert len(system_msgs) == 1
        assert system_msgs[0].content == 'System prompt'

    def test_clear_messages(self):
        """测试清空消息"""
        cache = MessageCache()
        cache.add_user_message('Hello')
        cache.clear()

        assert len(cache.get_messages()) == 0

    def test_get_last_message(self):
        """测试获取最后一条消息"""
        cache = MessageCache()
        assert cache.get_last_message() is None

        cache.add_user_message('First')
        cache.add_assistant_message('Second')

        last = cache.get_last_message()
        assert last.content == 'Second'


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
        assert node._node_data.base_url == 'http://localhost:11434'
        assert node._node_data.model == 'llama2'
        assert node._node_data.timeout == 60

    def test_validate_config(self):
        """测试配置验证"""
        node = OllamaNode()

        # 有效配置
        assert node.validate_config({'model': 'llama2'}) is True
        assert node.validate_config({'base_url': 'http://localhost:11434'}) is True

        # 无效配置
        assert node.validate_config({}) is False

    def test_version(self):
        """测试版本号"""
        assert OllamaNode.version() == '1'

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

        # 验证返回结果
        assert result['status'] == 'initialized'
        assert result['model'] == 'llama2'
        assert 'provider_key' in result

        # 验证provider已存储到context
        provider = context.get_global_variable('default_ollama_provider')
        assert provider is ollama_node

        # 验证通过key也能获取
        provider_by_key = context.get_global_variable(result['provider_key'])
        assert provider_by_key is ollama_node

    def test_get_provider_from_context(self, context):
        """测试从context获取provider"""
        ollama_node = OllamaNode()
        context.update_global_variable('default_ollama_provider', ollama_node)

        # 获取默认provider
        provider = OllamaNode.get_provider_from_context(context)
        assert provider is ollama_node

        # 获取指定key的provider
        context.update_global_variable('custom_provider', ollama_node)
        provider = OllamaNode.get_provider_from_context(context, 'custom_provider')
        assert provider is ollama_node

        # 获取不存在的provider
        provider = OllamaNode.get_provider_from_context(context, 'non_existent')
        assert provider is None

    def test_get_message_cache_from_context(self, context):
        """测试从context获取消息缓存"""
        # 首次获取，应创建新缓存
        cache = OllamaNode.get_message_cache_from_context(context, 'test_agent')
        assert isinstance(cache, MessageCache)

        # 添加消息
        cache.add_user_message('Hello')

        # 再次获取，应返回同一个缓存
        cache2 = OllamaNode.get_message_cache_from_context(context, 'test_agent')
        assert cache2 is cache
        assert len(cache2.get_messages()) == 1

    def test_extract_content_chat_response(self):
        """测试从chat响应提取内容"""
        node = OllamaNode()

        response = {'message': {'content': 'Hello, how can I help?'}}
        content = node.extract_content(response)
        assert content == 'Hello, how can I help?'

    def test_extract_content_generate_response(self):
        """测试从generate响应提取内容"""
        node = OllamaNode()

        response = {'response': 'Generated text'}
        content = node.extract_content(response)
        assert content == 'Generated text'

    def test_extract_structured_output_json(self):
        """测试提取JSON结构化输出"""
        content = """Here is the result:
                ```json
                {"name": "test", "value": 123}
                ```
                """
        result = OllamaNode.extract_structured_output(content)
        assert result == {'name': 'test', 'value': 123}

    def test_extract_structured_output_raw_json(self):
        """测试提取原始JSON"""
        content = '{"key": "value"}'
        result = OllamaNode.extract_structured_output(content)
        assert result == {'key': 'value'}

    def test_extract_structured_output_with_pattern(self):
        """测试使用自定义模式提取"""
        content = 'The answer is: 42'
        result = OllamaNode.extract_structured_output(content, r'answer is: (\d+)')
        assert result == {'extracted': '42'}

    def test_extract_structured_output_fallback(self):
        """测试无法提取时返回原始内容"""
        content = 'Just plain text'
        result = OllamaNode.extract_structured_output(content)
        assert result == {'raw_content': 'Just plain text'}


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
            'agent_strategy_label': 'Chat Agent',
        }
        agent.init_node_data(data)

        assert agent._node_data.title == 'Test Agent'
        assert agent._node_data.agent_strategy_name == 'chat'

    def test_validate_config(self):
        """测试配置验证"""
        agent = AgentNode()

        # 有效配置
        assert agent.validate_config({'agent_strategy_name': 'chat'}) is True

        # 无效配置
        assert agent.validate_config({}) is False

    def test_version(self):
        """测试版本号"""
        assert AgentNode.version() == '1'

    def test_get_structured_output_schema_dict(self):
        """测试获取结构化输出schema（字典）"""
        agent = AgentNode()
        config = {'output_schema': {'answer': 'string', 'confidence': 'number'}}

        schema = agent._get_structured_output_schema(config)
        assert '"answer"' in schema
        assert '"confidence"' in schema

    def test_get_structured_output_schema_string(self):
        """测试获取结构化输出schema（字符串）"""
        agent = AgentNode()
        config = {'output_schema': '{"answer": "string"}'}

        schema = agent._get_structured_output_schema(config)
        assert schema == '{"answer": "string"}'

    def test_get_structured_output_schema_none(self):
        """测试无输出schema"""
        agent = AgentNode()
        config = {}

        schema = agent._get_structured_output_schema(config)
        assert schema is None

    def test_build_prompt_with_schema(self):
        """测试构建带schema的提示词"""
        agent = AgentNode()

        prompt = 'What is 2+2?'
        schema = '{"answer": "number"}'

        result = agent._build_prompt_with_schema(prompt, schema)

        assert 'What is 2+2?' in result
        assert '{"answer": "number"}' in result
        assert 'JSON格式' in result

    def test_build_prompt_without_schema(self):
        """测试构建不带schema的提示词"""
        agent = AgentNode()

        prompt = 'What is 2+2?'
        result = agent._build_prompt_with_schema(prompt, None)

        assert result == prompt

    def test_extract_output(self):
        """测试提取输出"""
        agent = AgentNode()

        content = '```json\n{"result": 4}\n```'
        result = agent._extract_output(content)

        assert result['result'] == 4
        assert 'raw_content' in result

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
                'agent_strategy_label': 'Chat',
            },
        )

        result = await agent.execute(node, context)

        assert 'error' in result
        assert '未找到Ollama Provider' in result['error']

    @pytest.mark.asyncio
    async def test_execute_with_mocked_provider(self, workflow, execution_record, context):
        """测试使用mock provider执行"""
        agent = AgentNode()

        # 创建mock provider
        mock_provider = MagicMock(spec=OllamaNode)
        mock_provider._node_data = OllamaNodeData(
            title='Mock Ollama',
            model='llama2',
        )
        mock_provider.chat = AsyncMock(
            return_value={
                'message': {'content': '{"answer": 4}'},
                'usage': {'total_tokens': 100},
            }
        )
        mock_provider.extract_content = MagicMock(return_value='{"answer": 4}')

        # 将mock provider存入context
        context.update_global_variable('default_ollama_provider', mock_provider)

        node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='LLM',
            name='Test Agent',
            config={
                'title': 'Agent',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'chat',
                'agent_strategy_label': 'Chat',
                'system_prompt': 'You are a calculator',
                'user_prompt': 'Calculate: {input}',
                'temperature': 0.5,
            },
        )

        result = await agent.execute(node, context)

        # 验证结果
        assert 'error' not in result
        assert result['content'] == '{"answer": 4}'
        assert result['model'] == 'llama2'

        # 验证provider.chat被调用
        mock_provider.chat.assert_called_once()
        call_args = mock_provider.chat.call_args
        assert call_args.kwargs['temperature'] == 0.5

    @pytest.mark.asyncio
    async def test_execute_with_variable_substitution(self, workflow, execution_record):
        """测试变量替换"""
        context = ExecutionContext(
            workflow,
            execution_record,
            {'name': 'Alice', 'question': 'What is AI?'},
        )

        agent = AgentNode()

        mock_provider = MagicMock(spec=OllamaNode)
        mock_provider._node_data = OllamaNodeData(title='Mock', model='llama2')
        mock_provider.chat = AsyncMock(return_value={'message': {'content': 'AI is...'}})
        mock_provider.extract_content = MagicMock(return_value='AI is...')

        context.update_global_variable('default_ollama_provider', mock_provider)

        node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='LLM',
            name='Test Agent',
            config={
                'title': 'Agent',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'chat',
                'agent_strategy_label': 'Chat',
                'user_prompt': 'Hello {name}, your question: {question}',
            },
        )

        await agent.execute(node, context)

        # 验证消息中包含替换后的变量
        call_args = mock_provider.chat.call_args
        messages = call_args.kwargs['messages']
        user_message = [m for m in messages if m.role == 'user'][0]
        assert 'Alice' in user_message.content
        assert 'What is AI?' in user_message.content

    @pytest.mark.asyncio
    async def test_execute_preserves_message_history(self, workflow, execution_record, context):
        """测试消息历史保留"""
        agent = AgentNode()

        mock_provider = MagicMock(spec=OllamaNode)
        mock_provider._node_data = OllamaNodeData(title='Mock', model='llama2')
        mock_provider.chat = AsyncMock(return_value={'message': {'content': 'Response'}})
        mock_provider.extract_content = MagicMock(return_value='Response')

        context.update_global_variable('default_ollama_provider', mock_provider)

        node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='LLM',
            name='Test Agent',
            config={
                'title': 'Agent',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'test_strategy',
                'agent_strategy_label': 'Chat',
                'user_prompt': 'Hello',
            },
        )

        # 第一次执行
        await agent.execute(node, context)

        # 获取消息缓存
        cache = OllamaNode.get_message_cache_from_context(context, 'test_strategy')
        messages = cache.get_messages()

        # 应该有用户消息和助手回复
        assert len(messages) == 2
        assert messages[0].role == 'user'
        assert messages[1].role == 'assistant'
        assert messages[1].content == 'Response'

    @pytest.mark.asyncio
    async def test_execute_handles_exception(self, workflow, execution_record, context):
        """测试异常处理"""
        agent = AgentNode()

        mock_provider = MagicMock(spec=OllamaNode)
        mock_provider._node_data = OllamaNodeData(title='Mock', model='llama2')
        mock_provider.chat = AsyncMock(side_effect=Exception('Connection failed'))

        context.update_global_variable('default_ollama_provider', mock_provider)

        node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='LLM',
            name='Test Agent',
            config={
                'title': 'Agent',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'chat',
                'agent_strategy_label': 'Chat',
            },
        )

        result = await agent.execute(node, context)

        assert 'error' in result
        assert 'Connection failed' in result['error']
        assert result['content'] == ''


# ============ Integration Tests ============


class TestOllamaAgentIntegration:
    """Ollama和Agent节点集成测试"""

    @pytest.mark.asyncio
    async def test_workflow_ollama_then_agent(self, workflow, execution_record):
        """测试工作流：OllamaNode -> AgentNode"""
        context = ExecutionContext(workflow, execution_record, {'query': 'What is Python?'})

        # 1. 执行OllamaNode
        ollama_node = OllamaNode()
        ollama_config_node = Node(
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

        ollama_result = await ollama_node.execute(ollama_config_node, context)
        assert ollama_result['status'] == 'initialized'

        # 2. Mock HTTP调用
        with patch.object(ollama_node, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Python is a programming language.'},
                'usage': {'total_tokens': 50},
            }

            # 3. 执行AgentNode
            agent = AgentNode()
            agent_node = Node(
                id=uuid4(),
                workflow_id=workflow.id,
                type='LLM',
                name='Chat Agent',
                config={
                    'title': 'Agent',
                    'agent_strategy_provider_name': 'ollama',
                    'agent_strategy_name': 'qa',
                    'agent_strategy_label': 'QA Agent',
                    'system_prompt': 'You are a helpful assistant.',
                    'user_prompt': 'Answer: {query}',
                },
            )

            result = await agent.execute(agent_node, context)

            # 验证结果
            assert result['content'] == 'Python is a programming language.'
            assert result['model'] == 'llama2'

    @pytest.mark.asyncio
    async def test_multiple_agents_share_provider(self, workflow, execution_record):
        """测试多个Agent共享同一个Provider"""
        context = ExecutionContext(workflow, execution_record, {})

        # 设置OllamaNode
        ollama_node = OllamaNode()
        ollama_config_node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='OLLAMA',
            name='Shared Provider',
            config={'title': 'Ollama', 'model': 'llama2'},
        )

        await ollama_node.execute(ollama_config_node, context)

        # Mock chat方法
        with patch.object(ollama_node, 'chat') as mock_chat:
            mock_chat.return_value = {'message': {'content': 'Response'}}

            # 创建两个Agent
            agent1 = AgentNode()
            agent2 = AgentNode()

            node1 = Node(
                id=uuid4(),
                workflow_id=workflow.id,
                type='LLM',
                name='Agent 1',
                config={
                    'title': 'Agent1',
                    'agent_strategy_provider_name': 'ollama',
                    'agent_strategy_name': 'agent1',
                    'agent_strategy_label': 'Agent 1',
                    'user_prompt': 'Query 1',
                },
            )

            node2 = Node(
                id=uuid4(),
                workflow_id=workflow.id,
                type='LLM',
                name='Agent 2',
                config={
                    'title': 'Agent2',
                    'agent_strategy_provider_name': 'ollama',
                    'agent_strategy_name': 'agent2',
                    'agent_strategy_label': 'Agent 2',
                    'user_prompt': 'Query 2',
                },
            )

            # 两个Agent都应该能成功执行
            result1 = await agent1.execute(node1, context)
            result2 = await agent2.execute(node2, context)

            assert 'error' not in result1
            assert 'error' not in result2

            # 验证chat被调用了两次
            assert mock_chat.call_count == 2


# ============ Real Ollama Integration Tests ============


@pytest.mark.integration
@pytest.mark.asyncio
class TestRealOllamaAgentIntegration:
    """
    使用真实 Ollama 服务的集成测试。
    运行: pytest -m integration tests/test_agent_node.py -v
    """

    async def test_real_ollama_simple_chat(self, workflow, execution_record):
        """测试真实 Ollama 简单对话"""
        context = ExecutionContext(workflow, execution_record, {'question': '1+1等于几？'})

        # 1. 初始化 OllamaNode
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
        # 2. 执行 AgentNode
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
                'agent_strategy_label': 'Math Chat',
                'system_prompt': '你是一个数学助手，请简洁回答问题。',
                'user_prompt': '{question}',
                'temperature': 0.1,
                'max_tokens': 500,
            },
        )
        conn1 = Connection(
            id=uuid4(),
            workflow_id=workflow.id,
            source_node_id=ollama_config_node.id,
            target_node_id=agent_node.id,
            source_output='output',
            target_input='input',
        )
        sorter = TopologicalSorter([ollama_config_node, agent_node], [conn1])
        sorted_nodes = sorter.sort()

        # 验证拓扑排序结果
        assert len(sorted_nodes) == 2
        assert sorted_nodes[0].id == ollama_config_node.id  # OllamaNode 应该先执行
        assert sorted_nodes[1].id == agent_node.id  # AgentNode 依赖 OllamaNode

        # 3. 按拓扑顺序执行节点
        # 先执行 OllamaNode，初始化 provider 并存储到 context
        ollama_result = await ollama_node.execute(ollama_config_node, context)
        assert ollama_result['status'] == 'initialized'
        assert ollama_result['model'] == OLLAMA_MODEL_ID

        # 设置 AgentNode 的 provider_key，使其能找到 OllamaNode 实例
        agent_node.config['provider_key'] = ollama_result['provider_key']

        # 4. 执行 AgentNode
        result = await agent.execute(agent_node, context)

        # 验证结果
        assert 'error' not in result, f'执行出错: {result.get("error")}'
        assert result['content'], '响应内容不应为空'
        assert result['model'] == OLLAMA_MODEL_ID
        # 检查响应中包含 "2"
        assert '2' in result['content'], f'响应应包含答案2: {result["content"]}'

        print('\n[Real Ollama] 问题: 1+1等于几？')
        print(f'[Real Ollama] 回答: {result["content"][:200]}...')

    async def test_real_ollama_with_system_prompt(self, workflow, execution_record):
        """测试真实 Ollama 带系统提示词"""
        context = ExecutionContext(workflow, execution_record, {'topic': 'Python'})

        # 初始化 OllamaNode
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

        await ollama_node.execute(ollama_config_node, context)

        # 执行 AgentNode
        agent = AgentNode()
        agent_node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='LLM',
            name='Expert Agent',
            config={
                'title': 'Expert Agent',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'expert_chat',
                'agent_strategy_label': 'Expert Chat',
                'system_prompt': '你是一个编程专家，用一句话简洁回答。',
                'user_prompt': '用一句话介绍{topic}',
                'temperature': 0.3,
                'max_tokens': 200,
            },
        )

        result = await agent.execute(agent_node, context)

        assert 'error' not in result, f'执行出错: {result.get("error")}'
        assert result['content'], '响应内容不应为空'

        print('\n[Real Ollama] 问题: 用一句话介绍Python')
        print(f'[Real Ollama] 回答: {result["content"][:300]}...')

    async def test_real_ollama_structured_output(self, workflow, execution_record):
        """测试真实 Ollama 结构化输出"""
        context = ExecutionContext(workflow, execution_record, {'number': '15'})

        # 初始化 OllamaNode
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

        await ollama_node.execute(ollama_config_node, context)

        # 执行 AgentNode 带结构化输出
        agent = AgentNode()
        agent_node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='LLM',
            name='Structured Agent',
            config={
                'title': 'Structured Agent',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'structured_chat',
                'agent_strategy_label': 'Structured Chat',
                'system_prompt': '你是一个数学助手，必须按照指定的JSON格式输出。',
                'user_prompt': '判断{number}是奇数还是偶数',
                'output_schema': {'number': 'number', 'is_odd': 'boolean', 'reason': 'string'},
                'temperature': 0.1,
                'max_tokens': 500,
            },
        )

        result = await agent.execute(agent_node, context)

        assert 'error' not in result, f'执行出错: {result.get("error")}'
        assert result['content'], '响应内容不应为空'
        assert 'extracted' in result

        print('\n[Real Ollama] 问题: 判断15是奇数还是偶数')
        print(f'[Real Ollama] 原始回答: {result["content"][:300]}...')
        print(f'[Real Ollama] 提取结果: {result["extracted"]}')

    async def test_real_ollama_multi_turn_conversation(self, workflow, execution_record):
        """测试真实 Ollama 多轮对话"""
        context = ExecutionContext(workflow, execution_record, {})

        # 初始化 OllamaNode
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

        await ollama_node.execute(ollama_config_node, context)

        agent = AgentNode()

        # 第一轮对话
        context.update_global_variable('user_input', '我叫小明')
        node1 = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='LLM',
            name='Chat Agent',
            config={
                'title': 'Chat Agent',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'multi_turn',
                'agent_strategy_label': 'Multi Turn Chat',
                'system_prompt': '你是一个友好的助手，记住用户告诉你的信息。',
                'user_prompt': '我叫小明',
                'temperature': 0.3,
                'max_tokens': 200,
            },
        )

        result1 = await agent.execute(node1, context)
        assert 'error' not in result1, f'第一轮出错: {result1.get("error")}'

        print('\n[Real Ollama] 第一轮 - 用户: 我叫小明')
        print(f'[Real Ollama] 第一轮 - 助手: {result1["content"][:200]}...')

        # 第二轮对话 - 测试记忆
        node2 = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='LLM',
            name='Chat Agent',
            config={
                'title': 'Chat Agent',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'multi_turn',  # 使用相同的策略名以共享消息缓存
                'agent_strategy_label': 'Multi Turn Chat',
                'user_prompt': '我叫什么名字？',
                'temperature': 0.3,
                'max_tokens': 200,
            },
        )

        result2 = await agent.execute(node2, context)
        assert 'error' not in result2, f'第二轮出错: {result2.get("error")}'

        print('[Real Ollama] 第二轮 - 用户: 我叫什么名字？')
        print(f'[Real Ollama] 第二轮 - 助手: {result2["content"][:200]}...')

        # 验证消息缓存
        cache = OllamaNode.get_message_cache_from_context(context, 'multi_turn')
        messages = cache.get_messages()
        assert len(messages) >= 4, f'应该有至少4条消息（2轮对话），实际: {len(messages)}'

    async def test_real_ollama_workflow_chain(self, workflow, execution_record):
        """测试真实 Ollama 工作流链式调用"""
        context = ExecutionContext(workflow, execution_record, {'text': 'Hello World'})

        # 初始化 OllamaNode
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

        await ollama_node.execute(ollama_config_node, context)

        # Agent 1: 翻译
        agent1 = AgentNode()
        node1 = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='LLM',
            name='Translator',
            config={
                'title': 'Translator',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'translator',
                'agent_strategy_label': 'Translator',
                'system_prompt': '你是一个翻译助手，只输出翻译结果，不要解释。',
                'user_prompt': '将以下英文翻译成中文: {text}',
                'temperature': 0.1,
                'max_tokens': 200,
            },
        )

        result1 = await agent1.execute(node1, context)
        assert 'error' not in result1, f'翻译出错: {result1.get("error")}'

        print('\n[Real Ollama] 翻译任务')
        print('[Real Ollama] 输入: Hello World')
        print(f'[Real Ollama] 翻译: {result1["content"][:100]}...')

        # 将翻译结果传递给下一个 Agent
        context.update_global_variable('translated', result1['content'])

        # Agent 2: 分析
        agent2 = AgentNode()
        node2 = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='LLM',
            name='Analyzer',
            config={
                'title': 'Analyzer',
                'agent_strategy_provider_name': 'ollama',
                'agent_strategy_name': 'analyzer',
                'agent_strategy_label': 'Analyzer',
                'system_prompt': '你是一个文本分析助手，简洁回答。',
                'user_prompt': '这段中文"{translated}"表达了什么意思？用一句话回答。',
                'temperature': 0.3,
                'max_tokens': 200,
            },
        )

        result2 = await agent2.execute(node2, context)
        assert 'error' not in result2, f'分析出错: {result2.get("error")}'

        print(f'[Real Ollama] 分析: {result2["content"][:200]}...')
