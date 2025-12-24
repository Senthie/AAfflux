"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-23 15:27:46
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-24 15:16:59
FilePath: /api/app/engine/nodes/agent/agent.py
Description: Agent Node - LLM代理节点

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from collections.abc import Mapping
from typing import Any, Dict

from app.engine.execution_context import ExecutionContext
from app.engine.nodes.base.emum import (
    ErrorStrategy,
    NodeExecutionTypeEnum,
    NodeTypeEnum,
)
from app.engine.nodes.base.entities import RetryConfig
from app.engine.nodes.base.node import BaseNode, register_node_executor
from app.engine.nodes.provider.ollama_node import OllamaNode
from app.models.workflow import Node

from .entities import AgentNodeData


@register_node_executor(NodeTypeEnum.AGENT)
class AgentNode(BaseNode):
    """
    Agent节点 - 用于调用LLM模型

    支持:
    - 从context获取模型供应商节点实例
    - 消息缓存/多轮对话
    - 结构化输出提取
    """

    execution_type = NodeExecutionTypeEnum.EXECUTABLE
    _node_data: AgentNodeData

    def __init__(self):
        super().__init__()

    @classmethod
    def version(cls) -> str:
        return '1'

    def init_node_data(self, data: Mapping[str, Any]):
        """数据初始化"""
        self._node_data = AgentNodeData.model_validate(data)

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

    def _get_structured_output_schema(self, config: Dict[str, Any]) -> str | None:
        """从config获取结构化输出的字符串"""
        output_schema = config.get('output_schema')
        if output_schema:
            if isinstance(output_schema, dict):
                import json

                return json.dumps(output_schema, ensure_ascii=False)
            return str(output_schema)
        return None

    def _build_prompt_with_schema(self, prompt: str, output_schema: str | None) -> str:
        """将结构化输出字符串添加进提示词的最后"""
        if not output_schema:
            return prompt

        schema_instruction = f"""
            请按照以下JSON格式输出你的回答:
            ```json
            {output_schema}
            ```

            确保输出是有效的JSON格式。
            """
        return prompt + schema_instruction

    def _extract_output(
        self, content: str, extraction_pattern: str | None = None
    ) -> Dict[str, Any]:
        """通过re对输出结果进行提取"""
        result = OllamaNode.extract_structured_output(content, extraction_pattern)
        if 'raw_content' not in result:
            result['raw_content'] = content
        return result

    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """执行Agent节点"""
        config = node.config
        inputs = context.get_node_input(node, [])

        # 初始化节点数据
        self.init_node_data(config)

        # 从context获取模型供应商的请求实例
        provider_key = config.get('provider_key')  # 可指定特定的provider
        provider = OllamaNode.get_provider_from_context(context, provider_key)

        if not provider:
            return {
                'content': '',
                'extracted': {},
                'error': '未找到Ollama Provider，请确保OllamaNode已在工作流中执行',
            }

        # 从context获取消息缓存实例
        cache_key = self._node_data.agent_strategy_name
        max_messages = config.get('memory', {}).get('max_messages', 50)
        message_cache = OllamaNode.get_message_cache_from_context(context, cache_key, max_messages)

        # 获取结构化输出schema
        output_schema = self._get_structured_output_schema(config)

        # 获取提示词配置
        system_prompt = config.get('system_prompt', '')
        user_prompt_template = config.get('user_prompt', '{input}')

        # 渲染用户提示词
        user_prompt = user_prompt_template
        for key, value in inputs.items():
            user_prompt = user_prompt.replace(f'{{{key}}}', str(value))

        # 将结构化输出字符串添加进提示词的最后
        user_prompt = self._build_prompt_with_schema(user_prompt, output_schema)

        # 构建消息
        if system_prompt and not any(m.role == 'system' for m in message_cache.get_messages()):
            message_cache.add_system_message(system_prompt)

        message_cache.add_user_message(user_prompt)

        try:
            # 根据模型供应商的实例，创建请求并获取结果
            response = await provider.chat(
                messages=message_cache.get_messages(),
                temperature=config.get('temperature', 0.7),
                max_tokens=config.get('max_tokens'),
            )

            # 提取响应内容
            content = provider.extract_content(response)

            # 添加助手回复到缓存
            message_cache.add_assistant_message(content)

            # 通过re对输出结果进行提取
            extraction_pattern = config.get('extraction_pattern')
            extracted_output = self._extract_output(content, extraction_pattern)

            return {
                'content': content,
                'extracted': extracted_output,
                'model': provider._node_data.model if provider._node_data else 'unknown',
                'usage': response.get('usage', {}),
            }

        except Exception as e:
            return {
                'content': '',
                'extracted': {},
                'error': f'Agent执行失败: {str(e)}',
            }
