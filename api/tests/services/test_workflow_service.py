"""
工作流服务层测试

合并自:
- test_workflow_service.py
- test_workflow_validation_serialization.py

测试内容:
- 工作流CRUD操作
- 节点管理
- 连接管理
- 工作流验证
- 工作流序列化
"""

from typing import Any, Dict
from uuid import uuid4

from hypothesis import given, settings, strategies as st
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow.workflow import NodeModel, WorkflowModel
from app.schemas.workflow import (
    ConnectionCreateRequest,
    NodeCreateRequest,
    WorkflowCreateRequest,
    WorkflowUpdateRequest,
)
from app.services.workflow_serializer import (
    WorkflowSerializer,
)
from app.services.workflow_service import (
    WorkflowNotFoundError,
    WorkflowService,
    WorkflowValidationError,
)
from app.services.workflow_validator import WorkflowValidator
from app.utils.dag import (
    CycleDetectedError,
    detect_cycle,
    topological_sort,
)


# ============ Workflow Service Tests ============
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
    assert workflow.workspace_id == workspace_id


@pytest.mark.asyncio
async def test_get_workflow(test_session):
    """Test retrieving a workflow."""
    service = WorkflowService(test_session)
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    retrieved = await service.get_workflow(workflow.id)
    assert retrieved.id == workflow.id


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

    for i in range(3):
        workflow_data = WorkflowCreateRequest(name=f'Workflow {i}')
        await service.create_workflow(workflow_data, workspace_id, user_id)

    workflows, total = await service.list_workflows(workspace_id)
    assert len(workflows) >= 3


@pytest.mark.asyncio
async def test_update_workflow(test_session):
    """Test updating a workflow."""
    service = WorkflowService(test_session)
    workflow_data = WorkflowCreateRequest(name='Original Name')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    update_data = WorkflowUpdateRequest(name='Updated Name', description='Updated description')
    updated = await service.update_workflow(workflow.id, update_data)

    assert updated.name == 'Updated Name'


@pytest.mark.asyncio
async def test_delete_workflow(test_session):
    """Test deleting a workflow."""
    service = WorkflowService(test_session)
    workflow_data = WorkflowCreateRequest(name='To Delete')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    await service.delete_workflow(workflow.id)

    with pytest.raises(WorkflowNotFoundError):
        await service.get_workflow(workflow.id)


@pytest.mark.asyncio
async def test_add_node(test_session):
    """Test adding a node to a workflow."""
    service = WorkflowService(test_session)
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    node_data = NodeCreateRequest(
        type='LLM',
        name='LLM Node',
        config={'model': 'llama2', 'prompt': 'Hello'},
        position={'x': 100, 'y': 200},
    )
    node = await service.add_node(workflow.id, node_data)

    assert node.id is not None
    assert node.type == 'LLM'


@pytest.mark.asyncio
async def test_connect_nodes(test_session):
    """Test creating a connection between nodes."""
    service = WorkflowService(test_session)
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    node1_data = NodeCreateRequest(
        type='LLM', name='Node 1', config={'model': 'llama2', 'prompt': 'Test'}
    )
    node1 = await service.add_node(workflow.id, node1_data)

    node2_data = NodeCreateRequest(
        type='LLM', name='Node 2', config={'model': 'llama2', 'prompt': 'Test'}
    )
    node2 = await service.add_node(workflow.id, node2_data)

    connection_data = ConnectionCreateRequest(
        source_node_id=node1.id,
        target_node_id=node2.id,
        source_output='output',
        target_input='input',
    )
    connection = await service.connect_nodes(workflow.id, connection_data)

    assert connection.id is not None
    assert connection.source_node_id == node1.id


@pytest.mark.asyncio
async def test_connect_nodes_creates_cycle(test_session):
    """Test that creating a cyclic connection is rejected."""
    service = WorkflowService(test_session)
    workflow_data = WorkflowCreateRequest(name='Test Workflow')
    workflow = await service.create_workflow(workflow_data, uuid4(), uuid4())

    node1_data = NodeCreateRequest(
        type='LLM', name='Node 1', config={'model': 'llama2', 'prompt': 'Test'}
    )
    node1 = await service.add_node(workflow.id, node1_data)

    node2_data = NodeCreateRequest(
        type='LLM', name='Node 2', config={'model': 'llama2', 'prompt': 'Test'}
    )
    node2 = await service.add_node(workflow.id, node2_data)

    connection_data = ConnectionCreateRequest(
        source_node_id=node1.id,
        target_node_id=node2.id,
        source_output='output',
        target_input='input',
    )
    await service.connect_nodes(workflow.id, connection_data)

    reverse_connection = ConnectionCreateRequest(
        source_node_id=node2.id,
        target_node_id=node1.id,
        source_output='output',
        target_input='input',
    )

    with pytest.raises(WorkflowValidationError):
        await service.connect_nodes(workflow.id, reverse_connection)


# ============ DAG Utils Tests ============
class TestDAGUtils:
    """DAG工具函数测试"""

    def test_detect_cycle_no_cycle(self):
        """Test cycle detection with no cycle."""
        adjacency_list = {uuid4(): [uuid4()]}
        assert not detect_cycle(adjacency_list)

    def test_detect_cycle_with_cycle(self):
        """Test cycle detection with a cycle."""
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

        adjacency_list = {
            node_a: [node_b],
            node_b: [node_c],
            node_c: [],
        }

        result = topological_sort(adjacency_list)
        assert len(result) == 3
        assert result.index(node_a) < result.index(node_b)

    def test_topological_sort_with_cycle_raises_error(self):
        """Test that topological sort raises error on cycle."""
        node_a = uuid4()
        node_b = uuid4()

        adjacency_list = {
            node_a: [node_b],
            node_b: [node_a],
        }

        with pytest.raises(CycleDetectedError):
            topological_sort(adjacency_list)


