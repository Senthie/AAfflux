"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-29 17:20:58
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-16 16:17:13
FilePath: /api/tests/unit/test_chat_node.py
Description: 测试 chat node 是否如期运行

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from uuid import uuid4

import pytest

from app.engine.execution_context import ExecutionContext

# 导入引擎相关模块
from app.engine.nodes.base.emum import NodeTypeEnum
from app.engine.nodes.base.registry import node_executor_registry

# 导入 ChatNode 以触发注册
from app.engine.nodes.chat.chat import ChatNode  # noqa: F401

# 导入模型
from app.models.workflow.workflow import ExecutionRecordModel, NodeModel, WorkflowModel


# ============ Fixtures ============
@pytest.fixture
def workflow():
    """创建测试工作流"""
    return WorkflowModel(
        id=uuid4(),
        name='Test Workflow',
        workspace_id=uuid4(),
        created_by=uuid4(),
    )


@pytest.fixture
def execution_record(workflow):
    """创建执行记录"""
    return ExecutionRecordModel(
        id=uuid4(),
        workflow_id=workflow.id,
        inputs={},
        status='PENDING',
    )


@pytest.fixture
def context(workflow, execution_record):
    """创建执行上下文"""
    return ExecutionContext(workflow, execution_record, {})


@pytest.mark.integration
@pytest.mark.asyncio
class TestChatNode:
    async def test_chat_node_executor(self, workflow, execution_record):
        # 创建上下文
        context = ExecutionContext(workflow, execution_record, {})

        # 创建 Node 实体，使用 NodeTypeEnum.CHAT 与 ChatNode 注册的类型一致
        chat_node = NodeModel(
            id=uuid4(),
            workflow_id=workflow.id,
            type=NodeTypeEnum.CHAT.value,
            config={'prompt': '1 + 1 = ?', 'title': 'Test Chat Node'},
        )

        # 获取 node 的实例
        executor: ChatNode = node_executor_registry.get_executor(chat_node.type)

        result = executor.execute(chat_node, context)

        assert result is not None, 'ChatNode should return a result'
        assert isinstance(result, dict), 'ChatNode should return a dictionary'
        assert result.get('prompt') == '1 + 1 = ?', 'ChatNode should return the correct prompt'
        result = executor.execute_with_result(chat_node, context, [])
        assert result is not None, 'ChatNode should return a result'
