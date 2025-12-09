"""
Tests for workflow service functionality.

This module tests the workflow management service including CRUD operations
for workflows, nodes, and connections.
"""

from uuid import uuid4

import pytest

from app.schemas.workflow import (
    ConnectionCreateRequest,
    NodeCreateRequest,
    WorkflowCreateRequest,
)
from app.services.workflow_service import (
    NodeNotFoundError,
    WorkflowNotFoundError,
    WorkflowService,
    WorkflowValidationError,
)


@pytest.mark.asyncio
async def test_create_workflow(test_session):
    """Test creating a new workflow."""
    service = WorkflowService(test_session)

    workflow_data = WorkflowCreateRequest(
        name='Test Workflow',
        description='A test workflow',
        input_schema={'type': 'object'},
        output_schema={'type': 'object'},
    )

    workspace_id = uuid4()
    user_id = uuid4()

    workflow = await service.create_workflow(workflow_data, workspace_id, user_id)

    assert workflow.id is not None
    assert workflow.name == 'Test Workflow'
    assert workflow.description == 'A test workflow'
    assert workflow.workspace_id == workspace_id
    assert workflow.created_by == user_id
    assert workflow.is_deleted is False


@pytest.mark.asyncio
async def test_get_workflow(test_session):
    """Test retrieving a workflow."""
    service = WorkflowService(test_session)

    # Create a workflow
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    # Retrieve it
    retrieved = await service.get_workflow(workflow.id)

    assert retrieved.id == workflow.id
    assert retrieved.name == workflow.name


@pytest.mark.asyncio
async def test_get_nonexistent_workflow(test_session):
    """Test retrieving a non-existent workflow raises error."""
    service = WorkflowService(test_session)

    with pytest.raises(WorkflowNotFoundError):
        await service.get_workflow(uuid4())


@pytest.mark.asyncio
async def test_list_workflows(test_session):
    """Test listing workflows in a workspace."""
    service = WorkflowService(test_session)

    workspace_id = uuid4()
    user_id = uuid4()

    # Create multiple workflows
    for i in range(3):
        workflow_data = WorkflowCreateRequest(name=f'Workflow {i}')
        await service.create_workflow(workflow_data, workspace_id, user_id)

    # List workflows
    workflows, total = await service.list_workflows(workspace_id)

    assert len(workflows) >= 3
    assert total >= 3


@pytest.mark.asyncio
async def test_update_workflow(test_session):
    """Test updating a workflow."""
    service = WorkflowService(test_session)

    # Create a workflow
    workflow_data = WorkflowCreateRequest(name='Original Name')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    # Update it
    from app.schemas.workflow import WorkflowUpdateRequest

    update_data = WorkflowUpdateRequest(name='Updated Name', description='Updated description')
    updated = await service.update_workflow(workflow.id, update_data)

    assert updated.name == 'Updated Name'
    assert updated.description == 'Updated description'


@pytest.mark.asyncio
async def test_delete_workflow(test_session):
    """Test deleting a workflow."""
    service = WorkflowService(test_session)

    # Create a workflow
    workflow_data = WorkflowCreateRequest(name='To Delete')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    # Delete it
    await service.delete_workflow(workflow.id)

    # Verify it's deleted
    with pytest.raises(WorkflowNotFoundError):
        await service.get_workflow(workflow.id)


@pytest.mark.asyncio
async def test_add_node(test_session):
    """Test adding a node to a workflow."""
    service = WorkflowService(test_session)

    # Create a workflow
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    # Add a node
    node_data = NodeCreateRequest(
        type='LLM',
        name='LLM Node',
        config={'model': 'gpt-4', 'prompt': 'Hello'},
        position={'x': 100, 'y': 200},
    )
    node = await service.add_node(workflow.id, node_data)

    assert node.id is not None
    assert node.workflow_id == workflow.id
    assert node.type == 'LLM'
    assert node.name == 'LLM Node'
    assert node.config['model'] == 'gpt-4'


@pytest.mark.asyncio
async def test_add_node_with_invalid_config(test_session):
    """Test adding a node with invalid configuration raises error."""
    service = WorkflowService(test_session)

    # Create a workflow
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    # Try to add a node with missing required fields
    node_data = NodeCreateRequest(
        type='LLM',
        name='Invalid Node',
        config={},  # Missing required 'model' and 'prompt'
    )

    with pytest.raises(WorkflowValidationError):
        await service.add_node(workflow.id, node_data)


@pytest.mark.asyncio
async def test_list_nodes(test_session):
    """Test listing nodes in a workflow."""
    service = WorkflowService(test_session)

    # Create a workflow
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    # Add multiple nodes
    for i in range(3):
        node_data = NodeCreateRequest(
            type='LLM',
            name=f'Node {i}',
            config={'model': 'gpt-4', 'prompt': f'Prompt {i}'},
        )
        await service.add_node(workflow.id, node_data)

    # List nodes
    nodes = await service.list_nodes(workflow.id)

    assert len(nodes) == 3


@pytest.mark.asyncio
async def test_update_node(test_session):
    """Test updating a node."""
    service = WorkflowService(test_session)

    # Create a workflow and node
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    node_data = NodeCreateRequest(
        type='LLM',
        name='Original Node',
        config={'model': 'gpt-4', 'prompt': 'Original'},
    )
    node = await service.add_node(workflow.id, node_data)

    # Update the node
    from app.schemas.workflow import NodeUpdateRequest

    update_data = NodeUpdateRequest(
        name='Updated Node', config={'model': 'gpt-4', 'prompt': 'Updated'}
    )
    updated = await service.update_node(node.id, update_data)

    assert updated.name == 'Updated Node'
    assert updated.config['prompt'] == 'Updated'


