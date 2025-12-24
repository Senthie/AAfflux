"""
工作流引擎单元测试

来自: test_workflow_engine.py

测试内容:
- 拓扑排序
- 执行上下文
- 节点执行器注册
- 内置执行器
"""

from typing import Any, Dict, List
from uuid import uuid4

from hypothesis import given, settings, strategies as st
import pytest

from app.engine.execution_context import ExecutionContext
from app.engine.node_executor import (
    BaseNode,
    node_executor_registry,
    register_node_executor,
)
from app.engine.topological_sorter import TopologicalSorter
from app.engine.workflow_engine import WorkflowEngine
from app.models.workflow.workflow import Connection, ExecutionRecord, Node, Workflow


class TestTopologicalSorter:
    """拓扑排序测试"""

    def test_sort_simple_workflow(self):
        """Test sorting a simple linear workflow."""
        node1 = Node(
            id=uuid4(),
            workflow_id=uuid4(),
            type='START',
            name='Start',
            config={},
            position={'x': 0, 'y': 0},
        )
        node2 = Node(
            id=uuid4(),
            workflow_id=node1.workflow_id,
            type='PROCESS',
            name='Process',
            config={},
            position={'x': 100, 'y': 0},
        )
        node3 = Node(
            id=uuid4(),
            workflow_id=node1.workflow_id,
            type='END',
            name='End',
            config={},
            position={'x': 200, 'y': 0},
        )

        conn1 = Connection(
            id=uuid4(),
            workflow_id=node1.workflow_id,
            source_node_id=node1.id,
            target_node_id=node2.id,
            source_output='output',
            target_input='input',
        )
        conn2 = Connection(
            id=uuid4(),
            workflow_id=node1.workflow_id,
            source_node_id=node2.id,
            target_node_id=node3.id,
            source_output='output',
            target_input='input',
        )

        sorter = TopologicalSorter([node1, node2, node3], [conn1, conn2])
        sorted_nodes = sorter.sort()

        assert len(sorted_nodes) == 3
        assert sorted_nodes[0].id == node1.id
        assert sorted_nodes[1].id == node2.id
        assert sorted_nodes[2].id == node3.id

    def test_get_execution_levels(self):
        """Test getting execution levels for parallel execution."""
        node1 = Node(
            id=uuid4(),
            workflow_id=uuid4(),
            type='START',
            name='Start',
            config={},
            position={'x': 0, 'y': 0},
        )
        node2 = Node(
            id=uuid4(),
            workflow_id=node1.workflow_id,
            type='PROCESS',
            name='Process1',
            config={},
            position={'x': 100, 'y': 0},
        )
        node3 = Node(
            id=uuid4(),
            workflow_id=node1.workflow_id,
            type='PROCESS',
            name='Process2',
            config={},
            position={'x': 100, 'y': 100},
        )
        node4 = Node(
            id=uuid4(),
            workflow_id=node1.workflow_id,
            type='END',
            name='End',
            config={},
            position={'x': 200, 'y': 50},
        )

        connections = [
            Connection(
                id=uuid4(),
                workflow_id=node1.workflow_id,
                source_node_id=node1.id,
                target_node_id=node2.id,
                source_output='output',
                target_input='input',
            ),
            Connection(
                id=uuid4(),
                workflow_id=node1.workflow_id,
                source_node_id=node1.id,
                target_node_id=node3.id,
                source_output='output',
                target_input='input',
            ),
            Connection(
                id=uuid4(),
                workflow_id=node1.workflow_id,
                source_node_id=node2.id,
                target_node_id=node4.id,
                source_output='output',
                target_input='input1',
            ),
            Connection(
                id=uuid4(),
                workflow_id=node1.workflow_id,
                source_node_id=node3.id,
                target_node_id=node4.id,
                source_output='output',
                target_input='input2',
            ),
        ]

        sorter = TopologicalSorter([node1, node2, node3, node4], connections)
        levels = sorter.get_execution_levels()

        assert len(levels) == 3
        assert len(levels[0]) == 1  # node1
        assert len(levels[1]) == 2  # node2, node3 (parallel)
        assert len(levels[2]) == 1  # node4


class TestExecutionContext:
    """执行上下文测试"""

    def test_context_initialization(self):
        """Test execution context initialization."""
        workflow = Workflow(
            id=uuid4(),
            name='Test Workflow',
            workspace_id=uuid4(),
            created_by=uuid4(),
            input_schema={'type': 'object'},
            output_schema={'type': 'object'},
        )

        execution_record = ExecutionRecord(
            id=uuid4(), workflow_id=workflow.id, inputs={'test': 'value'}, status='PENDING'
        )

        initial_inputs = {'input1': 'value1', 'input2': 'value2'}
        context = ExecutionContext(workflow, execution_record, initial_inputs)

        assert context.workflow.id == workflow.id
        assert context.execution_record.id == execution_record.id
        assert context.initial_inputs == initial_inputs
        assert len(context.completed_nodes) == 0

    def test_node_output_management(self):
        """Test node output setting and getting."""
        workflow = Workflow(
            id=uuid4(), name='Test Workflow', workspace_id=uuid4(), created_by=uuid4()
        )
        execution_record = ExecutionRecord(
            id=uuid4(), workflow_id=workflow.id, inputs={}, status='PENDING'
        )
        context = ExecutionContext(workflow, execution_record, {})

        node_id = uuid4()
        outputs = {'result': 'success', 'count': 42}

        context.set_node_output(node_id, outputs)
        retrieved_outputs = context.get_node_output(node_id)
        assert retrieved_outputs == outputs

        empty_outputs = context.get_node_output(uuid4())
        assert empty_outputs == {}


