"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-10 15:57:56
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-02-04 17:19:33
FilePath: /api/app/engine/topological_sorter.py
Description: Topological sorting for workflow execution.

This module provides topological sorting functionality specifically for workflow execution,
building on the DAG utilities but with workflow-specific enhancements.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Dict, List, Set, Tuple
from uuid import UUID

from app.models.workflow.workflow import ConnectionModel, NodeModel
from app.utils.dag import build_adjacency_list, topological_sort as dag_topological_sort


class TopologicalSorter:
    """Topological sorter for workflow nodes."""

    def __init__(self, nodes: List[NodeModel], connections: List[ConnectionModel]):
        """Initialize the topological sorter.

        Args:
            nodes: List of workflow nodes
            connections: List of connections between nodes
        """
        self.nodes = {node.id: node for node in nodes}
        self.connections = connections
        self._adjacency_list = self._build_adjacency_list()

    def _build_adjacency_list(self) -> Dict[UUID, List[UUID]]:
        """Build adjacency list from connections.

        Returns:
            Dictionary mapping node IDs to their successor node IDs
        """
        # Convert connections to tuples
        connection_tuples: List[Tuple[UUID, UUID]] = [
            (conn.source_node_id, conn.target_node_id) for conn in self.connections
        ]

        # Build adjacency list using DAG utility
        adjacency_list = build_adjacency_list(connection_tuples)

        # Ensure all nodes are in the adjacency list (even isolated ones)
        for node_id in self.nodes:
            if node_id not in adjacency_list:
                adjacency_list[node_id] = []

        return adjacency_list

    def sort(self) -> List[NodeModel]:
        """Sort nodes in topological order.

        Returns:
            List of nodes in execution order

        Raises:
            CycleDetectedError: If the workflow contains cycles
        """
        # Get sorted node IDs
        sorted_node_ids = dag_topological_sort(self._adjacency_list)

        # Convert to Node objects
        sorted_nodes = []
        for node_id in sorted_node_ids:
            if node_id in self.nodes:
                sorted_nodes.append(self.nodes[node_id])

        return sorted_nodes

    def get_execution_levels(self) -> List[List[NodeModel]]:
        """Get nodes grouped by execution level.

        Nodes at the same level can be executed in parallel.

        Returns:
            List of lists, where each inner list contains nodes that can be executed in parallel
        """
        # Calculate in-degree for each node
        in_degree: Dict[UUID, int] = {}
        for node_id in self.nodes:
            in_degree[node_id] = 0

        # Calculate actual in-degrees
        for _source_id, targets in self._adjacency_list.items():
            for target_id in targets:
                if target_id in in_degree:
                    in_degree[target_id] += 1

        levels: List[List[NodeModel]] = []
        remaining_nodes = set(self.nodes.keys())

        while remaining_nodes:
            # Find nodes with no dependencies (in-degree 0)
            current_level_ids = [node_id for node_id in remaining_nodes if in_degree[node_id] == 0]

            if not current_level_ids:
                # This shouldn't happen if the graph is acyclic
                raise ValueError('Unable to determine execution levels - possible cycle')

            # Convert to Node objects
            current_level = [self.nodes[node_id] for node_id in current_level_ids]
            levels.append(current_level)

            # Remove current level nodes and update in-degrees
            for node_id in current_level_ids:
                remaining_nodes.remove(node_id)
                # Reduce in-degree of successors
                for successor_id in self._adjacency_list.get(node_id, []):
                    if successor_id in in_degree:
                        in_degree[successor_id] -= 1

        return levels

    def get_dependencies(self, node_id: UUID) -> List[NodeModel]:
        """Get all nodes that the given node depends on.

        Args:
            node_id: ID of the node

        Returns:
            List of nodes that must execute before the given node
        """
        dependencies = []

        # Find all connections where this node is the target
        for connection in self.connections:
            if connection.target_node_id == node_id:
                source_node = self.nodes.get(connection.source_node_id)
                if source_node:
                    dependencies.append(source_node)

        return dependencies

    def get_dependents(self, node_id: UUID) -> List[NodeModel]:
        """Get all nodes that depend on the given node.

        Args:
            node_id: ID of the node

        Returns:
            List of nodes that must wait for the given node to complete
        """
        dependents = []

        # Find all connections where this node is the source
        for connection in self.connections:
            if connection.source_node_id == node_id:
                target_node = self.nodes.get(connection.target_node_id)
                if target_node:
                    dependents.append(target_node)

        return dependents

    def is_ready_to_execute(self, node_id: UUID, completed_nodes: Set[UUID]) -> bool:
        """Check if a node is ready to execute.

        A node is ready if all its dependencies have completed.

        Args:
            node_id: ID of the node to check
            completed_nodes: Set of node IDs that have completed execution

        Returns:
            True if the node is ready to execute, False otherwise
        """
        dependencies = self.get_dependencies(node_id)
        dependency_ids = {dep.id for dep in dependencies}

        # Node is ready if all dependencies are completed
        return dependency_ids.issubset(completed_nodes)

    def get_next_executable_nodes(self, completed_nodes: Set[UUID]) -> List[NodeModel]:
        """Get all nodes that are ready to execute.

        Args:
            completed_nodes: Set of node IDs that have completed execution

        Returns:
            List of nodes that can be executed next
        """
        executable_nodes = []

        for node_id, node in self.nodes.items():
            if node_id not in completed_nodes and self.is_ready_to_execute(
                node_id, completed_nodes
            ):
                executable_nodes.append(node)

        return executable_nodes
