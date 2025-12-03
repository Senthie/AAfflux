# 当前 BPM 改造方案

## 📋 方案概述

本方案提供在不集成 Camunda 的情况下，如何改造和增强当前自研 BPM 引擎，使其满足基本的 BPMN 2.0 规范和业务需求。

---

## 🎯 改造目标

### 1. 核心目标

- ✅ 支持基本的 BPMN 2.0 元素
- ✅ 实现可视化流程设计器
- ✅ 支持复杂网关（并行、排他、包容）
- ✅ 支持子流程和调用活动
- ✅ 实现事件驱动机制
- ✅ 支持流程版本管理
- ✅ 实现分布式事务处理

### 2. 非目标

- ❌ 完全符合 BPMN 2.0 规范（过于复杂）
- ❌ 支持所有 BPMN 元素（只实现常用的）
- ❌ 与第三方 BPMN 引擎兼容

---

## 🏗️ 改造架构

### 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    BPM Engine Architecture                   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Process Designer (前端)                  │  │
│  │  - BPMN.js 集成                                       │  │
│  │  - 拖拽式设计                                         │  │
│  │  - 元素配置面板                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Process Definition Layer                 │  │
│  │  - BPMN XML 解析器                                    │  │
│  │  - 流程验证器                                         │  │
│  │  - 版本管理                                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Execution Engine                         │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │ Event      │  │ Task       │  │ Gateway    │     │  │
│  │  │ Handler    │  │ Executor   │  │ Evaluator  │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  │  ┌────────────┐  ┌────────────┐                     │  │
│  │  │ Subprocess │  │ Transaction│                     │  │
│  │  │ Manager    │  │ Manager    │                     │  │
│  │  └────────────┘  └────────────┘                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              State Management                         │  │
│  │  - Process Instance State                             │  │
│  │  - Task State                                         │  │
│  │  - Variable Store                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 数据模型改造

### 1. 新增 BPMN 元素表

创建 `api/app/models/bpm/element.py`：

```python
"""BPMN 元素模型"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Column, JSON
from enum import Enum


class ElementType(str, Enum):
    """BPMN 元素类型"""
    # 事件
    START_EVENT = "start_event"
    END_EVENT = "end_event"
    INTERMEDIATE_EVENT = "intermediate_event"
    BOUNDARY_EVENT = "boundary_event"
    
    # 任务
    USER_TASK = "user_task"
    SERVICE_TASK = "service_task"
    SCRIPT_TASK = "script_task"
    SEND_TASK = "send_task"
    RECEIVE_TASK = "receive_task"
    
    # 网关
    EXCLUSIVE_GATEWAY = "exclusive_gateway"
    PARALLEL_GATEWAY = "parallel_gateway"
    INCLUSIVE_GATEWAY = "inclusive_gateway"
    EVENT_BASED_GATEWAY = "event_based_gateway"
    
    # 子流程
    SUBPROCESS = "subprocess"
    CALL_ACTIVITY = "call_activity"
    
    # 其他
    SEQUENCE_FLOW = "sequence_flow"


class ProcessElement(SQLModel, table=True):
    """流程元素表 - 存储 BPMN 元素定义"""
    
    __tablename__ = "bpm_process_elements"
    
    # 主键
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # 流程定义
    process_definition_id: UUID = Field(
        foreign_key="bpm_process_definitions.id",
        index=True
    )
    
    # 元素信息
    element_id: str = Field(max_length=255, index=True)  # BPMN 中的 ID
    element_type: ElementType
    name: str = Field(max_length=255)
    
    # 元素配置
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # 位置信息（用于可视化）
    position_x: Optional[float] = Field(default=None)
    position_y: Optional[float] = Field(default=None)
    width: Optional[float] = Field(default=None)
    height: Optional[float] = Field(default=None)
    
    # 审计字段
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SequenceFlow(SQLModel, table=True):
    """顺序流表 - 存储元素之间的连接"""
    
    __tablename__ = "bpm_sequence_flows"
    
    # 主键
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # 流程定义
    process_definition_id: UUID = Field(
        foreign_key="bpm_process_definitions.id",
        index=True
    )
    
    # 流信息
    flow_id: str = Field(max_length=255, index=True)  # BPMN 中的 ID
    name: Optional[str] = Field(default=None, max_length=255)
    
    # 源和目标
    source_element_id: str = Field(max_length=255)  # 源元素的 element_id
    target_element_id: str = Field(max_length=255)  # 目标元素的 element_id
    
    # 条件表达式（用于网关）
    condition_expression: Optional[str] = Field(default=None)
    
    # 是否默认流（用于排他网关）
    is_default: bool = Field(default=False)
    
    # 审计字段
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExecutionToken(SQLModel, table=True):
    """执行令牌表 - 跟踪流程执行位置"""
    
    __tablename__ = "bpm_execution_tokens"
    
    # 主键
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # 流程实例
    process_instance_id: UUID = Field(
        foreign_key="bpm_process_instances.id",
        index=True
    )
    
    # 当前位置
    current_element_id: str = Field(max_length=255)  # 当前所在元素
    
    # 父令牌（用于并行网关）
    parent_token_id: Optional[UUID] = Field(
        default=None,
        foreign_key="bpm_execution_tokens.id"
    )
    
    # 状态
    is_active: bool = Field(default=True)
    is_waiting: bool = Field(default=False)  # 等待状态（如等待用户任务）
    
    # 审计字段
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
```

