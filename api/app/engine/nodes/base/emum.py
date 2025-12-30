"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-23 14:52:34
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-29 16:19:54
FilePath: /api/app/engine/nodes/base/emum.py
Description: node 类的相关的节点类型

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from enum import StrEnum


class NodeTypeEnum(StrEnum):
    """
    节点类型，每个节点都应该，只应该存在一个唯一的节点类型
    """

    ROOT = 'root'
    DIRECTORY = 'directory'
    FILE = 'file'
    LLM = 'llm'
    AGENT = 'agent'
    OLLAMA = 'ollama'
    CHAT = 'chat'


class NodeExecutionTypeEnum(StrEnum):
    """
    节点执行类型分类。
    继承自StrEnum，意味着每个枚举成员既是枚举也是字符串
    """

    # 执行并产生输出的常规节点
    EXECUTABLE = 'executable'  # Regular nodes that execute and produce outputs

    # 流式输出响应节点（如Answer、End）
    RESPONSE = 'response'  # Response nodes that stream outputs (Answer, End)

    # 可选择不同分支的节点（如if-else、分类器）
    BRANCH = 'branch'  # Nodes that can choose different branches (if-else, question-classifier)

    # 管理子图的容器节点（如迭代、循环、图）
    CONTAINER = 'container'  # Container nodes that manage subgraphs (iteration, loop, graph)

    # 可作为执行入口点的节点
    ROOT = 'root'  # Nodes that can serve as execution entry points

    MODEL_PROVIDE = 'model-provide'  # Model provide nodes


class ErrorStrategy(StrEnum):
    """
    错误处理策略。
    """

    FAIL_BRANCH = 'fail-branch'
    DEFAULT_VALUE = 'default-value'


class NodeExecutionResultStatusEnum(StrEnum):
    """
    节点执行结果状态。
    """

    SUCCESS = 'success'
    ERROR = 'error'
    TIMEOUT = 'timeout'
    UNKNOWN = 'unknown'
