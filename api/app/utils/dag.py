"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-04 09:50:20
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-05 01:15:18
FilePath: /api/app/utils/dag.py
Description:
    DAG (Directed Acyclic Graph) utility functions.
    This module provides utilities for working with directed acyclic graphs,
    including cycle detection and topological sorting.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Dict, List, Set, Tuple
from uuid import UUID


class CycleDetectedError(Exception):
    """Exception raised when a cycle is detected in the graph."""

    pass


def detect_cycle(adjacency_list: Dict[UUID, List[UUID]]) -> bool:
    """Detect if there is a cycle in the directed graph.

    Uses depth-first search with three colors:
    - WHITE (0): unvisited
    - GRAY (1): currently being processed
    - BLACK (2): completely processed

    Args:
        adjacency_list: Dictionary mapping node IDs to lists of their successor node IDs

    Returns:
        True if a cycle is detected, False otherwise
    """
    # Color states
    WHITE, GRAY, BLACK = 0, 1, 2

    # Initialize all nodes as WHITE
    color = {node: WHITE for node in adjacency_list}

    def dfs(node: UUID) -> bool:
        """Depth-first search to detect cycles.

        Args:
            node: Current node being visited

        Returns:
            True if a cycle is detected, False otherwise
        """
        color[node] = GRAY

        # Visit all neighbors
        for neighbor in adjacency_list.get(node, []):
            # If neighbor is not in color dict, add it
            if neighbor not in color:
                color[neighbor] = WHITE

            if color[neighbor] == GRAY:
                # Back edge found - cycle detected
                return True
            elif color[neighbor] == WHITE:
                if dfs(neighbor):
                    return True

        color[node] = BLACK
        return False

    # Check all nodes
    for node_id in adjacency_list:
        if color[node_id] == WHITE:
            if dfs(node_id):
                return True

    return False


def topological_sort(adjacency_list: Dict[UUID, List[UUID]]) -> List[UUID]:
    """Perform topological sort on a directed acyclic graph.

    Uses Kahn's algorithm (BFS-based approach).

    Args:
        adjacency_list: Dictionary mapping node IDs to lists of their successor node IDs

    Returns:
        List of node IDs in topologically sorted order

    Raises:
        CycleDetectedError: If the graph contains a cycle
    """
    # First check for cycles
    if detect_cycle(adjacency_list):
        raise CycleDetectedError('Cannot perform topological sort: cycle detected in graph')

    # Calculate in-degree for each node
    in_degree: Dict[UUID, int] = {}
    all_nodes: Set[UUID] = set(adjacency_list.keys())

    # Add all nodes that appear as targets
    for successors in adjacency_list.values():
        all_nodes.update(successors)

    # Initialize in-degree
    for node in all_nodes:
        in_degree[node] = 0

    # Calculate in-degree
    for _node, successors in adjacency_list.items():
        for successor in successors:
            in_degree[successor] = in_degree.get(successor, 0) + 1

    # Find all nodes with in-degree 0
    queue: List[UUID] = [node for node in all_nodes if in_degree[node] == 0]
    result: List[UUID] = []

    while queue:
        # Remove a node with in-degree 0
        node = queue.pop(0)
        result.append(node)

        # Reduce in-degree of successors
        for successor in adjacency_list.get(node, []):
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                queue.append(successor)

    # If result doesn't contain all nodes, there's a cycle
    if len(result) != len(all_nodes):
        raise CycleDetectedError('Cannot perform topological sort: cycle detected in graph')

    return result


def build_adjacency_list(connections: List[Tuple[UUID, UUID]]) -> Dict[UUID, List[UUID]]:
    """Build an adjacency list from a list of connections.

    Args:
        connections: List of (source_node_id, target_node_id) tuples

    Returns:
        Dictionary mapping node IDs to lists of their successor node IDs
    """
    adjacency_list: Dict[UUID, List[UUID]] = {}

    for source, target in connections:
        if source not in adjacency_list:
            adjacency_list[source] = []
        adjacency_list[source].append(target)

    return adjacency_list


def find_root_nodes(adjacency_list: Dict[UUID, List[UUID]]) -> List[UUID]:
    """Find all root nodes (nodes with no incoming edges).

    Args:
        adjacency_list: Dictionary mapping node IDs to lists of their successor node IDs

    Returns:
        List of root node IDs
    """
    all_nodes: Set[UUID] = set(adjacency_list.keys())
    target_nodes: Set[UUID] = set()

    # Collect all target nodes
    for successors in adjacency_list.values():
        target_nodes.update(successors)

    # Root nodes are those that are not targets
    root_nodes = all_nodes - target_nodes

    return list(root_nodes)


def find_leaf_nodes(adjacency_list: Dict[UUID, List[UUID]]) -> List[UUID]:
    """Find all leaf nodes (nodes with no outgoing edges).

    Args:
        adjacency_list: Dictionary mapping node IDs to lists of their successor node IDs

    Returns:
        List of leaf node IDs
    """
    all_nodes: Set[UUID] = set(adjacency_list.keys())

    # Add all nodes that appear as targets
    for successors in adjacency_list.values():
        all_nodes.update(successors)

    # Leaf nodes are those with no successors
    leaf_nodes = [node for node in all_nodes if not adjacency_list.get(node, [])]

    return leaf_nodes


def validate_dag_structure(adjacency_list: Dict[UUID, List[UUID]]) -> Tuple[bool, str]:
    """Validate that the graph structure is a valid DAG.

    Args:
        adjacency_list: Dictionary mapping node IDs to lists of their successor node IDs

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for cycles
    if detect_cycle(adjacency_list):
        return False, 'Graph contains a cycle'

    # Check for isolated nodes (nodes with no connections)
    all_nodes: Set[UUID] = set(adjacency_list.keys())
    for successors in adjacency_list.values():
        all_nodes.update(successors)

    # A valid workflow should have at least one root and one leaf
    root_nodes = find_root_nodes(adjacency_list)
    leaf_nodes = find_leaf_nodes(adjacency_list)

    if not root_nodes:
        return False, 'Graph has no root nodes (all nodes have incoming edges)'

    if not leaf_nodes:
        return False, 'Graph has no leaf nodes (all nodes have outgoing edges)'

    return True, ''