---

## 🔧 核心组件实现

### 1. BPMN XML 解析器

创建 `api/app/engine/bpmn/parser.py`：

```python
"""BPMN XML 解析器"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any
from uuid import UUID

from app.models.bpm.element import ProcessElement, SequenceFlow, ElementType
from app.core.logging import get_logger

logger = get_logger(__name__)


class BPMNParser:
    """BPMN XML 解析器"""
    
    # BPMN 命名空间
    BPMN_NS = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
    
    def parse(self, bpmn_xml: str, process_definition_id: UUID) -> Dict[str, Any]:
        """
        解析 BPMN XML
        
        Args:
            bpmn_xml: BPMN XML 字符串
            process_definition_id: 流程定义ID
        
        Returns:
            解析结果，包含元素和流
        """
        root = ET.fromstring(bpmn_xml)
        
        # 查找 process 元素
        process = root.find('.//bpmn:process', self.BPMN_NS)
        if process is None:
            raise ValueError("No process element found in BPMN XML")
        
        # 解析元素
        elements = self._parse_elements(process, process_definition_id)
        
        # 解析顺序流
        flows = self._parse_sequence_flows(process, process_definition_id)
        
        return {
            'process_id': process.get('id'),
            'process_name': process.get('name'),
            'elements': elements,
            'flows': flows
        }
    
    def _parse_elements(
        self,
        process: ET.Element,
        process_definition_id: UUID
    ) -> List[ProcessElement]:
        """解析流程元素"""
        elements = []
        
        # 解析各种元素类型
        element_mappings = {
            'startEvent': ElementType.START_EVENT,
            'endEvent': ElementType.END_EVENT,
            'userTask': ElementType.USER_TASK,
            'serviceTask': ElementType.SERVICE_TASK,
            'scriptTask': ElementType.SCRIPT_TASK,
            'exclusiveGateway': ElementType.EXCLUSIVE_GATEWAY,
            'parallelGateway': ElementType.PARALLEL_GATEWAY,
            'inclusiveGateway': ElementType.INCLUSIVE_GATEWAY,
            'subProcess': ElementType.SUBPROCESS,
            'callActivity': ElementType.CALL_ACTIVITY,
        }
        
        for bpmn_type, element_type in element_mappings.items():
            for elem in process.findall(f'.//bpmn:{bpmn_type}', self.BPMN_NS):
                element = self._parse_single_element(
                    elem,
                    element_type,
                    process_definition_id
                )
                elements.append(element)
        
        return elements
    
    def _parse_single_element(
        self,
        elem: ET.Element,
        element_type: ElementType,
        process_definition_id: UUID
    ) -> ProcessElement:
        """解析单个元素"""
        element_id = elem.get('id')
        name = elem.get('name', element_id)
        
        # 解析配置
        config = {}
        
        # 用户任务特殊处理
        if element_type == ElementType.USER_TASK:
            config['assignee'] = elem.get('assignee')
            config['candidate_users'] = elem.get('candidateUsers', '').split(',')
            config['candidate_groups'] = elem.get('candidateGroups', '').split(',')
            
            # 解析表单
            form_key = elem.get('formKey')
            if form_key:
                config['form_key'] = form_key
        
        # 服务任务特殊处理
        elif element_type == ElementType.SERVICE_TASK:
            config['implementation'] = elem.get('implementation')
            config['class'] = elem.get('class')
            config['expression'] = elem.get('expression')
        
        # 脚本任务特殊处理
        elif element_type == ElementType.SCRIPT_TASK:
            script_elem = elem.find('.//bpmn:script', self.BPMN_NS)
            if script_elem is not None:
                config['script'] = script_elem.text
                config['script_format'] = elem.get('scriptFormat', 'python')
        
        # 网关特殊处理
        elif 'gateway' in element_type.value:
            config['default_flow'] = elem.get('default')
        
        return ProcessElement(
            process_definition_id=process_definition_id,
            element_id=element_id,
            element_type=element_type,
            name=name,
            config=config
        )
    
    def _parse_sequence_flows(
        self,
        process: ET.Element,
        process_definition_id: UUID
    ) -> List[SequenceFlow]:
        """解析顺序流"""
        flows = []
        
        for flow_elem in process.findall('.//bpmn:sequenceFlow', self.BPMN_NS):
            flow_id = flow_elem.get('id')
            name = flow_elem.get('name')
            source = flow_elem.get('sourceRef')
            target = flow_elem.get('targetRef')
            
            # 解析条件表达式
            condition_elem = flow_elem.find('.//bpmn:conditionExpression', self.BPMN_NS)
            condition = condition_elem.text if condition_elem is not None else None
            
            flow = SequenceFlow(
                process_definition_id=process_definition_id,
                flow_id=flow_id,
                name=name,
                source_element_id=source,
                target_element_id=target,
                condition_expression=condition
            )
            flows.append(flow)
        
        return flows


### 2. 流程执行引擎

创建 `api/app/engine/bpmn/executor.py`：

```python
"""BPMN 流程执行引擎"""