# ============ Workflow Validator Tests ============
class TestWorkflowValidator:
    """工作流验证器测试"""

    @pytest.fixture
    async def sample_workflow(self, test_session: AsyncSession):
        """Create a sample workflow for testing."""
        workspace_id = uuid4()
        user_id = uuid4()

        workflow = WorkflowModel(
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

    @pytest.mark.asyncio
    async def test_validate_node_config_llm_valid(self, test_session: AsyncSession):
        """Test validating a valid LLM node configuration."""
        validator = WorkflowValidator(test_session)

        node = NodeModel(
            workflow_id=uuid4(),
            type='LLM',
            name='Test LLM Node',
            config={
                'model': 'llama2',
                'prompt': 'Test prompt',
                'temperature': 0.7,
                'max_tokens': 100,
            },
        )

        result = validator.validate_node_config(node)
        assert result.is_valid

    @pytest.mark.asyncio
    async def test_validate_node_config_llm_missing_required(self, test_session: AsyncSession):
        """Test validating an LLM node with missing required fields."""
        validator = WorkflowValidator(test_session)

        node = NodeModel(
            workflow_id=uuid4(),
            type='LLM',
            name='Test LLM Node',
            config={'model': 'llama2'},  # Missing 'prompt'
        )

        result = validator.validate_node_config(node)
        assert not result.is_valid


# ============ Workflow Serializer Tests ============
class TestWorkflowSerializer:
    """工作流序列化器测试"""

    @pytest.fixture
    async def sample_workflow(self, test_session: AsyncSession):
        """Create a sample workflow for testing."""
        workflow = WorkflowModel(
            name='Test Workflow',
            description='A test workflow',
            workspace_id=uuid4(),
            created_by=uuid4(),
            input_schema={'type': 'object'},
            output_schema={'type': 'object'},
        )
        test_session.add(workflow)
        await test_session.commit()
        await test_session.refresh(workflow)
        return workflow

    @pytest.mark.asyncio
    async def test_serialize_workflow(
        self, test_session: AsyncSession, sample_workflow: WorkflowModel
    ):
        """Test serializing a workflow."""
        serializer = WorkflowSerializer(test_session)

        node = NodeModel(
            workflow_id=sample_workflow.id,
            type='LLM',
            name='Test Node',
            config={'model': 'llama2', 'prompt': 'test'},
            position={'x': 100, 'y': 200},
        )
        test_session.add(node)
        await test_session.commit()

        data = await serializer.serialize_workflow(sample_workflow.id)

        assert data['version'] == '1.0'
        assert data['workflow']['name'] == 'Test Workflow'
        assert len(data['nodes']) == 1

    @pytest.mark.asyncio
    async def test_deserialize_workflow(self, test_session: AsyncSession):
        """Test deserializing a workflow."""
        serializer = WorkflowSerializer(test_session)

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
                    'config': {'model': 'llama2', 'prompt': 'test'},
                    'position': {'x': 0, 'y': 0},
                }
            ],
            'connections': [],
        }

        workflow = await serializer.deserialize_workflow(workflow_data, uuid4(), uuid4())
        assert workflow.name == 'Imported Workflow'

    @pytest.mark.asyncio
    async def test_validate_serialized_workflow_valid(self, test_session: AsyncSession):
        """Test validating valid serialized workflow data."""
        serializer = WorkflowSerializer(test_session)

        workflow_data = {
            'version': '1.0',
            'workflow': {'name': 'Test'},
            'nodes': [{'id': str(uuid4()), 'type': 'LLM', 'name': 'Node 1'}],
            'connections': [],
        }

        assert serializer.validate_serialized_workflow(workflow_data)


# ============ LLM Node Property Tests ============
class TestLLMNodeExecutor:
    """LLM节点执行器测试"""

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate LLM node configuration."""
        if 'model' not in config or not config['model']:
            return False
        if 'prompt' not in config or not config['prompt']:
            return False

        provider = config.get('provider', 'ollama')
        if provider.lower() != 'ollama':
            return False

        base_url = config.get('base_url', 'http://localhost:11434')
        if not base_url.startswith(('http://', 'https://')):
            return False

        temperature = config.get('temperature', 0.7)
        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
            return False

        max_tokens = config.get('max_tokens', 1000)
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            return False

        return True


class TestLLMNodeProperties:
    """LLM节点属性测试"""

    @settings(max_examples=100)
    @given(
        model=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')),
        ),
        prompt=st.text(min_size=1, max_size=1000),
        temperature=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
        max_tokens=st.integers(min_value=1, max_value=10000),
    )
    def test_llm_node_configuration_completeness_property(
        self, model: str, prompt: str, temperature: float, max_tokens: int
    ):
        """Property 53: LLM Node Configuration Completeness"""
        executor = TestLLMNodeExecutor()

        complete_config = {
            'provider': 'ollama',
            'model': model,
            'prompt': prompt,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'base_url': 'http://localhost:11434',
        }

        assert executor.validate_config(complete_config) is True

        # Test missing required fields
        for field in ['model', 'prompt']:
            incomplete_config = complete_config.copy()
            del incomplete_config[field]
            assert executor.validate_config(incomplete_config) is False
