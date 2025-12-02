"""Workflow and node related data models."""

from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4


class Workflow(SQLModel, table=True):
    """Workflow model for defining AI processing pipelines."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    workspace_id: UUID = Field(foreign_key="workspace.id", index=True)
    description: Optional[str] = None
    input_schema: dict = Field(default_factory=dict, sa_column=Column(JSON))
    output_schema: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    nodes: List["Node"] = Relationship(back_populates="workflow")
    connections: List["Connection"] = Relationship(back_populates="workflow")


class Node(SQLModel, table=True):
    """Node model representing individual processing units in workflows."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workflow_id: UUID = Field(foreign_key="workflow.id", index=True)
    type: str  # LLM, CONDITION, CODE, HTTP, TRANSFORM
    name: str
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    position: dict = Field(default_factory=dict, sa_column=Column(JSON))  # x, y coordinates

    # Relationships
    workflow: Optional[Workflow] = Relationship(back_populates="nodes")


class Connection(SQLModel, table=True):
    """Connection model representing data flow between nodes."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workflow_id: UUID = Field(foreign_key="workflow.id", index=True)
    source_node_id: UUID = Field(foreign_key="node.id")
    target_node_id: UUID = Field(foreign_key="node.id")
    source_output: str
    target_input: str

    # Relationships
    workflow: Optional[Workflow] = Relationship(back_populates="connections")
