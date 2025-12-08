"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-04 09:50:20
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-05 09:55:13
FilePath: /api/app/services/workflow_validator.py
Description:Workflow validation service.

This module provides validation functionality for workflows, including:
- Workflow completeness checks
- Cycle dependency detection
- Node configuration validation

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Dict, List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.workflow.workflow import Connection, Node, Workflow
from app.utils.dag import build_adjacency_list, detect_cycle


class ValidationResult:
    """Result of a validation operation."""

    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None):
        """Initialize validation result.

        Args:
            is_valid: Whether the validation passed
            errors: List of error messages if validation failed
        """
        self.is_valid = is_valid
        self.errors = errors or []

    def add_error(self, error: str) -> None:
        """Add an error message.

        Args:
            error: Error message to add
        """
        self.is_valid = False
        self.errors.append(error)

    def __bool__(self) -> bool:
        """Return validation status."""
        return self.is_valid

    def __str__(self) -> str:
        """Return string representation."""
        if self.is_valid:
            return 'Validation passed'
        return f'Validation failed: {"; ".join(self.errors)}'


class WorkflowValidator:
    """Service for validating workflows."""

    # Required fields for different node types
    NODE_TYPE_REQUIRED_FIELDS = {
        'LLM': ['model', 'prompt'],
        'CONDITION': ['condition'],
        'CODE': ['code'],
        'HTTP': ['url', 'method'],
        'TRANSFORM': ['transformation'],
    }

    def __init__(self, db: Session):
        """Initialize workflow validator.

        Args:
            db: Database session
        """
        self.db = db

    def validate_workflow(self, workflow_id: UUID) -> ValidationResult:
        """Validate a complete workflow.

        Checks:
        - Workflow exists
        - Has at least one node
        - All nodes have valid configurations
        - No cyclic dependencies
        - All connections are valid

        Args:
            workflow_id: ID of the workflow to validate

        Returns:
            ValidationResult indicating if workflow is valid
        """
        result = ValidationResult(is_valid=True)

        # Check workflow exists
        workflow = self.db.get(Workflow, workflow_id)
        if not workflow:
            result.add_error(f'Workflow {workflow_id} not found')
            return result

        # Get all nodes for this workflow
        nodes_statement = select(Node).where(Node.workflow_id == workflow_id)
        nodes = self.db.exec(nodes_statement).all()

        if not nodes:
            result.add_error('Workflow must have at least one node')
            return result

        # Validate each node
        for node in nodes:
            node_result = self.validate_node_config(node)
            if not node_result.is_valid:
                for error in node_result.errors:
                    result.add_error(f'Node {node.name} ({node.id}): {error}')

        # Get all connections
        connections_statement = select(Connection).where(Connection.workflow_id == workflow_id)
        connections = self.db.exec(connections_statement).all()

        # Validate connections
        node_ids = {node.id for node in nodes}
        for connection in connections:
            if connection.source_node_id not in node_ids:
                result.add_error(
                    f'Connection references non-existent source node: {connection.source_node_id}'
                )
            if connection.target_node_id not in node_ids:
                result.add_error(
                    f'Connection references non-existent target node: {connection.target_node_id}'
                )

        # Check for cyclic dependencies
        if not self.check_cyclic_dependency(workflow_id):
            result.add_error('Workflow contains cyclic dependencies')

        return result

    def check_cyclic_dependency(self, workflow_id: UUID) -> bool:
        """Check if workflow has cyclic dependencies.

        Args:
            workflow_id: ID of the workflow to check

        Returns:
            True if no cycles detected, False if cycles exist
        """
        # Get all connections for this workflow
        connections_statement = select(Connection).where(Connection.workflow_id == workflow_id)
        connections = self.db.exec(connections_statement).all()

        # Build adjacency list
        connection_tuples = [(conn.source_node_id, conn.target_node_id) for conn in connections]
        adjacency_list = build_adjacency_list(connection_tuples)

        # Check for cycles
        has_cycle = detect_cycle(adjacency_list)

        return not has_cycle

    def validate_node_config(self, node: Node) -> ValidationResult:
        """Validate a node's configuration.

        Checks:
        - Node type is supported
        - Required fields are present
        - Configuration is well-formed

        Args:
            node: Node to validate

        Returns:
            ValidationResult indicating if node configuration is valid
        """
        result = ValidationResult(is_valid=True)

        # Check node type is supported
        if node.type not in self.NODE_TYPE_REQUIRED_FIELDS:
            result.add_error(f'Unsupported node type: {node.type}')
            return result

        # Check required fields are present
        required_fields = self.NODE_TYPE_REQUIRED_FIELDS[node.type]
        config = node.config or {}

        for field in required_fields:
            if field not in config:
                result.add_error(f'Missing required field: {field}')
            elif not config[field]:
                result.add_error(f'Required field is empty: {field}')

        # Type-specific validation
        if node.type == 'LLM':
            result = self._validate_llm_node(config, result)
        elif node.type == 'CONDITION':
            result = self._validate_condition_node(config, result)
        elif node.type == 'CODE':
            result = self._validate_code_node(config, result)
        elif node.type == 'HTTP':
            result = self._validate_http_node(config, result)
        elif node.type == 'TRANSFORM':
            result = self._validate_transform_node(config, result)

        return result

    def _validate_llm_node(self, config: Dict, result: ValidationResult) -> ValidationResult:
        """Validate LLM node configuration.

        Args:
            config: Node configuration
            result: Current validation result

        Returns:
            Updated validation result
        """
        # Check temperature is in valid range
        if 'temperature' in config:
            temp = config['temperature']
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                result.add_error('Temperature must be between 0 and 2')

        # Check max_tokens is positive
        if 'max_tokens' in config:
            max_tokens = config['max_tokens']
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                result.add_error('max_tokens must be a positive integer')

        return result

    def _validate_condition_node(self, config: Dict, result: ValidationResult) -> ValidationResult:
        """Validate condition node configuration.

        Args:
            config: Node configuration
            result: Current validation result

        Returns:
            Updated validation result
        """
        # Check condition is a non-empty string
        condition = config.get('condition', '')
        if not isinstance(condition, str) or not condition.strip():
            result.add_error('Condition must be a non-empty string')

        return result

    def _validate_code_node(self, config: Dict, result: ValidationResult) -> ValidationResult:
        """Validate code node configuration.

        Args:
            config: Node configuration
            result: Current validation result

        Returns:
            Updated validation result
        """
        # Check code is a non-empty string
        code = config.get('code', '')
        if not isinstance(code, str) or not code.strip():
            result.add_error('Code must be a non-empty string')

        return result

    def _validate_http_node(self, config: Dict, result: ValidationResult) -> ValidationResult:
        """Validate HTTP node configuration.

        Args:
            config: Node configuration
            result: Current validation result

        Returns:
            Updated validation result
        """
        # Check URL is valid
        url = config.get('url', '')
        if not isinstance(url, str) or not url.strip():
            result.add_error('URL must be a non-empty string')

        # Check method is valid
        method = config.get('method', '')
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        if method not in valid_methods:
            result.add_error(f'HTTP method must be one of: {", ".join(valid_methods)}')

        return result

    def _validate_transform_node(self, config: Dict, result: ValidationResult) -> ValidationResult:
        """Validate transform node configuration.

        Args:
            config: Node configuration
            result: Current validation result

        Returns:
            Updated validation result
        """
        # Check transformation is specified
        transformation = config.get('transformation', '')
        if not isinstance(transformation, str) or not transformation.strip():
            result.add_error('Transformation must be a non-empty string')

        return result

    def validate_connection(
        self, source_node_id: UUID, target_node_id: UUID, workflow_id: UUID
    ) -> ValidationResult:
        """Validate a connection between two nodes.

        Checks:
        - Both nodes exist
        - Both nodes belong to the same workflow
        - Connection would not create a cycle

        Args:
            source_node_id: ID of source node
            target_node_id: ID of target node
            workflow_id: ID of the workflow

        Returns:
            ValidationResult indicating if connection is valid
        """
        result = ValidationResult(is_valid=True)

        # Check nodes exist
        source_node = self.db.get(Node, source_node_id)
        target_node = self.db.get(Node, target_node_id)

        if not source_node:
            result.add_error(f'Source node {source_node_id} not found')
        if not target_node:
            result.add_error(f'Target node {target_node_id} not found')

        if not result.is_valid:
            return result

        # Check nodes belong to the same workflow
        if source_node.workflow_id != workflow_id:
            result.add_error(f'Source node does not belong to workflow {workflow_id}')
        if target_node.workflow_id != workflow_id:
            result.add_error(f'Target node does not belong to workflow {workflow_id}')

        if not result.is_valid:
            return result

        # Check if connection would create a cycle
        # Get existing connections
        connections_statement = select(Connection).where(Connection.workflow_id == workflow_id)
        connections = self.db.exec(connections_statement).all()

        # Build adjacency list with the new connection
        connection_tuples = [(conn.source_node_id, conn.target_node_id) for conn in connections]
        connection_tuples.append((source_node_id, target_node_id))
        adjacency_list = build_adjacency_list(connection_tuples)

        # Check for cycles
        if detect_cycle(adjacency_list):
            result.add_error('Connection would create a cycle in the workflow')

        return result
