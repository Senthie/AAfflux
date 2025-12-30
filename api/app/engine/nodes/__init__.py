"""
Node Types Module

This module provides utilities for registering and accessing node executors.
Node types are automatically registered when their modules are imported
due to the @register_node_executor decorator.

Usage:
    from app.engine.nodes import node_executor_registry, register_all_nodes

    # 在使用 registry 前调用注册函数
    register_all_nodes()

    # 获取节点执行器
    executor = node_executor_registry.get_executor('AGENT')
"""

# 标记是否已注册
_nodes_registered = False


def _get_registry():
    """延迟导入 registry，避免循环导入"""
    from app.engine.nodes.base.registry import node_executor_registry

    return node_executor_registry


def register_all_nodes() -> None:
    """
    导入所有节点模块以触发装饰器注册。

    使用函数内导入避免循环导入问题。
    此函数可以安全地多次调用，只会注册一次。
    """
    global _nodes_registered
    if _nodes_registered:
        return

    # Provider 节点 (无依赖其他节点)
    # Agent 节点 (依赖 provider 节点)
    from app.engine.nodes.agent.agent import AgentNode  # noqa: F401

    # 基础节点 (无依赖其他节点)
    from app.engine.nodes.chat.chat import ChatNode  # noqa: F401
    from app.engine.nodes.provider.ollama_node import OllamaNode  # noqa: F401

    _nodes_registered = True


# 使用属性访问器延迟加载 registry
class _ModuleProxy:
    @property
    def node_executor_registry(self):
        return _get_registry()


_proxy = _ModuleProxy()


def __getattr__(name):
    if name == 'node_executor_registry':
        return _get_registry()
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


__all__ = [
    'node_executor_registry',
    'register_all_nodes',
]
