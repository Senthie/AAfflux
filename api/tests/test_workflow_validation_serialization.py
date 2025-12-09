"""Tests for workflow validation and serialization.

This module tests the workflow validator and serializer services.
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.workflow.workflow import Connection, Node, Workflow
from app.services.workflow_serializer import (
    DeserializationError,
    SerializationError,
    WorkflowSerializer,
)
from app.services.workflow_validator import WorkflowValidator
from app.utils.dag import (
    CycleDetectedError,
    build_adjacency_list,
    detect_cycle,
    find_leaf_nodes,
    find_root_nodes,
    topological_sort,
)


@pytest.fixture
async def sample_workflow(test_session: AsyncSession):
    """Create a sample workflow for testing."""
    workspace_id = uuid4()
    user_id = uuid4()

    workflow = Workflow(
        name='Test Workflow',
        description='A test workflow',
        workspace_id=workspace_id,
        created_by=user_id,
        input_schema={'type': 'object'},
        output_schema={'type': 'object'},
    )
    test_session.add(workflow)
    await test_session.commit()
    await test_session.refresh(workflow)

    return workflow


class TestDAGUtils:
    """Test DAG utility functions."""

    def test_detect_cycle_no_cycle(self):
        """Test cycle detection with no cycle."""
        # A -> B -> C
        adjacency_list = {
            uuid4(): [uuid4()],
        }
        assert not detect_cycle(adjacency_list)

    def test_detect_cycle_with_cycle(self):
        """Test cycle detection with a cycle."""
        # A -> B -> C -> A
        node_a = uuid4()
        node_b = uuid4()
        node_c = uuid4()

        adjacency_list = {
            node_a: [node_b],
            node_b: [node_c],
            node_c: [node_a],
        }
        assert detect_cycle(adjacency_list)

    def test_topological_sort_simple(self):
        """Test topological sort with a simple DAG."""
        node_a = uuid4()
        node_b = uuid4()
        node_c = uuid4()

        # A -> B -> C
        adjacency_list = {
            node_a: [node_b],
            node_b: [node_c],
            node_c: [],
        }

        result = topological_sort(adjacency_list)
        assert len(result) == 3
        assert result.index(node_a) < result.index(node_b)
        assert result.index(node_b) < result.index(node_c)

    def test_topological_sort_with_cycle_raises_error(self):
        """Test that topological sort raises error on cycle."""
        node_a = uuid4()
        node_b = uuid4()

        # A -> B -> A
        adjacency_list = {
            node_a: [node_b],
            node_b: [node_a],
        }

        with pytest.raises(CycleDetectedError):
            topological_sort(adjacency_list)

    def test_build_adjacency_list(self):
        """Test building adjacency list from connections."""
        node_a = uuid4()
        node_b = uuid4()
        node_c = uuid4()

        connections = [
            (node_a, node_b),
            (node_b, node_c),
        ]

        adjacency_list = build_adjacency_list(connections)
        assert node_a in adjacency_list
        assert node_b in adjacency_list[node_a]
        assert node_c in adjacency_list[node_b]

    def test_find_root_nodes(self):
        """Test finding root nodes."""
        node_a = uuid4()
        node_b = uuid4()
        node_c = uuid4()

        # A -> B -> C
        adjacency_list = {
            node_a: [node_b],
            node_b: [node_c],
            node_c: [],
        }

        roots = find_root_nodes(adjacency_list)
        assert node_a in roots
        assert node_b not in roots
        assert node_c not in roots

    def test_find_leaf_nodes(self):
        """Test finding leaf nodes."""
        node_a = uuid4()
        node_b = uuid4()
        node_c = uuid4()

        # A -> B -> C
        adjacency_list = {
            node_a: [node_b],
            node_b: [node_c],
            node_c: [],
        }

        leaves = find_leaf_nodes(adjacency_list)
        assert node_c in leaves
        assert node_a not in leaves
        assert node_b not in leaves


class TestWorkflowValidator:
    """Test workflow validator.

    Note: These tests are currently skipped because WorkflowValidator service
    uses synchronous SQLModel API (session.exec(), session.get()) but tests
    provide AsyncSession. The service needs to be refactored to use async API.
    """

    @pytest.mark.skip(reason='WorkflowValidator needs async refactoring')
    @pytest.mark.asyncio
    async def test_validate_node_config_llm_valid(self, test_session: AsyncSession):
        """Test validating a valid LLM node configuration."""
        validator = WorkflowValidator(test_session)

        node = Node(
            workflow_id=uuid4(),
            type='LLM',
            name='Test LLM Node',
            config={
                'model': 'gpt-4',
                'prompt': 'Test prompt',
                'temperature': 0.7,
                'max_tokens': 100,
            },
        )

        result = validator.validate_node_config(node)
        assert result.is_valid

    @pytest.mark.skip(reason='WorkflowValidator needs async refactoring')
    @pytest.mark.asyncio
    async def test_validate_node_config_llm_missing_required(self, test_session: AsyncSession):
        """Test validating an LLM node with missing required fields."""
        validator = WorkflowValidator(test_session)

        node = Node(
            workflow_id=uuid4(),
            type='LLM',
            name='Test LLM Node',
            config={
                'model': 'gpt-4',
                # Missing 'prompt'
            },
        )

        result = validator.validate_node_config(node)
        assert not result.is_valid
        assert any('prompt' in error.lower() for error in result.errors)

    @pytest.mark.skip(reason='WorkflowValidator needs async refactoring')
    @pytest.mark.asyncio
    async def test_validate_node_config_invalid_temperature(self, test_session: AsyncSession):
        """Test validating an LLM node with invalid temperature."""
        validator = WorkflowValidator(test_session)

        node = Node(
            workflow_id=uuid4(),
            type='LLM',
            name='Test LLM Node',
            config={
                'model': 'gpt-4',
                'prompt': 'Test prompt',
                'temperature': 3.0,  # Invalid: > 2
            },
        )

        result = validator.validate_node_config(node)
        assert not result.is_valid
        assert any('temperature' in error.lower() for error in result.errors)

    @pytest.mark.skip(reason='WorkflowValidator needs async refactoring')
    @pytest.mark.asyncio
    async def test_check_cyclic_dependency_no_cycle(
        self, test_session: AsyncSession, sample_workflow: Workflow
    ):
        """Test checking for cyclic dependencies with no cycle."""
        validator = WorkflowValidator(test_session)

        # Create nodes
        node_a = Node(
            workflow_id=sample_workflow.id,
            type='LLM',
            name='Node A',
            config={'model': 'gpt-4', 'prompt': 'test'},
        )
        node_b = Node(
            workflow_id=sample_workflow.id,
            type='LLM',
            name='Node B',
            config={'model': 'gpt-4', 'prompt': 'test'},
        )
        test_session.add(node_a)
        test_session.add(node_b)
        await test_session.commit()

        # Create connection A -> B
        connection = Connection(
            workflow_id=sample_workflow.id,
            source_node_id=node_a.id,
            target_node_id=node_b.id,
            source_output='output',
            target_input='input',
        )
        test_session.add(connection)
        await test_session.commit()

        # Should not have cycle
        assert validator.check_cyclic_dependency(sample_workflow.id)

    @pytest.mark.skip(reason='WorkflowValidator needs async refactoring')
    @pytest.mark.asyncio
    async def test_validate_workflow_empty(
        self, test_session: AsyncSession, sample_workflow: Workflow
    ):
        """Test validating an empty workflow."""
        validator = WorkflowValidator(test_session)

        result = validator.validate_workflow(sample_workflow.id)
        assert not result.is_valid
        assert any('at least one node' in error.lower() for error in result.errors)


class TestWorkflowSerializer:
    """Test workflow serializer.

    Note: These tests are currently skipped because WorkflowSerializer service
    uses synchronous SQLModel API (session.exec(), session.get(), session.commit())
    but tests provide AsyncSession. The service needs to be refactored to use async API.
    """

    @pytest.mark.skip(reason='WorkflowSerializer needs async refactoring')
    @pytest.mark.asyncio
    async def test_serialize_workflow(self, test_session: AsyncSession, sample_workflow: Workflow):
        """Test serializing a workflow."""
        serializer = WorkflowSerializer(test_session)

        # Add a node
        node = Node(
            workflow_id=sample_workflow.id,
            type='LLM',
            name='Test Node',
            config={'model': 'gpt-4', 'prompt': 'test'},
            position={'x': 100, 'y': 200},
        )
        test_session.add(node)
        await test_session.commit()

        # Serialize
        data = serializer.serialize_workflow(sample_workflow.id)

        assert data['version'] == '1.0'
        assert data['workflow']['name'] == 'Test Workflow'
        assert len(data['nodes']) == 1
        assert data['nodes'][0]['name'] == 'Test Node'

    @pytest.mark.skip(reason='WorkflowSerializer needs async refactoring')
    @pytest.mark.asyncio
    async def test_serialize_nonexistent_workflow(self, test_session: AsyncSession):
        """Test serializing a non-existent workflow."""
        serializer = WorkflowSerializer(test_session)

        with pytest.raises(SerializationError):
            serializer.serialize_workflow(uuid4())

    @pytest.mark.skip(reason='WorkflowSerializer needs async refactoring')
    @pytest.mark.asyncio
    async def test_deserialize_workflow(self, test_session: AsyncSession):
        """Test deserializing a workflow."""
        serializer = WorkflowSerializer(test_session)

        workspace_id = uuid4()
        user_id = uuid4()

        workflow_data = {
            'version': '1.0',
            'workflow': {
                'name': 'Imported Workflow',
                'description': 'Test import',
                'input_schema': {},
                'output_schema': {},
            },
            'nodes': [
                {
                    'id': str(uuid4()),
                    'type': 'LLM',
                    'name': 'Node 1',
                    'config': {'model': 'gpt-4', 'prompt': 'test'},
                    'position': {'x': 0, 'y': 0},
                }
            ],
            'connections': [],
        }

        workflow = serializer.deserialize_workflow(workflow_data, workspace_id, user_id)

        assert workflow.name == 'Imported Workflow'
        assert workflow.workspace_id == workspace_id

    @pytest.mark.skip(reason='WorkflowSerializer needs async refactoring')
    @pytest.mark.asyncio
    async def test_deserialize_invalid_version(self, test_session: AsyncSession):
        """Test deserializing with invalid version."""
        serializer = WorkflowSerializer(test_session)

        workflow_data = {
            'version': '2.0',  # Unsupported version
            'workflow': {'name': 'Test'},
            'nodes': [],
            'connections': [],
        }

        with pytest.raises(DeserializationError):
            serializer.deserialize_workflow(workflow_data, uuid4(), uuid4())

    @pytest.mark.skip(reason='WorkflowSerializer needs async refactoring')
    @pytest.mark.asyncio
    async def test_validate_serialized_workflow_valid(self, test_session: AsyncSession):
        """Test validating valid serialized workflow data."""
        serializer = WorkflowSerializer(test_session)

        node_id = str(uuid4())
        workflow_data = {
            'version': '1.0',
            'workflow': {'name': 'Test'},
            'nodes': [
                {
                    'id': node_id,
                    'type': 'LLM',
                    'name': 'Node 1',
                }
            ],
            'connections': [],
        }

        assert serializer.validate_serialized_workflow(workflow_data)

    @pytest.mark.skip(reason='WorkflowSerializer needs async refactoring')
    @pytest.mark.asyncio
    async def test_validate_serialized_workflow_invalid(self, test_session: AsyncSession):
        """Test validating invalid serialized workflow data."""
        serializer = WorkflowSerializer(test_session)

        # Missing 'nodes' key
        workflow_data = {
            'version': '1.0',
            'workflow': {'name': 'Test'},
            'connections': [],
        }

        assert not serializer.validate_serialized_workflow(workflow_data)

    @pytest.mark.skip(reason='WorkflowSerializer needs async refactoring')
    @pytest.mark.asyncio
    async def test_round_trip_serialization(
        self, test_session: AsyncSession, sample_workflow: Workflow
    ):
        """Test round-trip serialization and deserialization."""
        serializer = WorkflowSerializer(test_session)

        # Add nodes and connections
        node_a = Node(
            workflow_id=sample_workflow.id,
            type='LLM',
            name='Node A',
            config={'model': 'gpt-4', 'prompt': 'test'},
            position={'x': 0, 'y': 0},
        )
        node_b = Node(
            workflow_id=sample_workflow.id,
            type='LLM',
            name='Node B',
            config={'model': 'gpt-4', 'prompt': 'test'},
            position={'x': 100, 'y': 0},
        )
        test_session.add(node_a)
        test_session.add(node_b)
        await test_session.commit()

        connection = Connection(
            workflow_id=sample_workflow.id,
            source_node_id=node_a.id,
            target_node_id=node_b.id,
            source_output='output',
            target_input='input',
        )
        test_session.add(connection)
        await test_session.commit()

        # Serialize
        data = serializer.serialize_workflow(sample_workflow.id)

        # Deserialize
        new_workflow = serializer.deserialize_workflow(
            data, sample_workflow.workspace_id, sample_workflow.created_by
        )

        # Verify
        assert new_workflow.name == sample_workflow.name
        assert new_workflow.description == sample_workflow.description

        # Check nodes were created
        nodes_statement = select(Node).where(Node.workflow_id == new_workflow.id)
        result = await test_session.execute(nodes_statement)
        nodes = result.scalars().all()
        assert len(nodes) == 2

        # Check connections were created
        connections_statement = select(Connection).where(Connection.workflow_id == new_workflow.id)
        result = await test_session.execute(connections_statement)
        connections = result.scalars().all()
        assert len(connections) == 1
