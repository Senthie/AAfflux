"""
Workflow-related Pydantic schemas for request/response validation.

This module defines the data transfer objects (DTOs) for workflow management,
including schemas for workflows, nodes, and connections.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Node Schemas
# ============================================================================


class NodeConfigBase(BaseModel):
    """Base configuration for all node types."""

    pass


class LLMNodeConfig(NodeConfigBase):
    """Configuration for LLM nodes."""

    model: str = Field(..., description='LLM model name')
    prompt: str = Field(..., description='Prompt template')
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2, description='Temperature')
    max_tokens: Optional[int] = Field(default=1000, gt=0, description='Maximum tokens')


class ConditionNodeConfig(NodeConfigBase):
    """Configuration for condition nodes."""

    condition: str = Field(..., description='Condition expression')


class CodeNodeConfig(NodeConfigBase):
    """Configuration for code execution nodes."""

    code: str = Field(..., description='Python code to execute')


class HTTPNodeConfig(NodeConfigBase):
    """Configuration for HTTP request nodes."""

    url: str = Field(..., description='HTTP URL')
    method: str = Field(..., description='HTTP method (GET, POST, etc.)')
    headers: Optional[Dict[str, str]] = Field(default=None, description='HTTP headers')
    body: Optional[Dict[str, Any]] = Field(default=None, description='Request body')


class TransformNodeConfig(NodeConfigBase):
    """Configuration for data transformation nodes."""

    transformation: str = Field(..., description='Transformation expression')


class NodePositionSchema(BaseModel):
    """Schema for node position on canvas."""

    x: float = Field(..., description='X coordinate')
    y: float = Field(..., description='Y coordinate')


class NodeCreateRequest(BaseModel):
    """Request schema for creating a node."""

    type: str = Field(..., description='Node type (LLM, CONDITION, CODE, HTTP, TRANSFORM)')
    name: str = Field(..., min_length=1, max_length=255, description='Node name')
    config: Dict[str, Any] = Field(default_factory=dict, description='Node configuration')
    position: Dict[str, float] = Field(default_factory=dict, description='Node position (x, y)')

    @field_validator('type')
    @classmethod
    def validate_node_type(cls, v: str) -> str:
        """Validate node type."""
        valid_types = ['LLM', 'CONDITION', 'CODE', 'HTTP', 'TRANSFORM']
        if v not in valid_types:
            raise ValueError(f'Node type must be one of: {", ".join(valid_types)}')
        return v


class NodeUpdateRequest(BaseModel):
    """Request schema for updating a node."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description='Node name')
    config: Optional[Dict[str, Any]] = Field(None, description='Node configuration')
    position: Optional[Dict[str, float]] = Field(None, description='Node position (x, y)')


class NodeResponse(BaseModel):
    """Response schema for a node."""

    id: UUID
    workflow_id: UUID
    type: str
    name: str
    config: Dict[str, Any]
    position: Dict[str, float]
    is_deleted: bool = False

    model_config = {'from_attributes': True}


# ============================================================================
# Connection Schemas
# ============================================================================


class ConnectionCreateRequest(BaseModel):
    """Request schema for creating a connection."""

    source_node_id: UUID = Field(..., description='Source node ID')
    target_node_id: UUID = Field(..., description='Target node ID')
    source_output: str = Field(..., min_length=1, max_length=255, description='Source output port')
    target_input: str = Field(..., min_length=1, max_length=255, description='Target input port')


class ConnectionResponse(BaseModel):
    """Response schema for a connection."""

    id: UUID
    workflow_id: UUID
    source_node_id: UUID
    target_node_id: UUID
    source_output: str
    target_input: str

    model_config = {'from_attributes': True}


# ============================================================================
# Workflow Schemas
# ============================================================================


class WorkflowCreateRequest(BaseModel):
    """Request schema for creating a workflow."""

    name: str = Field(..., min_length=1, max_length=255, description='Workflow name')
    description: Optional[str] = Field(None, description='Workflow description')
    input_schema: Dict[str, Any] = Field(default_factory=dict, description='Input parameter schema')
    output_schema: Dict[str, Any] = Field(default_factory=dict, description='Output result schema')


class WorkflowUpdateRequest(BaseModel):
    """Request schema for updating a workflow."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description='Workflow name')
    description: Optional[str] = Field(None, description='Workflow description')
    input_schema: Optional[Dict[str, Any]] = Field(None, description='Input parameter schema')
    output_schema: Optional[Dict[str, Any]] = Field(None, description='Output result schema')


class WorkflowResponse(BaseModel):
    """Response schema for a workflow."""

    id: UUID
    name: str
    description: Optional[str]
    workspace_id: UUID
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    is_deleted: bool = False

    model_config = {'from_attributes': True}


class WorkflowDetailResponse(WorkflowResponse):
    """Detailed response schema for a workflow including nodes and connections."""

    nodes: List[NodeResponse] = Field(default_factory=list, description='Workflow nodes')
    connections: List[ConnectionResponse] = Field(
        default_factory=list, description='Node connections'
    )


class WorkflowListResponse(BaseModel):
    """Response schema for workflow list."""

    workflows: List[WorkflowResponse]
    total: int


class WorkflowDeleteResponse(BaseModel):
    """Response schema for workflow deletion."""

    success: bool
    message: str
    workflow_id: UUID


# ============================================================================
# Validation Schemas
# ============================================================================


class ValidationErrorDetail(BaseModel):
    """Schema for validation error details."""

    field: Optional[str] = None
    message: str


class ValidationResultResponse(BaseModel):
    """Response schema for validation results."""

    is_valid: bool
    errors: List[ValidationErrorDetail] = Field(default_factory=list)


# ============================================================================
# Serialization Schemas
# ============================================================================


class WorkflowExportResponse(BaseModel):
    """Response schema for workflow export."""

    version: str
    workflow: Dict[str, Any]
    nodes: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]


class WorkflowImportRequest(BaseModel):
    """Request schema for workflow import."""

    workflow_data: Dict[str, Any] = Field(..., description='Serialized workflow data')
