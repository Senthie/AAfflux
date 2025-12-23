"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-23 17:54:48
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-23 18:18:24
FilePath: /api/app/engine/nodes/provider/ollama_node.py
Description: Ollama Provider Node - 继承BaseNode的Ollama供应商节点

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from collections.abc import Mapping
import json
import re
from typing import Any, Dict

import httpx
from pydantic import BaseModel, Field

from app.engine.execution_context import ExecutionContext
from app.engine.nodes.base.emum import (
    ErrorStrategy,
    NodeExecutionTypeEnum,
    NodeTypeEnum,
)
from app.engine.nodes.base.entities import BaseNodeData, RetryConfig
from app.engine.nodes.base.node import BaseNode, register_node_executor
from app.models.workflow import Node

# ============ 数据模型 ============


class OllamaNodeData(BaseNodeData):
    """Ollama节点数据"""

    base_url: str = Field(default='http://localhost:11434', description='Ollama API地址')
    api_key: str | None = Field(default=None, description='API Key (如果需要)')
    model: str = Field(default='llama2', description='模型名称')
    timeout: int = Field(default=120, description='请求超时时间(秒)')


class OllamaMessage(BaseModel):
    """Ollama消息格式"""

    role: str  # system, user, assistant
    content: str


# ============ 消息缓存 ============


class MessageCache:
    """
    消息缓存类 - 管理对话历史

    用于维护多轮对话的上下文
    """

    def __init__(self, max_messages: int = 50):
        self._messages: list[OllamaMessage] = []
        self._max_messages = max_messages

    def add_message(self, role: str, content: str):
        """添加消息"""
        self._messages.append(OllamaMessage(role=role, content=content))
        if len(self._messages) > self._max_messages:
            system_msgs = [m for m in self._messages if m.role == 'system']
            other_msgs = [m for m in self._messages if m.role != 'system']
            keep_count = self._max_messages - len(system_msgs)
            self._messages = system_msgs + other_msgs[-keep_count:]

    def add_system_message(self, content: str):
        self.add_message('system', content)

    def add_user_message(self, content: str):
        self.add_message('user', content)

    def add_assistant_message(self, content: str):
        self.add_message('assistant', content)

    def get_messages(self) -> list[OllamaMessage]:
        return self._messages.copy()

    def clear(self):
        self._messages.clear()

    def get_last_message(self) -> OllamaMessage | None:
        return self._messages[-1] if self._messages else None


# ============ Ollama Provider Node ============


@register_node_executor(NodeTypeEnum.OLLAMA)
class OllamaNode(BaseNode):
    """
    Ollama供应商节点 - 继承BaseNode

    执行后将自身实例存储到ExecutionContext中，供AgentNode调用
    """

    execution_type = NodeExecutionTypeEnum.EXECUTABLE
    _node_data: OllamaNodeData
    _client: httpx.AsyncClient | None = None

    # Context中存储provider实例的key前缀
    PROVIDER_KEY_PREFIX = 'ollama_provider_'

    def __init__(self):
        super().__init__()
        self._node_data = None
        self._client = None

    @classmethod
    def version(cls) -> str:
        return '1'

    def init_node_data(self, data: Mapping[str, Any]):
        """数据初始化"""
        self._node_data = OllamaNodeData.model_validate(data)

    def _get_error_strategy(self) -> ErrorStrategy | None:
        return self._node_data.error_strategy if self._node_data else None

    def _get_retry_config(self) -> RetryConfig:
        return self._node_data.retry_config if self._node_data else RetryConfig()

    def _get_title(self) -> str:
        return self._node_data.title if self._node_data else 'Ollama Provider'

    def _get_description(self) -> str | None:
        return self._node_data.desc if self._node_data else None

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证节点配置"""
        return 'model' in config or 'base_url' in config

    # ============ HTTP Client ============

    @property
    def client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            headers = {'Content-Type': 'application/json'}
            if self._node_data and self._node_data.api_key:
                headers['Authorization'] = f'Bearer {self._node_data.api_key}'

            self._client = httpx.AsyncClient(
                base_url=self._node_data.base_url if self._node_data else 'http://localhost:11434',
                headers=headers,
                timeout=self._node_data.timeout if self._node_data else 120,
            )
        return self._client

    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    # ============ API Methods ============

    async def chat(
        self,
        messages: list[OllamaMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """发送聊天请求"""
        payload = {
            'model': model or (self._node_data.model if self._node_data else 'llama2'),
            'messages': [msg.model_dump() for msg in messages],
            'stream': stream,
            'options': {'temperature': temperature},
        }

        if max_tokens:
            payload['options']['num_predict'] = max_tokens

        response = await self.client.post('/api/chat', json=payload)
        response.raise_for_status()
        return response.json()

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """发送生成请求"""
        payload = {
            'model': model or (self._node_data.model if self._node_data else 'llama2'),
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': temperature},
        }

        if system:
            payload['system'] = system
        if max_tokens:
            payload['options']['num_predict'] = max_tokens

        response = await self.client.post('/api/generate', json=payload)
        response.raise_for_status()
        return response.json()

    def extract_content(self, response: dict[str, Any]) -> str:
        """从响应中提取内容"""
        if 'message' in response:
            return response['message'].get('content', '')
        if 'response' in response:
            return response['response']
        return ''

    @staticmethod
    def extract_structured_output(content: str, pattern: str | None = None) -> dict[str, Any]:
        """从输出内容中提取结构化数据"""
        if pattern:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return {'extracted': match.group(1) if match.groups() else match.group(0)}

        # 默认尝试提取JSON
        json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        match = re.search(json_pattern, content)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        return {'raw_content': content}

    # ============ Node Execution ============

    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """
        执行Ollama节点

        主要功能：初始化provider并存储到context中供其他节点使用
        """
        config = node.config
        self.init_node_data(config)

        # 生成唯一的provider key
        provider_key = f'{self.PROVIDER_KEY_PREFIX}{node.id}'

        # 将自身实例存储到context中
        context.update_global_variable(provider_key, self)

        # 同时存储一个默认的provider引用（方便AgentNode获取）
        context.update_global_variable('default_ollama_provider', self)

        return {
            'provider_key': provider_key,
            'model': self._node_data.model,
            'base_url': self._node_data.base_url,
            'status': 'initialized',
        }

    # ============ Context Helper Methods ============

    @staticmethod
    def get_provider_from_context(
        context: ExecutionContext, provider_key: str | None = None
    ) -> 'OllamaNode | None':
        """
        从context中获取OllamaNode实例

        Args:
            context: 执行上下文
            provider_key: provider的key，如果为None则获取默认provider

        Returns:
            OllamaNode实例或None
        """
        if provider_key:
            provider = context.get_global_variable(provider_key)
        else:
            provider = context.get_global_variable('default_ollama_provider')

        if isinstance(provider, OllamaNode):
            return provider
        return None

    @staticmethod
    def get_message_cache_from_context(
        context: ExecutionContext, cache_key: str, max_messages: int = 50
    ) -> MessageCache:
        """
        从context中获取或创建MessageCache

        Args:
            context: 执行上下文
            cache_key: 缓存的key
            max_messages: 最大消息数

        Returns:
            MessageCache实例
        """
        full_key = f'message_cache_{cache_key}'
        existing_cache = context.get_global_variable(full_key)

        if existing_cache and isinstance(existing_cache, MessageCache):
            return existing_cache

        cache = MessageCache(max_messages=max_messages)
        context.update_global_variable(full_key, cache)
        return cache
