"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-29 14:51:19
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-30 12:23:04
FilePath: /api/app/engine/nodes/chat/chat.py
Description: chat 对话节点

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from collections.abc import Mapping
from typing import Any, Dict

from app.engine.execution_context import ExecutionContext
from app.engine.nodes.base import (
    BaseNode,
    ErrorStrategy,
    NodeExecutionTypeEnum,
    NodeTypeEnum,
    RetryConfig,
    register_node_executor,
)
from app.engine.nodes.chat.entities import ChatNodeData
from app.models.workflow import Node


@register_node_executor(NodeTypeEnum.CHAT)
class ChatNode(BaseNode):
    """
    chat 对话节点
    用于对话

    """

    execution_type = NodeExecutionTypeEnum.ROOT
    _node_data: ChatNodeData

    @classmethod
    def version(cls) -> str:
        """返回节点版本号"""
        return '1'

    def init_node_data(self, data: Mapping[str, Any]):
        """数据初始化"""
        self._node_data: ChatNodeData = ChatNodeData.model_validate(data)

    def _get_error_strategy(self) -> ErrorStrategy | None:
        return self._node_data.error_strategy if self._node_data else None

    def _get_retry_config(self) -> RetryConfig:
        return self._node_data.retry_config if self._node_data else RetryConfig()

    def _get_title(self) -> str:
        return self._node_data.title if self._node_data else 'Agent'

    def _get_description(self) -> str | None:
        return self._node_data.desc if self._node_data else None

    def validate_config(self, config: Dict[str, Any]) -> bool:
        required_fields = ['agent_strategy_name']
        return all(field in config for field in required_fields)

    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        # 记录运行时间
        self.init_node_data(node.config)
        return {'prompt': self._node_data.prompt}
