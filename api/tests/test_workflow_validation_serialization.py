"""Tests for workflow validation and serialization.

This module tests the workflow validator and serializer services.
"""

from uuid import uuid4

import pytest
from sqlmodel import Session, SQLModel, create_engine

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
def db_session():
    """Create a test database session."""

    # Monkey patch JSONB to use JSON for SQLite
    import sqlalchemy.dialects.sqlite.base as sqlite_base

    original_visit = sqlite_base.SQLiteTypeCompiler.visit_JSON

    def visit_JSONB(self, type_, **kw):
        return self.visit_JSON(type_, **kw)

    sqlite_base.SQLiteTypeCompiler.visit_JSONB = visit_JSONB

    engine = create_engine('sqlite:///:memory:')
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def sample_workflow(db_session: Session):
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
    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)

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
    """Test workflow validator."""

    def test_validate_node_config_llm_valid(self, db_session: Session):
        """Test validating a valid LLM node configuration."""
        validator = WorkflowValidator(db_session)

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

    def test_validate_node_config_llm_missing_required(self, db_session: Session):
        """Test validating an LLM node with missing required fields."""
        validator = WorkflowValidator(db_session)

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

    def test_validate_node_config_invalid_temperature(self, db_session: Session):
        """Test validating an LLM node with invalid temperature."""
        validator = WorkflowValidator(db_session)

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

    def test_check_cyclic_dependency_no_cycle(self, db_session: Session, sample_workflow: Workflow):
        """Test checking for cyclic dependencies with no cycle."""
        validator = WorkflowValidator(db_session)

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
        db_session.add(node_a)
        db_session.add(node_b)
        db_session.commit()

        # Create connection A -> B
        connection = Connection(
            workflow_id=sample_workflow.id,
            source_node_id=node_a.id,
            target_node_id=node_b.id,
            source_output='output',
            target_input='input',
        )
        db_session.add(connection)
        db_session.commit()

        # Should not have cycle
        assert validator.check_cyclic_dependency(sample_workflow.id)

    def test_validate_workflow_empty(self, db_session: Session, sample_workflow: Workflow):
        """Test validating an empty workflow."""
        validator = WorkflowValidator(db_session)

        result = validator.validate_workflow(sample_workflow.id)
        assert not result.is_valid
        assert any('at least one node' in error.lower() for error in result.errors)


class TestWorkflowSerializer:
    """Test workflow serializer."""

    def test_serialize_workflow(self, db_session: Session, sample_workflow: Workflow):
        """Test serializing a workflow."""
        serializer = WorkflowSerializer(db_session)

        # Add a node
        node = Node(
            workflow_id=sample_workflow.id,
            type='LLM',
            name='Test Node',
            config={'model': 'gpt-4', 'prompt': 'test'},
            position={'x': 100, 'y': 200},
        )
        db_session.add(node)
        db_session.commit()

        # Serialize
        data = serializer.serialize_workflow(sample_workflow.id)

        assert data['version'] == '1.0'
        assert data['workflow']['name'] == 'Test Workflow'
        assert len(data['nodes']) == 1
        assert data['nodes'][0]['name'] == 'Test Node'

    def test_serialize_nonexistent_workflow(self, db_session: Session):
        """Test serializing a non-existent workflow."""
        serializer = WorkflowSerializer(db_session)

        with pytest.raises(SerializationError):
            serializer.serialize_workflow(uuid4())

    def test_deserialize_workflow(self, db_session: Session):
        """Test deserializing a workflow."""
        serializer = WorkflowSerializer(db_session)

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

    def test_deserialize_invalid_version(self, db_session: Session):
        """Test deserializing with invalid version."""
        serializer = WorkflowSerializer(db_session)

        workflow_data = {
            'version': '2.0',  # Unsupported version
            'workflow': {'name': 'Test'},
            'nodes': [],
            'connections': [],
        }

        with pytest.raises(DeserializationError):
            serializer.deserialize_workflow(workflow_data, uuid4(), uuid4())

    def test_validate_serialized_workflow_valid(self, db_session: Session):
        """Test validating valid serialized workflow data."""
        serializer = WorkflowSerializer(db_session)

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

    def test_validate_serialized_workflow_invalid(self, db_session: Session):
        """Test validating invalid serialized workflow data."""
        serializer = WorkflowSerializer(db_session)

        # Missing 'nodes' key
        workflow_data = {
            'version': '1.0',
            'workflow': {'name': 'Test'},
            'connections': [],
        }

        assert not serializer.validate_serialized_workflow(workflow_data)

    def test_round_trip_serialization(self, db_session: Session, sample_workflow: Workflow):
        """Test round-trip serialization and deserialization."""
        serializer = WorkflowSerializer(db_session)

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
        db_session.add(node_a)
        db_session.add(node_b)
        db_session.commit()

        connection = Connection(
            workflow_id=sample_workflow.id,
            source_node_id=node_a.id,
            target_node_id=node_b.id,
            source_output='output',
            target_input='input',
        )
        db_session.add(connection)
        db_session.commit()

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
        from sqlmodel import select

        nodes_statement = select(Node).where(Node.workflow_id == new_workflow.id)
        nodes = db_session.exec(nodes_statement).all()
        assert len(nodes) == 2

        # Check connections were created
        connections_statement = select(Connection).where(Connection.workflow_id == new_workflow.id)
        connections = db_session.exec(connections_statement).all()
        assert len(connections) == 1
