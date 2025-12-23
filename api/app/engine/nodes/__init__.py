"""
Node Types Module

This module imports and registers all available node types for the workflow engine.
Each node type is automatically registered when imported due to the @register_node_executor decorator.
"""

# Import all node executors to register them
from app.engine.nodes.code_node import CodeNodeExecutor
from app.engine.nodes.condition_node import ConditionNodeExecutor
from app.engine.nodes.http_node import HTTPNodeExecutor
from app.engine.nodes.llm_node import LLMNodeExecutor
from app.engine.nodes.ollama_node import OllamaNodeExecutor
from app.engine.nodes.transform_node import TransformNodeExecutor

# Export the node executors for external use
__all__ = [
    'LLMNodeExecutor',
    'OllamaNodeExecutor',
    'ConditionNodeExecutor',
    'CodeNodeExecutor',
    'HTTPNodeExecutor',
    'TransformNodeExecutor',
]

# The node executors are automatically registered with the global registry
# when this module is imported due to the @register_node_executor decorators
