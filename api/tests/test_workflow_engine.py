"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-10 16:03:29
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-10 16:13:17
FilePath: /api/tests/test_workflow_engine.py
Description:Tests for workflow execution engine components.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Any, Dict, List
from uuid import uuid4

from hypothesis import given, settings, strategies as st
import pytest

from app.engine.execution_context import ExecutionContext
from app.engine.node_executor import (
    BaseNodeExecutor,
    NodeExecutorRegistry,
    node_executor_registry,
    register_node_executor,
)
from app.engine.topological_sorter import TopologicalSorter
from app.engine.workflow_engine import WorkflowEngine
from app.models.workflow.workflow import (
    Connection,
    ExecutionRecord,
    Node,
    Workflow,
)


class TestTopologicalSorter:
    """Test topological sorting functionality."""

    def test_sort_simple_workflow(self):
        """Test sorting a simple linear workflow."""
        # Create nodes
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

        # Create connections
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

        # Create sorter and sort
        sorter = TopologicalSorter([node1, node2, node3], [conn1, conn2])
        sorted_nodes = sorter.sort()

        # Verify order
        assert len(sorted_nodes) == 3
        assert sorted_nodes[0].id == node1.id
        assert sorted_nodes[1].id == node2.id
        assert sorted_nodes[2].id == node3.id

    def test_get_execution_levels(self):
        """
        Test getting execution levels for parallel execution.
        """
        # Create nodes that can be executed in parallel
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

        # Create connections (node1 -> node2, node1 -> node3, node2 -> node4, node3 -> node4)
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

        # Create sorter and get levels
        sorter = TopologicalSorter([node1, node2, node3, node4], connections)
        levels = sorter.get_execution_levels()

        # Verify levels
        assert len(levels) == 3
        assert len(levels[0]) == 1  # node1
        assert len(levels[1]) == 2  # node2, node3 (parallel)
        assert len(levels[2]) == 1  # node4

        # Verify node1 is in first level
        assert levels[0][0].id == node1.id

        # Verify node2 and node3 are in second level (can be in any order)
        level1_ids = {node.id for node in levels[1]}
        assert node2.id in level1_ids
        assert node3.id in level1_ids

        # Verify node4 is in third level
        assert levels[2][0].id == node4.id


class TestExecutionContext:
    """Test execution context functionality."""

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
        assert context.global_variables == initial_inputs
        assert len(context.completed_nodes) == 0
        assert len(context.failed_nodes) == 0

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

        # Set outputs
        context.set_node_output(node_id, outputs)

        # Get outputs
        retrieved_outputs = context.get_node_output(node_id)
        assert retrieved_outputs == outputs

        # Check that outputs don't affect each other
        empty_outputs = context.get_node_output(uuid4())
        assert empty_outputs == {}


class TestNodeExecutorRegistry:
    """Test node executor registry functionality."""

    def test_register_and_get_executor(self):
        """Test registering and retrieving executors."""

        # Create a test executor
        @register_node_executor('TEST_NODE')
        class TestNodeExecutor(BaseNodeExecutor):
            def __init__(self):
                super().__init__()

            async def execute(self, node, context):
                return {'test': 'result'}

            def validate_config(self, config):
                return True

        # Check registration
        assert node_executor_registry.is_registered('TEST_NODE')
        assert 'TEST_NODE' in node_executor_registry.get_registered_types()

        # Get executor
        executor = node_executor_registry.get_executor('TEST_NODE')
        assert isinstance(executor, TestNodeExecutor)

        # Test singleton behavior
        executor2 = node_executor_registry.get_executor('TEST_NODE')
        assert executor is executor2

    def test_unregistered_node_type(self):
        """Test handling of unregistered node types."""
        with pytest.raises(ValueError, match='No executor registered for node type'):
            node_executor_registry.get_executor('NONEXISTENT_TYPE')

    def test_validate_node_config(self):
        """Test node configuration validation."""

        # Create a test executor with validation
        class ValidatingExecutor(BaseNodeExecutor):
            def __init__(self):
                super().__init__()

            async def execute(self, node, context):
                return {}

            def validate_config(self, config):
                return 'required_field' in config

        # Register manually for this test
        registry = NodeExecutorRegistry()
        registry.register('VALIDATING', ValidatingExecutor)

        # Test validation
        assert registry.validate_node_config('VALIDATING', {'required_field': 'value'})
        assert not registry.validate_node_config('VALIDATING', {'other_field': 'value'})


class TestBuiltinExecutors:
    """Test built-in node executors."""

    @pytest.mark.asyncio
    async def test_start_node_executor(self):
        """Test START node executor."""
        from app.engine.node_executor import StartNodeExecutor

        executor = StartNodeExecutor()

        # Create test data
        workflow = Workflow(id=uuid4(), name='Test', workspace_id=uuid4(), created_by=uuid4())
        execution_record = ExecutionRecord(
            id=uuid4(), workflow_id=workflow.id, inputs={}, status='PENDING'
        )
        initial_inputs = {'start_data': 'test'}
        context = ExecutionContext(workflow, execution_record, initial_inputs)

        node = Node(id=uuid4(), workflow_id=workflow.id, type='START', name='Start', config={})

        # Execute
        result = await executor.execute(node, context)

        # Verify result
        assert result == initial_inputs

    @pytest.mark.asyncio
    async def test_passthrough_node_executor(self):
        """Test PASSTHROUGH node executor."""
        from app.engine.node_executor import PassthroughNodeExecutor

        executor = PassthroughNodeExecutor()

        # Create test data
        workflow = Workflow(id=uuid4(), name='Test', workspace_id=uuid4(), created_by=uuid4())
        execution_record = ExecutionRecord(
            id=uuid4(), workflow_id=workflow.id, inputs={}, status='PENDING'
        )
        context = ExecutionContext(workflow, execution_record, {'input': 'test'})

        node = Node(id=uuid4(), workflow_id=workflow.id, type='PASSTHROUGH', name='Pass', config={})

        # Execute
        result = await executor.execute(node, context)

        # Verify result (should return global variables since no connections)
        assert result == context.global_variables


class TestWorkflowEngineProperties:
    """Property-based tests for workflow engine."""

    # Feature: low-code-platform-backend, Property 32: 输入参数验证
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
            values=st.one_of(
                st.text(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans(),
            ),
            min_size=0,
            max_size=10,
        ),
    )
    def test_input_parameter_validation_property(
        self, required_fields: List[str], provided_inputs: Dict[str, Any]
    ):
        """
        Property 32: Input parameter validation
        For any workflow execution request, the input parameters should match the workflow definition's input variables.

        **Validates: Requirements 8.1**
        """
        # Create a workflow with input schema
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

        # Create a mock workflow engine
        engine = WorkflowEngine(db=None)  # We'll test the validation method directly

        # Test the validation logic
        missing_fields = [field for field in required_fields if field not in provided_inputs]

        if missing_fields:
            # If there are missing required fields, validation should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                engine._validate_inputs(workflow, provided_inputs)
            # Check that the error message contains information about missing fields
            assert 'Missing required input fields' in str(exc_info.value)
            for field in missing_fields:
                assert field in str(exc_info.value)
        else:
            # If all required fields are present, validation should pass
            try:
                engine._validate_inputs(workflow, provided_inputs)
                # If no exception is raised, the validation passed as expected
                assert True
            except ValueError:
                # This should not happen when all required fields are present
                pytest.fail('Validation failed unexpectedly when all required fields were provided')
