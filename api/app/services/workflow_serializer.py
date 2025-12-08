"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-04 09:40:36
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-04 09:42:29
FilePath: /api/app/services/workflow_serializer.py
Description:
    工作流序列化服务。

    该模块为工作流提供序列化和反序列化功能，
    实现数据库模型与JSON表示形式之间的转换

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Any, Dict
from uuid import UUID

from sqlmodel import Session, select

from app.models.workflow.workflow import Connection, Node, Workflow


class SerializationError(Exception):
    """Exception raised when serialization fails."""

    pass


class DeserializationError(Exception):
    """Exception raised when deserialization fails."""

    pass


class WorkflowSerializer:
    """Service for serializing and deserializing workflows."""

    # Current serialization format version
    FORMAT_VERSION = '1.0'

    def __init__(self, db: Session):
        """Initialize workflow serializer.

        Args:
            db: Database session
        """
        self.db = db

    def serialize_workflow(self, workflow_id: UUID) -> Dict[str, Any]:
        """Serialize a workflow to JSON format.

        Args:
            workflow_id: ID of the workflow to serialize

        Returns:
            Dictionary containing the complete workflow definition

        Raises:
            SerializationError: If workflow cannot be serialized
        """
        # Get workflow
        workflow = self.db.get(Workflow, workflow_id)
        if not workflow:
            raise SerializationError(f'Workflow {workflow_id} not found')

        # Get all nodes
        nodes_statement = select(Node).where(Node.workflow_id == workflow_id)
        nodes = self.db.exec(nodes_statement).all()

        # Get all connections
        connections_statement = select(Connection).where(Connection.workflow_id == workflow_id)
        connections = self.db.exec(connections_statement).all()

        # Build JSON structure
        workflow_data = {
            'version': self.FORMAT_VERSION,
            'workflow': {
                'id': str(workflow.id),
                'name': workflow.name,
                'description': workflow.description,
                'workspace_id': str(workflow.workspace_id),
                'input_schema': workflow.input_schema,
                'output_schema': workflow.output_schema,
                'created_at': workflow.created_at.isoformat() if workflow.created_at else None,
                'updated_at': workflow.updated_at.isoformat() if workflow.updated_at else None,
                'created_by': str(workflow.created_by),
            },
            'nodes': [self._serialize_node(node) for node in nodes],
            'connections': [self._serialize_connection(conn) for conn in connections],
        }

        return workflow_data

    def _serialize_node(self, node: Node) -> Dict[str, Any]:
        """Serialize a single node.

        Args:
            node: Node to serialize

        Returns:
            Dictionary containing node data
        """
        return {
            'id': str(node.id),
            'workflow_id': str(node.workflow_id),
            'type': node.type,
            'name': node.name,
            'config': node.config,
            'position': node.position,
        }

    def _serialize_connection(self, connection: Connection) -> Dict[str, Any]:
        """Serialize a single connection.

        Args:
            connection: Connection to serialize

        Returns:
            Dictionary containing connection data
        """
        return {
            'id': str(connection.id),
            'workflow_id': str(connection.workflow_id),
            'source_node_id': str(connection.source_node_id),
            'target_node_id': str(connection.target_node_id),
            'source_output': connection.source_output,
            'target_input': connection.target_input,
        }

    def deserialize_workflow(
        self, workflow_data: Dict[str, Any], workspace_id: UUID, created_by: UUID
    ) -> Workflow:
        """Deserialize a workflow from JSON format.

        Args:
            workflow_data: Dictionary containing workflow definition
            workspace_id: ID of the workspace to create workflow in
            created_by: ID of the user creating the workflow

        Returns:
            Created Workflow object

        Raises:
            DeserializationError: If workflow data is invalid
        """
        # Validate format version
        version = workflow_data.get('version')
        if not version:
            raise DeserializationError('Missing format version')

        if version != self.FORMAT_VERSION:
            # In the future, we might support migration from older versions
            raise DeserializationError(
                f'Unsupported format version: {version}. Expected: {self.FORMAT_VERSION}'
            )

        # Validate structure
        if 'workflow' not in workflow_data:
            raise DeserializationError("Missing 'workflow' key")
        if 'nodes' not in workflow_data:
            raise DeserializationError("Missing 'nodes' key")
        if 'connections' not in workflow_data:
            raise DeserializationError("Missing 'connections' key")

        workflow_info = workflow_data['workflow']

        # Validate required workflow fields
        required_fields = ['name']
        for field in required_fields:
            if field not in workflow_info:
                raise DeserializationError(f'Missing required workflow field: {field}')

        # Create workflow
        workflow = Workflow(
            name=workflow_info['name'],
            description=workflow_info.get('description'),
            workspace_id=workspace_id,
            input_schema=workflow_info.get('input_schema', {}),
            output_schema=workflow_info.get('output_schema', {}),
            created_by=created_by,
        )

        self.db.add(workflow)
        self.db.flush()  # Get the workflow ID without committing

        # Map old node IDs to new node IDs
        node_id_map: Dict[str, UUID] = {}

        # Create nodes
        for node_data in workflow_data['nodes']:
            try:
                node = self._deserialize_node(node_data, workflow.id)
                self.db.add(node)
                self.db.flush()

                # Store mapping
                old_id = node_data.get('id')
                if old_id:
                    node_id_map[old_id] = node.id
            except Exception as e:
                raise DeserializationError(f'Failed to deserialize node: {str(e)}') from e

        # Create connections
        for conn_data in workflow_data['connections']:
            try:
                connection = self._deserialize_connection(conn_data, workflow.id, node_id_map)
                self.db.add(connection)
            except Exception as e:
                raise DeserializationError(f'Failed to deserialize connection: {str(e)}') from e

        # Commit all changes
        self.db.commit()
        self.db.refresh(workflow)

        return workflow

    def _deserialize_node(self, node_data: Dict[str, Any], workflow_id: UUID) -> Node:
        """Deserialize a single node.

        Args:
            node_data: Dictionary containing node data
            workflow_id: ID of the workflow this node belongs to

        Returns:
            Created Node object

        Raises:
            DeserializationError: If node data is invalid
        """
        # Validate required fields
        required_fields = ['type', 'name']
        for field in required_fields:
            if field not in node_data:
                raise DeserializationError(f'Missing required node field: {field}')

        # Create node
        node = Node(
            workflow_id=workflow_id,
            type=node_data['type'],
            name=node_data['name'],
            config=node_data.get('config', {}),
            position=node_data.get('position', {}),
        )

        return node

    def _deserialize_connection(
        self,
        conn_data: Dict[str, Any],
        workflow_id: UUID,
        node_id_map: Dict[str, UUID],
    ) -> Connection:
        """Deserialize a single connection.

        Args:
            conn_data: Dictionary containing connection data
            workflow_id: ID of the workflow this connection belongs to
            node_id_map: Mapping from old node IDs to new node IDs

        Returns:
            Created Connection object

        Raises:
            DeserializationError: If connection data is invalid
        """
        # Validate required fields
        required_fields = [
            'source_node_id',
            'target_node_id',
            'source_output',
            'target_input',
        ]
        for field in required_fields:
            if field not in conn_data:
                raise DeserializationError(f'Missing required connection field: {field}')

        # Map old node IDs to new node IDs
        source_node_id_str = conn_data['source_node_id']
        target_node_id_str = conn_data['target_node_id']

        if source_node_id_str not in node_id_map:
            raise DeserializationError(f'Source node ID not found in mapping: {source_node_id_str}')
        if target_node_id_str not in node_id_map:
            raise DeserializationError(f'Target node ID not found in mapping: {target_node_id_str}')

        source_node_id = node_id_map[source_node_id_str]
        target_node_id = node_id_map[target_node_id_str]

        # Create connection
        connection = Connection(
            workflow_id=workflow_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            source_output=conn_data['source_output'],
            target_input=conn_data['target_input'],
        )

        return connection

    def validate_serialized_workflow(self, workflow_data: Dict[str, Any]) -> bool:
        """Validate the structure and completeness of serialized workflow data.

        Args:
            workflow_data: Dictionary containing workflow definition

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check version
            if 'version' not in workflow_data:
                return False

            # Check required top-level keys
            required_keys = ['workflow', 'nodes', 'connections']
            for key in required_keys:
                if key not in workflow_data:
                    return False

            # Check workflow data
            workflow_info = workflow_data['workflow']
            if not isinstance(workflow_info, dict):
                return False
            if 'name' not in workflow_info:
                return False

            # Check nodes
            nodes = workflow_data['nodes']
            if not isinstance(nodes, list):
                return False

            node_ids = set()
            for node in nodes:
                if not isinstance(node, dict):
                    return False
                if 'id' not in node or 'type' not in node or 'name' not in node:
                    return False
                node_ids.add(node['id'])

            # Check connections
            connections = workflow_data['connections']
            if not isinstance(connections, list):
                return False

            for conn in connections:
                if not isinstance(conn, dict):
                    return False
                required_conn_fields = [
                    'source_node_id',
                    'target_node_id',
                    'source_output',
                    'target_input',
                ]
                for field in required_conn_fields:
                    if field not in conn:
                        return False

                # Check that referenced nodes exist
                if conn['source_node_id'] not in node_ids:
                    return False
                if conn['target_node_id'] not in node_ids:
                    return False

            return True

        except Exception:
            return False

    def export_workflow_to_json(self, workflow_id: UUID) -> str:
        """Export a workflow to JSON string.

        Args:
            workflow_id: ID of the workflow to export

        Returns:
            JSON string representation of the workflow

        Raises:
            SerializationError: If workflow cannot be serialized
        """
        import json

        workflow_data = self.serialize_workflow(workflow_id)
        return json.dumps(workflow_data, indent=2, ensure_ascii=False)

    def import_workflow_from_json(
        self, json_str: str, workspace_id: UUID, created_by: UUID
    ) -> Workflow:
        """Import a workflow from JSON string.

        Args:
            json_str: JSON string containing workflow definition
            workspace_id: ID of the workspace to create workflow in
            created_by: ID of the user creating the workflow

        Returns:
            Created Workflow object

        Raises:
            DeserializationError: If JSON is invalid or workflow data is invalid
        """
        import json

        try:
            workflow_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise DeserializationError(f'Invalid JSON: {str(e)}') from e

        return self.deserialize_workflow(workflow_data, workspace_id, created_by)