from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.bpm import (
    ProcessInstance,
    ProcessStatus,
    Task,
    TaskStatus,
    TaskType
)
from app.models.bpm.element import (
    ProcessElement,
    SequenceFlow,
    ExecutionToken,
    ElementType
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class BPMNExecutor:
    """BPMN 流程执行器"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def start_process(
        self,
        process_instance_id: UUID
    ) -> None:
        """启动流程实例"""
        # 1. 获取流程实例
        instance = await self._get_process_instance(process_instance_id)
        
        # 2. 查找开始事件
        start_event = await self._find_start_event(
            instance.process_definition_id
        )
        
        if not start_event:
            raise ValueError("No start event found in process definition")
        
        # 3. 创建初始执行令牌
        token = ExecutionToken(
            process_instance_id=process_instance_id,
            current_element_id=start_event.element_id,
            is_active=True
        )
        self.session.add(token)
        await self.session.commit()
        
        # 4. 执行开始事件
        await self._execute_element(token, start_event, instance)
    
    async def _execute_element(
        self,
        token: ExecutionToken,
        element: ProcessElement,
        instance: ProcessInstance
    ) -> None:
        """执行元素"""
        logger.info(
            "Executing element",
            element_id=element.element_id,
            element_type=element.element_type
        )
        
        # 根据元素类型执行
        if element.element_type == ElementType.START_EVENT:
            await self._execute_start_event(token, element, instance)
        
        elif element.element_type == ElementType.END_EVENT:
            await self._execute_end_event(token, element, instance)
        
        elif element.element_type == ElementType.USER_TASK:
            await self._execute_user_task(token, element, instance)
        
        elif element.element_type == ElementType.SERVICE_TASK:
            await self._execute_service_task(token, element, instance)
        
        elif element.element_type == ElementType.SCRIPT_TASK:
            await self._execute_script_task(token, element, instance)
        
        elif element.element_type == ElementType.EXCLUSIVE_GATEWAY:
            await self._execute_exclusive_gateway(token, element, instance)
        
        elif element.element_type == ElementType.PARALLEL_GATEWAY:
            await self._execute_parallel_gateway(token, element, instance)
        
        else:
            logger.warning(
                "Unsupported element type",
                element_type=element.element_type
            )
    
    async def _execute_start_event(
        self,
        token: ExecutionToken,
        element: ProcessElement,
        instance: ProcessInstance
    ) -> None:
        """执行开始事件"""
        # 开始事件直接流转到下一个元素
        await self._move_token_forward(token, element, instance)
    
    async def _execute_end_event(
        self,
        token: ExecutionToken,
        element: ProcessElement,
        instance: ProcessInstance
    ) -> None:
        """执行结束事件"""
        # 标记令牌为完成
        token.is_active = False
        token.completed_at = datetime.utcnow()
        self.session.add(token)
        
        # 检查是否所有令牌都已完成
        active_tokens = await self._get_active_tokens(instance.id)
        if not active_tokens:
            # 流程结束
            instance.status = ProcessStatus.COMPLETED
            instance.ended_at = datetime.utcnow()
            self.session.add(instance)
        
        await self.session.commit()
    
    async def _execute_user_task(
        self,
        token: ExecutionToken,
        element: ProcessElement,
        instance: ProcessInstance
    ) -> None:
        """执行用户任务"""
        # 创建任务
        task = Task(
            workspace_id=instance.workspace_id,
            process_instance_id=instance.id,
            name=element.name,
            task_type=TaskType.USER_TASK,
            status=TaskStatus.PENDING,
            candidate_users=element.config.get('candidate_users', []),
            candidate_groups=element.config.get('candidate_groups', [])
        )
        
        # 如果指定了 assignee，直接分配
        assignee = element.config.get('assignee')
        if assignee:
            task.assignee = UUID(assignee)
            task.status = TaskStatus.ASSIGNED
        
        self.session.add(task)
        
        # 令牌进入等待状态
        token.is_waiting = True
        self.session.add(token)
        
        await self.session.commit()
        
        logger.info("User task created", task_id=str(task.id))
    
    async def complete_user_task(
        self,
        task_id: UUID,
        result: Dict[str, Any]
    ) -> None:
        """完成用户任务"""
        # 1. 获取任务
        task = await self._get_task(task_id)
        
        # 2. 更新任务状态
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.form_data = result
        self.session.add(task)
        
        # 3. 获取对应的令牌
        token = await self._get_waiting_token(
            task.process_instance_id,
            task.name  # 假设任务名称与元素名称一致
        )
        
        if token:
            # 4. 继续执行
            token.is_waiting = False
            self.session.add(token)
            await self.session.commit()
            
            # 5. 移动到下一个元素
            instance = await self._get_process_instance(task.process_instance_id)
            element = await self._get_element_by_id(
                instance.process_definition_id,
                token.current_element_id
            )
            await self._move_token_forward(token, element, instance)
    
    async def _execute_exclusive_gateway(
        self,
        token: ExecutionToken,
        element: ProcessElement,
        instance: ProcessInstance
    ) -> None:
        """执行排他网关"""
        # 1. 获取所有出口流
        outgoing_flows = await self._get_outgoing_flows(
            element.process_definition_id,
            element.element_id
        )
        
        # 2. 评估条件，选择一条流
        selected_flow = None
        default_flow_id = element.config.get('default_flow')
        
        for flow in outgoing_flows:
            if flow.condition_expression:
                # 评估条件表达式
                if await self._evaluate_condition(
                    flow.condition_expression,
                    instance.variables
                ):
                    selected_flow = flow
                    break
            elif flow.flow_id == default_flow_id:
                # 记录默认流
                selected_flow = flow
        
        if not selected_flow and default_flow_id:
            # 使用默认流
            selected_flow = next(
                (f for f in outgoing_flows if f.flow_id == default_flow_id),
                None
            )
        
        if not selected_flow:
            raise ValueError("No valid outgoing flow found for exclusive gateway")
        
        # 3. 移动令牌到目标元素
        target_element = await self._get_element_by_id(
            element.process_definition_id,
            selected_flow.target_element_id
        )
        
        token.current_element_id = target_element.element_id
        self.session.add(token)
        await self.session.commit()
        
        # 4. 执行目标元素
        await self._execute_element(token, target_element, instance)
    
    async def _execute_parallel_gateway(
        self,
        token: ExecutionToken,
        element: ProcessElement,
        instance: ProcessInstance
    ) -> None:
        """执行并行网关"""
        # 1. 获取所有出口流
        outgoing_flows = await self._get_outgoing_flows(
            element.process_definition_id,
            element.element_id
        )
        
        # 2. 为每条出口流创建新令牌
        for flow in outgoing_flows:
            target_element = await self._get_element_by_id(
                element.process_definition_id,
                flow.target_element_id
            )
            
            # 创建子令牌
            child_token = ExecutionToken(
                process_instance_id=instance.id,
                current_element_id=target_element.element_id,
                parent_token_id=token.id,
                is_active=True
            )
            self.session.add(child_token)
            await self.session.commit()
            
            # 执行目标元素
            await self._execute_element(child_token, target_element, instance)
        
        # 3. 父令牌完成
        token.is_active = False
        token.completed_at = datetime.utcnow()
        self.session.add(token)
        await self.session.commit()
    
    async def _move_token_forward(
        self,
        token: ExecutionToken,
        current_element: ProcessElement,
        instance: ProcessInstance
    ) -> None:
        """移动令牌到下一个元素"""
        # 1. 获取出口流
        outgoing_flows = await self._get_outgoing_flows(
            current_element.process_definition_id,
            current_element.element_id
        )
        
        if not outgoing_flows:
            logger.warning(
                "No outgoing flows found",
                element_id=current_element.element_id
            )
            return
        
        # 2. 获取目标元素（假设只有一条流）
        flow = outgoing_flows[0]
        target_element = await self._get_element_by_id(
            current_element.process_definition_id,
            flow.target_element_id
        )
        
        # 3. 更新令牌位置
        token.current_element_id = target_element.element_id
        self.session.add(token)
        await self.session.commit()
        
        # 4. 执行目标元素
        await self._execute_element(token, target_element, instance)
    
    async def _evaluate_condition(
        self,
        expression: str,
        variables: Dict[str, Any]
    ) -> bool:
        """评估条件表达式"""
        try:
            # 简单的表达式评估（生产环境应使用更安全的方式）
            return eval(expression, {"__builtins__": {}}, variables)
        except Exception as e:
            logger.error(
                "Failed to evaluate condition",
                expression=expression,
                error=str(e)
            )
            return False
    
    # ... 辅助方法 ...
```

---

