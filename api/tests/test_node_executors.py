"""
Tests for node executor implementations.

This module contains property-based tests for various node executors
to verify their correctness according to the specification.
"""

from uuid import uuid4

from hypothesis import given, settings, strategies as st
import pytest

from app.engine.execution_context import ExecutionContext
from app.engine.nodes.condition_node import ConditionNodeExecutor
from app.models.workflow.workflow import ExecutionRecord, Node, Workflow


class TestConditionNodeExecutor:
    """Tests for condition node executor."""

    @pytest.mark.asyncio
    async def test_basic_condition_evaluation(self):
        """Test basic condition evaluation functionality."""
        executor = ConditionNodeExecutor()

        # Create test workflow and context
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

        # Test true condition
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
        assert result['condition'] == 'x > y'

        # Test false condition
        node.config['condition'] = 'x < y'
        result = await executor.execute(node, context)

        assert result['result'] is False
        assert result['branch'] == 'failure_path'

    # Feature: low-code-platform-backend, Property 54: 条件节点分支路由
    @settings(max_examples=100)
    @given(
        # Generate various condition expressions and input values
        x_value=st.integers(min_value=-100, max_value=100),
        y_value=st.integers(min_value=-100, max_value=100),
        condition_type=st.sampled_from(['x > y', 'x < y', 'x == y', 'x >= y', 'x <= y', 'x != y']),
        true_branch=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')),
        ),
        false_branch=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')),
        ),
    )
    @pytest.mark.asyncio
    async def test_condition_node_branch_routing_property(
        self, x_value: int, y_value: int, condition_type: str, true_branch: str, false_branch: str
    ):
        """
        Property 54: Condition node branch routing
        For any condition node, it should select the correct branch based on expression evaluation result.

        **Validates: Requirements 13.2**
        """
        # Ensure branches are different to avoid ambiguity
        if true_branch == false_branch:
            false_branch = false_branch + '_alt'

        executor = ConditionNodeExecutor()

        # Create test workflow and context
        workflow = Workflow(
            id=uuid4(),
            name='Test Workflow',
            workspace_id=uuid4(),
            created_by=uuid4(),
        )

        execution_record = ExecutionRecord(
            id=uuid4(), workflow_id=workflow.id, inputs={}, status='PENDING'
        )

        # Set up context with input variables
        context = ExecutionContext(workflow, execution_record, {'x': x_value, 'y': y_value})

        # Create condition node
        node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='CONDITION',
            name='Test Condition',
            config={
                'condition': condition_type,
                'true_branch': true_branch,
                'false_branch': false_branch,
            },
        )

        # Execute the node
        result = await executor.execute(node, context)

        # Calculate expected result based on condition
        expected_result = self._evaluate_condition(condition_type, x_value, y_value)
        expected_branch = true_branch if expected_result else false_branch

        # Verify the property: condition evaluation result should match expected result
        assert result['result'] == expected_result, (
            f"Condition '{condition_type}' with x={x_value}, y={y_value} "
            f'should evaluate to {expected_result}, but got {result["result"]}'
        )

        # Verify the property: branch selection should match condition result
        assert result['branch'] == expected_branch, (
            f"Condition '{condition_type}' with result {expected_result} "
            f"should select branch '{expected_branch}', but got '{result['branch']}'"
        )

        # Verify that the condition expression is preserved
        assert result['condition'] == condition_type

        # Verify that inputs are recorded
        assert 'inputs_used' in result
        assert result['inputs_used']['x'] == x_value
        assert result['inputs_used']['y'] == y_value

    def _evaluate_condition(self, condition: str, x: int, y: int) -> bool:
        """Helper method to evaluate condition expressions for verification."""
        if condition == 'x > y':
            return x > y
        elif condition == 'x < y':
            return x < y
        elif condition == 'x == y':
            return x == y
        elif condition == 'x >= y':
            return x >= y
        elif condition == 'x <= y':
            return x <= y
        elif condition == 'x != y':
            return x != y
        else:
            raise ValueError(f'Unknown condition type: {condition}')

    @settings(max_examples=100)
    @given(
        # Test with boolean values and logical operators
        a_value=st.booleans(),
        b_value=st.booleans(),
        condition_type=st.sampled_from(['a and b', 'a or b', 'not a', 'a and not b', 'not a or b']),
        true_branch=st.text(
            min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))
        ),
        false_branch=st.text(
            min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))
        ),
    )
    @pytest.mark.asyncio
    async def test_condition_node_boolean_logic_property(
        self, a_value: bool, b_value: bool, condition_type: str, true_branch: str, false_branch: str
    ):
        """
        Property 54 (Boolean variant): Condition node branch routing with boolean logic
        For any condition node with boolean expressions, it should select the correct branch.

        **Validates: Requirements 13.2**
        """
        # Ensure branches are different
        if true_branch == false_branch:
            false_branch = false_branch + '_alt'

        executor = ConditionNodeExecutor()

        # Create test workflow and context
        workflow = Workflow(
            id=uuid4(),
            name='Test Workflow',
            workspace_id=uuid4(),
            created_by=uuid4(),
        )

        execution_record = ExecutionRecord(
            id=uuid4(), workflow_id=workflow.id, inputs={}, status='PENDING'
        )

        # Set up context with boolean variables
        context = ExecutionContext(workflow, execution_record, {'a': a_value, 'b': b_value})

        # Create condition node
        node = Node(
            id=uuid4(),
            workflow_id=workflow.id,
            type='CONDITION',
            name='Boolean Condition',
            config={
                'condition': condition_type,
                'true_branch': true_branch,
                'false_branch': false_branch,
            },
        )

        # Execute the node
        result = await executor.execute(node, context)

        # Calculate expected result based on boolean condition
        expected_result = self._evaluate_boolean_condition(condition_type, a_value, b_value)
        expected_branch = true_branch if expected_result else false_branch

        # Verify the property: boolean condition evaluation should be correct
        assert result['result'] == expected_result, (
            f"Boolean condition '{condition_type}' with a={a_value}, b={b_value} "
            f'should evaluate to {expected_result}, but got {result["result"]}'
        )

        # Verify the property: branch selection should match boolean result
        assert result['branch'] == expected_branch, (
            f"Boolean condition '{condition_type}' with result {expected_result} "
            f"should select branch '{expected_branch}', but got '{result['branch']}'"
        )

    def _evaluate_boolean_condition(self, condition: str, a: bool, b: bool) -> bool:
        """Helper method to evaluate boolean condition expressions."""
        if condition == 'a and b':
            return a and b
        elif condition == 'a or b':
            return a or b
        elif condition == 'not a':
            return not a
        elif condition == 'a and not b':
            return a and not b
        elif condition == 'not a or b':
            return not a or b
        else:
            raise ValueError(f'Unknown boolean condition: {condition}')

    @pytest.mark.asyncio
    async def test_condition_node_config_validation(self):
        """Test condition node configuration validation."""
        executor = ConditionNodeExecutor()

        # Valid configuration
        valid_config = {'condition': 'x > 0', 'true_branch': 'success', 'false_branch': 'failure'}
        assert executor.validate_config(valid_config) is True

        # Missing condition
        invalid_config = {'true_branch': 'success', 'false_branch': 'failure'}
        assert executor.validate_config(invalid_config) is False

        # Empty condition
        invalid_config = {'condition': '', 'true_branch': 'success', 'false_branch': 'failure'}
        assert executor.validate_config(invalid_config) is False

        # Invalid syntax
        invalid_config = {
            'condition': 'x > > y',  # Invalid syntax
            'true_branch': 'success',
            'false_branch': 'failure',
        }
        assert executor.validate_config(invalid_config) is False