class TestNodeExecutorRegistry:
    """节点执行器注册测试"""

    def test_register_and_get_executor(self):
        """Test registering and retrieving executors."""

        @register_node_executor('TEST_NODE')
        class TestNodeExecutor(BaseNode):
            def __init__(self):
                super().__init__()

            @classmethod
            def version(cls) -> str:
                return '1'

            def init_node_data(self, data):
                pass

            def _get_error_strategy(self):
                return None

            def _get_retry_config(self):
                from app.engine.nodes.base.entities import RetryConfig

                return RetryConfig()

            def _get_title(self) -> str:
                return 'Test Node'

            def _get_description(self):
                return None

            async def execute(self, node, context):
                return {'test': 'result'}

            def validate_config(self, config):
                return True

        assert node_executor_registry.is_registered('TEST_NODE')
        assert 'TEST_NODE' in node_executor_registry.get_registered_types()

        executor = node_executor_registry.get_executor('TEST_NODE')
        assert isinstance(executor, TestNodeExecutor)

    def test_unregistered_node_type(self):
        """Test handling of unregistered node types."""
        with pytest.raises(ValueError, match='No executor registered for node type'):
            node_executor_registry.get_executor('NONEXISTENT_TYPE')


class TestBuiltinExecutors:
    """内置执行器测试"""

    @pytest.mark.asyncio
    async def test_start_node_executor(self):
        """Test START node executor."""
        from app.engine.node_executor import StartNodeExecutor

        executor = StartNodeExecutor()
        workflow = Workflow(id=uuid4(), name='Test', workspace_id=uuid4(), created_by=uuid4())
        execution_record = ExecutionRecord(
            id=uuid4(), workflow_id=workflow.id, inputs={}, status='PENDING'
        )
        initial_inputs = {'start_data': 'test'}
        context = ExecutionContext(workflow, execution_record, initial_inputs)

        node = Node(id=uuid4(), workflow_id=workflow.id, type='START', name='Start', config={})
        result = await executor.execute(node, context)
        assert result == initial_inputs

    @pytest.mark.asyncio
    async def test_passthrough_node_executor(self):
        """Test PASSTHROUGH node executor."""
        from app.engine.node_executor import PassthroughNodeExecutor

        executor = PassthroughNodeExecutor()
        workflow = Workflow(id=uuid4(), name='Test', workspace_id=uuid4(), created_by=uuid4())
        execution_record = ExecutionRecord(
            id=uuid4(), workflow_id=workflow.id, inputs={}, status='PENDING'
        )
        context = ExecutionContext(workflow, execution_record, {'input': 'test'})

        node = Node(id=uuid4(), workflow_id=workflow.id, type='PASSTHROUGH', name='Pass', config={})
        result = await executor.execute(node, context)
        assert result == context.global_variables


class TestWorkflowEngineProperties:
    """工作流引擎属性测试"""

    @settings(max_examples=100)
    @given(
        required_fields=st.lists(
            st.text(
                min_size=1,
                max_size=20,
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            ),
            min_size=0,
            max_size=5,
            unique=True,
        ),
        provided_inputs=st.dictionaries(
            keys=st.text(
                min_size=1,
                max_size=20,
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            ),
            values=st.one_of(st.text(), st.integers(), st.booleans()),
            min_size=0,
            max_size=10,
        ),
    )
    def test_input_parameter_validation_property(
        self, required_fields: List[str], provided_inputs: Dict[str, Any]
    ):
        """Property 32: Input parameter validation"""
        workflow = Workflow(
            id=uuid4(),
            name='Test Workflow',
            workspace_id=uuid4(),
            created_by=uuid4(),
            input_schema={
                'type': 'object',
                'required': required_fields,
                'properties': {field: {'type': 'string'} for field in required_fields},
            },
            output_schema={'type': 'object'},
        )

        engine = WorkflowEngine(db=None)
        missing_fields = [field for field in required_fields if field not in provided_inputs]

        if missing_fields:
            with pytest.raises(ValueError) as exc_info:
                engine._validate_inputs(workflow, provided_inputs)
            assert 'Missing required input fields' in str(exc_info.value)
        else:
            try:
                engine._validate_inputs(workflow, provided_inputs)
                assert True
            except ValueError:
                pytest.fail('Validation failed unexpectedly')
