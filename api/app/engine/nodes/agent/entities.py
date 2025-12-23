"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-23 15:27:57
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-23 15:29:05
FilePath: /api/app/engine/nodes/agent/entities.py
Description: Agent 的实体类

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from app.engine.nodes.base.entities import BaseNodeData


class AgentNodeData(BaseNodeData):
    # 代理策略相关字段
    agent_strategy_provider_name: str  # 冗余字段
    agent_strategy_name: str
    agent_strategy_label: str  # 冗余字段

    # 内存配置
    # memory: MemoryConfig | None = None

    # 版本控制
    tool_node_version: str | None = None

    # 嵌套模型：代理输入定义
    # class AgentInput(BaseModel):
    #     value: Union[list[str], list[ToolSelector], Any]
    #     type: Literal['mixed', 'variable', 'constant']

    # 代理参数映射
    # agent_parameters: dict[str, AgentInput]