@pytest.mark.asyncio
async def test_delete_node(test_session):
    """Test deleting a node."""
    service = WorkflowService(test_session)

    # Create a workflow and node
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    node_data = NodeCreateRequest(
        type='LLM', name='To Delete', config={'model': 'gpt-4', 'prompt': 'Test'}
    )
    node = await service.add_node(workflow.id, node_data)

    # Delete the node
    await service.delete_node(node.id)

    # Verify it's deleted
    with pytest.raises(NodeNotFoundError):
        await service.get_node(node.id)


@pytest.mark.asyncio
async def test_connect_nodes(test_session):
    """Test creating a connection between nodes."""
    service = WorkflowService(test_session)

    # Create a workflow
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    # Add two nodes
    node1_data = NodeCreateRequest(
        type='LLM', name='Node 1', config={'model': 'gpt-4', 'prompt': 'Test'}
    )
    node1 = await service.add_node(workflow.id, node1_data)

    node2_data = NodeCreateRequest(
        type='LLM', name='Node 2', config={'model': 'gpt-4', 'prompt': 'Test'}
    )
    node2 = await service.add_node(workflow.id, node2_data)

    # Connect them
    connection_data = ConnectionCreateRequest(
        source_node_id=node1.id,
        target_node_id=node2.id,
        source_output='output',
        target_input='input',
    )
    connection = await service.connect_nodes(workflow.id, connection_data)

    assert connection.id is not None
    assert connection.workflow_id == workflow.id
    assert connection.source_node_id == node1.id
    assert connection.target_node_id == node2.id


@pytest.mark.asyncio
async def test_connect_nodes_creates_cycle(test_session):
    """Test that creating a cyclic connection is rejected."""
    service = WorkflowService(test_session)

    # Create a workflow
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    # Add two nodes
    node1_data = NodeCreateRequest(
        type='LLM', name='Node 1', config={'model': 'gpt-4', 'prompt': 'Test'}
    )
    node1 = await service.add_node(workflow.id, node1_data)

    node2_data = NodeCreateRequest(
        type='LLM', name='Node 2', config={'model': 'gpt-4', 'prompt': 'Test'}
    )
    node2 = await service.add_node(workflow.id, node2_data)

    # Connect node1 -> node2
    connection_data = ConnectionCreateRequest(
        source_node_id=node1.id,
        target_node_id=node2.id,
        source_output='output',
        target_input='input',
    )
    await service.connect_nodes(workflow.id, connection_data)

    # Try to connect node2 -> node1 (creates cycle)
    reverse_connection = ConnectionCreateRequest(
        source_node_id=node2.id,
        target_node_id=node1.id,
        source_output='output',
        target_input='input',
    )

    with pytest.raises(WorkflowValidationError):
        await service.connect_nodes(workflow.id, reverse_connection)


@pytest.mark.asyncio
async def test_list_connections(test_session):
    """Test listing connections in a workflow."""
    service = WorkflowService(test_session)

    # Create a workflow
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    # Add nodes
    nodes = []
    for i in range(3):
        node_data = NodeCreateRequest(
            type='LLM', name=f'Node {i}', config={'model': 'gpt-4', 'prompt': 'Test'}
        )
        node = await service.add_node(workflow.id, node_data)
        nodes.append(node)

    # Connect them in sequence
    for i in range(len(nodes) - 1):
        connection_data = ConnectionCreateRequest(
            source_node_id=nodes[i].id,
            target_node_id=nodes[i + 1].id,
            source_output='output',
            target_input='input',
        )
        await service.connect_nodes(workflow.id, connection_data)

    # List connections
    connections = await service.list_connections(workflow.id)

    assert len(connections) == 2


@pytest.mark.asyncio
async def test_delete_connection(test_session):
    """Test deleting a connection."""
    service = WorkflowService(test_session)

    # Create a workflow
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    # Add two nodes
    node1_data = NodeCreateRequest(
        type='LLM', name='Node 1', config={'model': 'gpt-4', 'prompt': 'Test'}
    )
    node1 = await service.add_node(workflow.id, node1_data)

    node2_data = NodeCreateRequest(
        type='LLM', name='Node 2', config={'model': 'gpt-4', 'prompt': 'Test'}
    )
    node2 = await service.add_node(workflow.id, node2_data)

    # Connect them
    connection_data = ConnectionCreateRequest(
        source_node_id=node1.id,
        target_node_id=node2.id,
        source_output='output',
        target_input='input',
    )
    connection = await service.connect_nodes(workflow.id, connection_data)

    # Delete the connection
    await service.delete_connection(connection.id)

    # Verify it's deleted
    connections = await service.list_connections(workflow.id)
    assert len(connections) == 0


@pytest.mark.asyncio
async def test_validate_workflow(test_session):
    """Test workflow validation."""
    service = WorkflowService(test_session)

    # Create a workflow
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    # Add a valid node
    node_data = NodeCreateRequest(
        type='LLM', name='Node 1', config={'model': 'gpt-4', 'prompt': 'Test'}
    )
    await service.add_node(workflow.id, node_data)

    # Validate
    result = await service.validate_workflow(workflow.id)

    assert result.is_valid is True
    assert len(result.errors) == 0
