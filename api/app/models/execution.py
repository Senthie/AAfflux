"""Execution record and result data models."""

from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4


class ExecutionRecord(SQLModel, table=True):
    """Execution record model for tracking workflow runs."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workflow_id: UUID = Field(foreign_key="workflow.id", index=True)
    inputs: dict = Field(default_factory=dict, sa_column=Column(JSON))
    outputs: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    status: str  # PENDING, RUNNING, SUCCESS, FAILED
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # Relationships
    node_results: List["NodeExecutionResult"] = Relationship(back_populates="execution_record")


class NodeExecutionResult(SQLModel, table=True):
    """Node execution result model for tracking individual node performance."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    execution_record_id: UUID = Field(foreign_key="executionrecord.id", index=True)
    node_id: UUID = Field(foreign_key="node.id")
    status: str
    inputs: dict = Field(default_factory=dict, sa_column=Column(JSON))
    outputs: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    error: Optional[str] = None
    duration_ms: int

    # Relationships
    execution_record: Optional[ExecutionRecord] = Relationship(back_populates="node_results")
