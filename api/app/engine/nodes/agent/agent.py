"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-23 15:27:46
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-30 14:38:15
FilePath: /api/app/engine/nodes/agent/agent.py
Description: Agent Node - LLM代理节点

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
from app.engine.nodes.provider.ollama_node import OllamaNode
from app.models.workflow import Node
from app.utils.json_path import JsonPathUtil

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
        self._node_data: AgentNodeData = AgentNodeData.model_validate(data)

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

    def _find_provider_from_connections(
        self, node: Node, context: ExecutionContext
    ) -> OllamaNode | None:
        """
        从连接关系中查找 provider 节点

        Args:
            node: 当前节点
            context: 执行上下文

        Returns:
            OllamaNode 实例或 None
        """
        # 1. 从 context 获取节点连接关系
        connections = context.get_connections()
        if not connections:
            return None

        # 2. 查询当前 node 的入边 (target_node_id == node.id 的连接)
        incoming_connections = [conn for conn in connections if conn.target_node_id == node.id]

        if not incoming_connections:
            return None

        # 3. 遍历入边，查找 provider 节点
        for conn in incoming_connections:
            source_node_id = conn.source_node_id

            # 从 node_outputs 中获取源节点的输出
            node_outputs = context.node_outputs.get('outputs', {})

            for _, node_data in node_outputs.items():
                outputs = node_data.get('outputs', {})

                # 检查是否是源节点且包含 provider_key
                if node_data.get('id') == str(source_node_id) and 'provider_key' in outputs:
                    provider_key = outputs['provider_key']
                    provider = context.get_global_variable(provider_key)

                    if isinstance(provider, OllamaNode):
                        return provider

        return None

    async def execute(self, node: Node, context: ExecutionContext) -> Dict[str, Any]:
        """执行Agent节点"""
        config = node.config
        # 初始化节点数据
        self.init_node_data(config)

        # 从连接关系中查找 provider
        provider: OllamaNode | None = self._find_provider_from_connections(node, context)

        # 如果仍未找到，尝试获取默认 provider
        if not provider:
            provider = OllamaNode.get_provider_from_context(context, None)

        if not provider:
            return {
                'content': '',
                'extracted': {},
                'error': '未找到Ollama Provider，请确保OllamaNode已在工作流中执行并正确连接',
            }

        # 从context获取消息缓存实例
        cache_key = self._node_data.agent_strategy_name
        max_messages = config.get('memory', {}).get('max_messages', 50)
        message_cache = OllamaNode.get_message_cache_from_context(context, cache_key, max_messages)

        # 添加系统消息（如果配置了且缓存为空）
        system_prompt = config.get('system_prompt')
        if system_prompt and not message_cache.get_messages():
            # 系统消息也支持表达式解析
            if config.get('system_prompt_is_expr', False):
                exprs = JsonPathUtil.get_exprs(system_prompt)
                for expr in exprs:
                    value = context.get_node_output(expr.expr)
                    system_prompt = system_prompt.replace(expr.org_name, str(value), 1)
            message_cache.add_system_message(system_prompt)

        # 获取结构化输出schema
        output_schema = self._get_structured_output_schema(config)

        # 获取提示词配置
        prompt = self._node_data.prompt

        # 判断提示词是否是表达式
        if self._node_data.prompt_is_expr:
            exprs = JsonPathUtil.get_exprs(prompt)
            for expr in exprs:
                value = context.get_node_output(expr.expr)
                prompt = prompt.replace(expr.org_name, str(value), 1)

        # 将结构化输出字符串添加进提示词的最后
        user_prompt = self._build_prompt_with_schema(prompt, output_schema)

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

            # 设置节点输出到 context
            result = {
                'content': content,
                'extracted': extracted_output,
                'model': provider._node_data.model if provider._node_data else 'unknown',
                'usage': response.get('usage', {}),
            }
            return result

        except Exception as e:
            error_result = {
                'content': '',
                'extracted': {},
                'error': f'Agent执行失败: {str(e)}',
            }
            return error_result
