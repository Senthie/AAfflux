# Camunda 集成方案

## 📋 方案概述

本方案提供将 Camunda BPM 引擎集成到当前 FastAPI 项目的完整实施方案，包括架构设计、集成方式、数据同步和API设计。

---

## 🏗️ 集成架构

### 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              BPM Service Layer                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │ Process    │  │ Task       │  │ Approval   │     │  │
│  │  │ Service    │  │ Service    │  │ Service    │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Camunda Client (REST API)                   │  │
│  │  - Process Deployment                                 │  │
│  │  - Process Instance Management                        │  │
│  │  - Task Management                                    │  │
│  │  - Variable Management                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Local BPM Models                         │  │
│  │  - ProcessDefinition (元数据)                         │  │
│  │  - ProcessInstance (状态同步)                         │  │
│  │  - Task (任务同步)                                    │  │
│  │  - Approval (业务扩展)                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                  Camunda BPM Platform                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Camunda Engine                           │  │
│  │  - BPMN 2.0 Execution                                 │  │
│  │  - Process Engine API                                 │  │
│  │  - Job Executor                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Camunda Database                         │  │
│  │  - Process Definitions                                │  │
│  │  - Process Instances                                  │  │
│  │  - Tasks                                              │  │
│  │  - Variables                                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2. 集成模式选择

**推荐：REST API 集成模式** ✅

**优点**：
- 技术栈独立（Python + Java）
- 部署灵活（可独立扩展）
- 维护简单（各自独立升级）
- 故障隔离（Camunda故障不影响主应用）

**缺点**：
- 网络延迟
- 需要数据同步

---

## 🔧 实施步骤

### 步骤1：部署 Camunda Platform（1周）

#### 1.1 Docker Compose 部署

创建 `docker-compose.camunda.yml`：

```yaml
version: '3.8'

services:
  camunda:
    image: camunda/camunda-bpm-platform:7.20.0
    container_name: camunda-bpm
    ports:
      - "8080:8080"  # Camunda Web Apps
      - "8000:8000"  # Debug port
    environment:
      - DB_DRIVER=org.postgresql.Driver
      - DB_URL=jdbc:postgresql://postgres:5432/camunda
      - DB_USERNAME=camunda
      - DB_PASSWORD=camunda
      - WAIT_FOR=postgres:5432
    depends_on:
      - postgres
    networks:
      - app-network
    volumes:
      - camunda-data:/camunda/configuration
    restart: unless-stopped

  postgres:
    image: postgres:15
    container_name: camunda-postgres
    environment:
      - POSTGRES_DB=camunda
      - POSTGRES_USER=camunda
      - POSTGRES_PASSWORD=camunda
    ports:
      - "5433:5432"  # 避免与主数据库冲突
    volumes:
      - camunda-postgres-data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped

volumes:
  camunda-data:
  camunda-postgres-data:

networks:
  app-network:
    external: true
```

启动命令：
```bash
docker-compose -f docker-compose.camunda.yml up -d
```

访问 Camunda Web Apps：
- URL: http://localhost:8080/camunda
- 默认账号: demo / demo

#### 1.2 验证部署

```bash
# 检查 Camunda 健康状态
curl http://localhost:8080/engine-rest/engine

# 预期响应
[
  {
    "name": "default"
  }
]
```

---

### 步骤2：开发 Camunda Client（2周）

#### 2.1 安装依赖

```bash
cd api
uv add httpx pydantic-settings
```

#### 2.2 创建 Camunda Client

创建 `api/app/integrations/camunda/client.py`：

```python
"""Camunda REST API Client"""

import httpx
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CamundaConfig(BaseModel):
    """Camunda 配置"""
    base_url: str = "http://localhost:8080/engine-rest"
    timeout: int = 30
    username: Optional[str] = None
    password: Optional[str] = None


class CamundaClient:
    """Camunda REST API 客户端"""
    
    def __init__(self, config: Optional[CamundaConfig] = None):
        self.config = config or CamundaConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            auth=(self.config.username, self.config.password) 
                 if self.config.username else None
        )
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
    
    # ==================== Process Definition ====================
    
    async def deploy_process(
        self,
        deployment_name: str,
        bpmn_xml: str,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        部署流程定义
        
        Args:
            deployment_name: 部署名称
            bpmn_xml: BPMN XML 内容
            tenant_id: 租户ID（可选）
        
        Returns:
            部署信息
        """
        files = {
            'deployment-name': (None, deployment_name),
            'deployment-source': (None, 'python-api'),
            'deploy-changed-only': (None, 'true'),
            'data': ('process.bpmn', bpmn_xml, 'text/xml')
        }
        
        if tenant_id:
            files['tenant-id'] = (None, tenant_id)
        
        response = await self.client.post(
            '/deployment/create',
            files=files
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(
            "Process deployed",
            deployment_id=result.get('id'),
            deployment_name=deployment_name
        )
        return result
    
    async def get_process_definition(
        self,
        process_definition_key: str,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取流程定义"""
        params = {'key': process_definition_key}
        if tenant_id:
            params['tenantId'] = tenant_id
        
        response = await self.client.get(
            '/process-definition',
            params=params
        )
        response.raise_for_status()
        
        definitions = response.json()
        if not definitions:
            raise ValueError(f"Process definition not found: {process_definition_key}")
        
        # 返回最新版本
        return definitions[0]
    
    async def get_process_definition_xml(
        self,
        process_definition_id: str
    ) -> str:
        """获取流程定义的 BPMN XML"""
        response = await self.client.get(
            f'/process-definition/{process_definition_id}/xml'
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get('bpmn20Xml', '')
    
    # ==================== Process Instance ====================
    
    async def start_process_instance(
        self,
        process_definition_key: str,
        business_key: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        启动流程实例
        
        Args:
            process_definition_key: 流程定义Key
            business_key: 业务Key
            variables: 流程变量
            tenant_id: 租户ID
        
        Returns:
            流程实例信息
        """
        payload = {
            'businessKey': business_key,
            'variables': self._format_variables(variables or {})
        }
        
        if tenant_id:
            payload['tenantId'] = tenant_id
        
        response = await self.client.post(
            f'/process-definition/key/{process_definition_key}/start',
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(
            "Process instance started",
            process_instance_id=result.get('id'),
            process_definition_key=process_definition_key
        )
        return result
    
    async def get_process_instance(
        self,
        process_instance_id: str
    ) -> Dict[str, Any]:
        """获取流程实例"""
        response = await self.client.get(
            f'/process-instance/{process_instance_id}'
        )
        response.raise_for_status()
        return response.json()
    
    async def delete_process_instance(
        self,
        process_instance_id: str,
        reason: Optional[str] = None
    ) -> None:
        """删除（取消）流程实例"""
        params = {}
        if reason:
            params['deleteReason'] = reason
        
        response = await self.client.delete(
            f'/process-instance/{process_instance_id}',
            params=params
        )
        response.raise_for_status()
        
        logger.info(
            "Process instance deleted",
            process_instance_id=process_instance_id,
            reason=reason
        )
    
    async def get_process_variables(
        self,
        process_instance_id: str
    ) -> Dict[str, Any]:
        """获取流程变量"""
        response = await self.client.get(
            f'/process-instance/{process_instance_id}/variables'
        )
        response.raise_for_status()
        
        variables = response.json()
        return self._parse_variables(variables)
    
    async def set_process_variables(
        self,
        process_instance_id: str,
        variables: Dict[str, Any]
    ) -> None:
        """设置流程变量"""
        payload = {
            'modifications': self._format_variables(variables)
        }
        
        response = await self.client.post(
            f'/process-instance/{process_instance_id}/variables',
            json=payload
        )
        response.raise_for_status()
    
    # ==================== Task ====================
    
    async def get_tasks(
        self,
        assignee: Optional[str] = None,
        candidate_user: Optional[str] = None,
        candidate_group: Optional[str] = None,
        process_instance_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """查询任务列表"""
        params = {}
        if assignee:
            params['assignee'] = assignee
        if candidate_user:
            params['candidateUser'] = candidate_user
        if candidate_group:
            params['candidateGroup'] = candidate_group
        if process_instance_id:
            params['processInstanceId'] = process_instance_id
        if tenant_id:
            params['tenantId'] = tenant_id
        
        response = await self.client.get('/task', params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """获取任务详情"""
        response = await self.client.get(f'/task/{task_id}')
        response.raise_for_status()
        return response.json()
    
    async def claim_task(self, task_id: str, user_id: str) -> None:
        """认领任务"""
        payload = {'userId': user_id}
        response = await self.client.post(
            f'/task/{task_id}/claim',
            json=payload
        )
        response.raise_for_status()
        
        logger.info("Task claimed", task_id=task_id, user_id=user_id)
    
    async def complete_task(
        self,
        task_id: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> None:
        """完成任务"""
        payload = {
            'variables': self._format_variables(variables or {})
        }
        
        response = await self.client.post(
            f'/task/{task_id}/complete',
            json=payload
        )
        response.raise_for_status()
        
        logger.info("Task completed", task_id=task_id)
    
    # ==================== Helper Methods ====================
    
    def _format_variables(self, variables: Dict[str, Any]) -> Dict[str, Dict]:
        """格式化变量为 Camunda 格式"""
        formatted = {}
        for key, value in variables.items():
            formatted[key] = {
                'value': value,
                'type': self._get_variable_type(value)
            }
        return formatted
    
    def _parse_variables(self, variables: Dict[str, Dict]) -> Dict[str, Any]:
        """解析 Camunda 变量格式"""
        parsed = {}
        for key, var_info in variables.items():
            parsed[key] = var_info.get('value')
        return parsed
    
    def _get_variable_type(self, value: Any) -> str:
        """获取变量类型"""
        if isinstance(value, bool):
            return 'Boolean'
        elif isinstance(value, int):
            return 'Integer'
        elif isinstance(value, float):
            return 'Double'
        elif isinstance(value, str):
            return 'String'
        elif isinstance(value, (dict, list)):
            return 'Json'
        else:
            return 'String'


# 全局客户端实例
camunda_client: Optional[CamundaClient] = None


async def get_camunda_client() -> CamundaClient:
    """获取 Camunda 客户端实例"""
    global camunda_client
    if camunda_client is None:
        camunda_client = CamundaClient()
    return camunda_client


async def close_camunda_client():
    """关闭 Camunda 客户端"""
    global camunda_client
    if camunda_client:
        await camunda_client.close()
        camunda_client = None
```

---

### 步骤3：改造现有 BPM 模型（1周）

#### 3.1 修改 ProcessDefinition 模型

修改 `api/app/models/bpm/process.py`：

```python
"""BPM 流程模型 - 与 Camunda 集成版本"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Column, JSON
from enum import Enum


class ProcessEngine(str, Enum):
    """流程引擎类型"""
    INTERNAL = "internal"  # 内部引擎
    CAMUNDA = "camunda"    # Camunda 引擎


class ProcessDefinition(SQLModel, table=True):
    """流程定义表 - 存储元数据和 Camunda 映射"""
    
    __tablename__ = "bpm_process_definitions"
    
    # 主键
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # 租户隔离
    workspace_id: UUID = Field(foreign_key="workspaces.id", index=True)
    
    # 流程基本信息
    key: str = Field(max_length=255, index=True)  # 流程Key（唯一标识）
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    category: Optional[str] = Field(max_length=100, default=None)
    
    # 引擎信息 ⭐ 新增
    engine: ProcessEngine = Field(default=ProcessEngine.CAMUNDA)
    
    # Camunda 集成信息 ⭐ 新增
    camunda_deployment_id: Optional[str] = Field(default=None, max_length=255)
    camunda_definition_id: Optional[str] = Field(default=None, max_length=255)
    camunda_definition_key: Optional[str] = Field(default=None, max_length=255)
    
    # 流程定义内容
    bpmn_xml: Optional[str] = Field(default=None)  # BPMN 2.0 XML
    diagram_svg: Optional[str] = Field(default=None)  # 流程图 SVG
    
    # 版本控制
    version: int = Field(default=1)
    is_latest: bool = Field(default=True)
    
    # 状态
    status: str = Field(max_length=50, default="draft")  # draft, published, archived
    
    # 配置
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # 审计字段
    created_by: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = Field(default=None)


class ProcessInstance(SQLModel, table=True):
    """流程实例表 - 与 Camunda 同步"""
    
    __tablename__ = "bpm_process_instances"
    
    # 主键
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # 租户隔离
    workspace_id: UUID = Field(foreign_key="workspaces.id", index=True)
    
    # 流程定义
    process_definition_id: UUID = Field(foreign_key="bpm_process_definitions.id")
    
    # Camunda 集成信息 ⭐ 新增
    camunda_instance_id: Optional[str] = Field(default=None, max_length=255, index=True)
    camunda_business_key: Optional[str] = Field(default=None, max_length=255)
    
    # 业务信息
    business_key: str = Field(max_length=255, index=True)
    title: str = Field(max_length=500)
    
    # 状态
    status: ProcessStatus = Field(default=ProcessStatus.RUNNING)
    
    # 流程变量
    variables: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # 执行信息
    current_node: Optional[str] = Field(default=None, max_length=255)
    
    # 审计字段
    started_by: UUID = Field(foreign_key="users.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = Field(default=None)
    
    # 同步信息 ⭐ 新增
    last_synced_at: Optional[datetime] = Field(default=None)
```

#### 3.2 修改 Task 模型

```python
class Task(SQLModel, table=True):
    """任务表 - 与 Camunda 同步"""
    
    __tablename__ = "bpm_tasks"
    
    # 主键
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # 租户隔离
    workspace_id: UUID = Field(foreign_key="workspaces.id", index=True)
    
    # 流程实例
    process_instance_id: UUID = Field(foreign_key="bpm_process_instances.id")
    
    # Camunda 集成信息 ⭐ 新增
    camunda_task_id: Optional[str] = Field(default=None, max_length=255, index=True)
    camunda_task_definition_key: Optional[str] = Field(default=None, max_length=255)
    
    # 任务信息
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    task_type: TaskType = Field(default=TaskType.USER_TASK)
    
    # 分配信息
    assignee: Optional[UUID] = Field(default=None, foreign_key="users.id")
    candidate_users: list = Field(default_factory=list, sa_column=Column(JSON))
    candidate_groups: list = Field(default_factory=list, sa_column=Column(JSON))
    
    # 状态
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    
    # 表单数据
    form_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # 时间信息
    due_date: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    claimed_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    
    # 同步信息 ⭐ 新增
    last_synced_at: Optional[datetime] = Field(default=None)
```

---

### 步骤4：开发同步服务（2周）

#### 4.1 创建同步服务

创建 `api/app/services/bpm_sync_service.py`：

```python
"""BPM 同步服务 - 与 Camunda 数据同步"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.bpm import (
    ProcessDefinition,
    ProcessInstance,
    ProcessStatus,
    Task,
    TaskStatus
)
from app.integrations.camunda.client import get_camunda_client
from app.core.logging import get_logger

logger = get_logger(__name__)


class BPMSyncService:
    """BPM 同步服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ==================== Process Definition Sync ====================
    
    async def deploy_to_camunda(
        self,
        process_definition_id: UUID
    ) -> ProcessDefinition:
        """
        将流程定义部署到 Camunda
        
        Args:
            process_definition_id: 流程定义ID
        
        Returns:
            更新后的流程定义
        """
        # 1. 获取流程定义
        result = await self.session.execute(
            select(ProcessDefinition).where(
                ProcessDefinition.id == process_definition_id
            )
        )
        process_def = result.scalar_one_or_none()
        if not process_def:
            raise ValueError(f"Process definition not found: {process_definition_id}")
        
        if not process_def.bpmn_xml:
            raise ValueError("BPMN XML is required for deployment")
        
        # 2. 部署到 Camunda
        camunda = await get_camunda_client()
        deployment = await camunda.deploy_process(
            deployment_name=f"{process_def.name}_v{process_def.version}",
            bpmn_xml=process_def.bpmn_xml,
            tenant_id=str(process_def.workspace_id)
        )
        
        # 3. 更新流程定义
        process_def.camunda_deployment_id = deployment['id']
        
        # 获取部署的流程定义信息
        deployed_definitions = deployment.get('deployedProcessDefinitions', {})
        if deployed_definitions:
            first_def = list(deployed_definitions.values())[0]
            process_def.camunda_definition_id = first_def['id']
            process_def.camunda_definition_key = first_def['key']
        
        process_def.status = "published"
        process_def.published_at = datetime.utcnow()
        
        self.session.add(process_def)
        await self.session.commit()
        await self.session.refresh(process_def)
        
        logger.info(
            "Process definition deployed to Camunda",
            process_definition_id=str(process_definition_id),
            camunda_deployment_id=process_def.camunda_deployment_id
        )
        
        return process_def
    
    # ==================== Process Instance Sync ====================
    
    async def start_process_in_camunda(
        self,
        process_instance_id: UUID
    ) -> ProcessInstance:
        """
        在 Camunda 中启动流程实例
        
        Args:
            process_instance_id: 流程实例ID
        
        Returns:
            更新后的流程实例
        """
        # 1. 获取流程实例
        result = await self.session.execute(
            select(ProcessInstance).where(
                ProcessInstance.id == process_instance_id
            )
        )
        instance = result.scalar_one_or_none()
        if not instance:
            raise ValueError(f"Process instance not found: {process_instance_id}")
        
        # 2. 获取流程定义
        result = await self.session.execute(
            select(ProcessDefinition).where(
                ProcessDefinition.id == instance.process_definition_id
            )
        )
        process_def = result.scalar_one_or_none()
        if not process_def or not process_def.camunda_definition_key:
            raise ValueError("Process definition not deployed to Camunda")
        
        # 3. 在 Camunda 中启动流程
        camunda = await get_camunda_client()
        camunda_instance = await camunda.start_process_instance(
            process_definition_key=process_def.camunda_definition_key,
            business_key=instance.business_key,
            variables=instance.variables,
            tenant_id=str(instance.workspace_id)
        )
        
        # 4. 更新流程实例
        instance.camunda_instance_id = camunda_instance['id']
        instance.camunda_business_key = camunda_instance.get('businessKey')
        instance.status = ProcessStatus.RUNNING
        instance.last_synced_at = datetime.utcnow()
        
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        
        logger.info(
            "Process instance started in Camunda",
            process_instance_id=str(process_instance_id),
            camunda_instance_id=instance.camunda_instance_id
        )
        
        return instance
    
    async def sync_process_instance_from_camunda(
        self,
        process_instance_id: UUID
    ) -> ProcessInstance:
        """从 Camunda 同步流程实例状态"""
        # 1. 获取本地流程实例
        result = await self.session.execute(
            select(ProcessInstance).where(
                ProcessInstance.id == process_instance_id
            )
        )
        instance = result.scalar_one_or_none()
        if not instance or not instance.camunda_instance_id:
            raise ValueError("Process instance not found or not in Camunda")
        
        # 2. 从 Camunda 获取状态
        camunda = await get_camunda_client()
        try:
            camunda_instance = await camunda.get_process_instance(
                instance.camunda_instance_id
            )
            
            # 流程仍在运行
            instance.status = ProcessStatus.RUNNING
            instance.last_synced_at = datetime.utcnow()
            
        except Exception as e:
            # 流程已结束（Camunda 中不存在）
            if "404" in str(e):
                instance.status = ProcessStatus.COMPLETED
                instance.ended_at = datetime.utcnow()
                instance.last_synced_at = datetime.utcnow()
            else:
                raise
        
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        
        return instance
    
    # ==================== Task Sync ====================
    
    async def sync_tasks_from_camunda(
        self,
        process_instance_id: UUID
    ) -> List[Task]:
        """从 Camunda 同步任务"""
        # 1. 获取流程实例
        result = await self.session.execute(
            select(ProcessInstance).where(
                ProcessInstance.id == process_instance_id
            )
        )
        instance = result.scalar_one_or_none()
        if not instance or not instance.camunda_instance_id:
            raise ValueError("Process instance not found or not in Camunda")
        
        # 2. 从 Camunda 获取任务
        camunda = await get_camunda_client()
        camunda_tasks = await camunda.get_tasks(
            process_instance_id=instance.camunda_instance_id
        )
        
        # 3. 同步任务
        synced_tasks = []
        for camunda_task in camunda_tasks:
            task = await self._sync_single_task(
                instance,
                camunda_task
            )
            synced_tasks.append(task)
        
        logger.info(
            "Tasks synced from Camunda",
            process_instance_id=str(process_instance_id),
            task_count=len(synced_tasks)
        )
        
        return synced_tasks
    
    async def _sync_single_task(
        self,
        instance: ProcessInstance,
        camunda_task: dict
    ) -> Task:
        """同步单个任务"""
        # 查找现有任务
        result = await self.session.execute(
            select(Task).where(
                Task.camunda_task_id == camunda_task['id']
            )
        )
        task = result.scalar_one_or_none()
        
        if not task:
            # 创建新任务
            task = Task(
                workspace_id=instance.workspace_id,
                process_instance_id=instance.id,
                camunda_task_id=camunda_task['id'],
                camunda_task_definition_key=camunda_task.get('taskDefinitionKey'),
                name=camunda_task['name'],
                description=camunda_task.get('description'),
                status=TaskStatus.PENDING
            )
        
        # 更新任务信息
        if camunda_task.get('assignee'):
            # TODO: 将 Camunda 用户ID映射到本地用户ID
            pass
        
        task.last_synced_at = datetime.utcnow()
        
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        
        return task
```

---

### 步骤5：改造 BPM Service（1周）

修改 `api/app/services/bpm_process_service.py`：

```python
"""BPM 流程服务 - Camunda 集成版本"""

from uuid import UUID
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.bpm import ProcessDefinition, ProcessInstance, ProcessEngine
from app.services.bpm_sync_service import BPMSyncService
from app.integrations.camunda.client import get_camunda_client


class ProcessService:
    """流程服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.sync_service = BPMSyncService(session)
    
    async def create_process_definition(
        self,
        workspace_id: UUID,
        key: str,
        name: str,
        bpmn_xml: str,
        engine: ProcessEngine = ProcessEngine.CAMUNDA,
        **kwargs
    ) -> ProcessDefinition:
        """创建流程定义"""
        process_def = ProcessDefinition(
            workspace_id=workspace_id,
            key=key,
            name=name,
            bpmn_xml=bpmn_xml,
            engine=engine,
            **kwargs
        )
        
        self.session.add(process_def)
        await self.session.commit()
        await self.session.refresh(process_def)
        
        return process_def
    
    async def publish_process_definition(
        self,
        process_definition_id: UUID
    ) -> ProcessDefinition:
        """发布流程定义（部署到 Camunda）"""
        return await self.sync_service.deploy_to_camunda(process_definition_id)
    
    async def start_process_instance(
        self,
        process_definition_id: UUID,
        business_key: str,
        title: str,
        variables: dict,
        started_by: UUID
    ) -> ProcessInstance:
        """启动流程实例"""
        # 1. 创建本地流程实例
        instance = ProcessInstance(
            workspace_id=workspace_id,
            process_definition_id=process_definition_id,
            business_key=business_key,
            title=title,
            variables=variables,
            started_by=started_by
        )
        
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        
        # 2. 在 Camunda 中启动
        instance = await self.sync_service.start_process_in_camunda(instance.id)
        
        # 3. 同步任务
        await self.sync_service.sync_tasks_from_camunda(instance.id)
        
        return instance
```

---

### 步骤6：配置和环境变量（0.5周）

#### 6.1 更新配置文件

修改 `api/app/core/config.py`：

```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # Camunda 配置
    camunda_base_url: str = Field(
        default="http://localhost:8080/engine-rest",
        env="CAMUNDA_BASE_URL"
    )
    camunda_username: Optional[str] = Field(default=None, env="CAMUNDA_USERNAME")
    camunda_password: Optional[str] = Field(default=None, env="CAMUNDA_PASSWORD")
    camunda_timeout: int = Field(default=30, env="CAMUNDA_TIMEOUT")
```

#### 6.2 更新 .env.example

```bash
# Camunda Configuration
CAMUNDA_BASE_URL=http://localhost:8080/engine-rest
CAMUNDA_USERNAME=demo
CAMUNDA_PASSWORD=demo
CAMUNDA_TIMEOUT=30
```

---

### 步骤7：数据库迁移（0.5周）

创建 Alembic 迁移脚本：

```bash
cd api
uv run alembic revision -m "add_camunda_integration_fields"
```

编辑生成的迁移文件：

```python
"""add camunda integration fields

Revision ID: xxx
"""

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # ProcessDefinition 表
    op.add_column('bpm_process_definitions', 
        sa.Column('engine', sa.String(50), nullable=False, server_default='camunda'))
    op.add_column('bpm_process_definitions', 
        sa.Column('camunda_deployment_id', sa.String(255), nullable=True))
    op.add_column('bpm_process_definitions', 
        sa.Column('camunda_definition_id', sa.String(255), nullable=True))
    op.add_column('bpm_process_definitions', 
        sa.Column('camunda_definition_key', sa.String(255), nullable=True))
    
    # ProcessInstance 表
    op.add_column('bpm_process_instances', 
        sa.Column('camunda_instance_id', sa.String(255), nullable=True))
    op.add_column('bpm_process_instances', 
        sa.Column('camunda_business_key', sa.String(255), nullable=True))
    op.add_column('bpm_process_instances', 
        sa.Column('last_synced_at', sa.DateTime(), nullable=True))
    
    op.create_index('idx_camunda_instance_id', 'bpm_process_instances', 
        ['camunda_instance_id'])
    
    # Task 表
    op.add_column('bpm_tasks', 
        sa.Column('camunda_task_id', sa.String(255), nullable=True))
    op.add_column('bpm_tasks', 
        sa.Column('camunda_task_definition_key', sa.String(255), nullable=True))
    op.add_column('bpm_tasks', 
        sa.Column('last_synced_at', sa.DateTime(), nullable=True))
    
    op.create_index('idx_camunda_task_id', 'bpm_tasks', ['camunda_task_id'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_camunda_task_id', 'bpm_tasks')
    op.drop_index('idx_camunda_instance_id', 'bpm_process_instances')
    
    # 删除列
    op.drop_column('bpm_tasks', 'last_synced_at')
    op.drop_column('bpm_tasks', 'camunda_task_definition_key')
    op.drop_column('bpm_tasks', 'camunda_task_id')
    
    op.drop_column('bpm_process_instances', 'last_synced_at')
    op.drop_column('bpm_process_instances', 'camunda_business_key')
    op.drop_column('bpm_process_instances', 'camunda_instance_id')
    
    op.drop_column('bpm_process_definitions', 'camunda_definition_key')
    op.drop_column('bpm_process_definitions', 'camunda_definition_id')
    op.drop_column('bpm_process_definitions', 'camunda_deployment_id')
    op.drop_column('bpm_process_definitions', 'engine')
```

执行迁移：

```bash
uv run alembic upgrade head
```

---

## 📝 使用示例

### 示例1：部署流程定义

```python
from app.services.bpm_process_service import ProcessService

# BPMN XML 示例
bpmn_xml = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
             targetNamespace="http://bpmn.io/schema/bpmn">
  <process id="approval_process" name="审批流程" isExecutable="true">
    <startEvent id="start" name="开始"/>
    <userTask id="review_task" name="审核任务"/>
    <endEvent id="end" name="结束"/>
    <sequenceFlow sourceRef="start" targetRef="review_task"/>
    <sequenceFlow sourceRef="review_task" targetRef="end"/>
  </process>
</definitions>
"""

# 1. 创建流程定义
process_def = await process_service.create_process_definition(
    workspace_id=workspace_id,
    key="approval_process",
    name="审批流程",
    bpmn_xml=bpmn_xml,
    engine=ProcessEngine.CAMUNDA
)

# 2. 发布到 Camunda
process_def = await process_service.publish_process_definition(process_def.id)

print(f"Deployed to Camunda: {process_def.camunda_deployment_id}")
```

### 示例2：启动流程实例

```python
# 启动流程
instance = await process_service.start_process_instance(
    process_definition_id=process_def.id,
    business_key="REQ-2024-001",
    title="采购申请审批",
    variables={
        "amount": 10000,
        "applicant": "张三",
        "department": "IT部门"
    },
    started_by=user_id
)

print(f"Process started in Camunda: {instance.camunda_instance_id}")
```

### 示例3：处理任务

```python
from app.services.bpm_task_service import TaskService

# 1. 获取我的待办任务
tasks = await task_service.get_my_tasks(user_id)

# 2. 认领任务
task = tasks[0]
await task_service.claim_task(task.id, user_id)

# 3. 完成任务
await task_service.complete_task(
    task.id,
    result={
        "approved": True,
        "comment": "同意"
    }
)
```

---

## 🔄 数据同步策略

### 1. 实时同步（推荐）

```python
# 在关键操作后立即同步
async def complete_task(task_id: UUID, result: dict):
    # 1. 在 Camunda 中完成任务
    await camunda.complete_task(task.camunda_task_id, result)
    
    # 2. 更新本地状态
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    
    # 3. 同步流程实例状态
    await sync_service.sync_process_instance_from_camunda(
        task.process_instance_id
    )
    
    # 4. 同步新任务
    await sync_service.sync_tasks_from_camunda(
        task.process_instance_id
    )
```

### 2. 定时同步（补充）

创建 Celery 定时任务：

```python
from celery import shared_task

@shared_task
def sync_active_processes():
    """定时同步活跃流程"""
    # 查询所有运行中的流程
    # 逐个同步状态
    pass

# 配置定时任务（每5分钟）
app.conf.beat_schedule = {
    'sync-active-processes': {
        'task': 'app.tasks.sync_active_processes',
        'schedule': 300.0,  # 5分钟
    },
}
```

---

## ⚠️ 注意事项

### 1. 用户映射

Camunda 和本地系统的用户ID需要映射：

```python
class UserMappingService:
    """用户映射服务"""
    
    async def get_camunda_user_id(self, local_user_id: UUID) -> str:
        """本地用户ID → Camunda用户ID"""
        # 可以使用用户的 email 或创建映射表
        user = await self.get_user(local_user_id)
        return user.email
    
    async def get_local_user_id(self, camunda_user_id: str) -> UUID:
        """Camunda用户ID → 本地用户ID"""
        user = await self.get_user_by_email(camunda_user_id)
        return user.id
```

### 2. 租户隔离

确保 Camunda 中的租户ID与本地 workspace_id 一致：

```python
# 使用 workspace_id 作为 Camunda 的 tenant_id
tenant_id = str(workspace_id)
```

### 3. 错误处理

```python
try:
    await camunda.complete_task(task_id, variables)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        # 任务在 Camunda 中不存在，可能已被删除
        logger.warning("Task not found in Camunda", task_id=task_id)
    else:
        raise
```

---

## 📊 监控和运维

### 1. 健康检查

```python
@app.get("/health/camunda")
async def camunda_health_check():
    """Camunda 健康检查"""
    try:
        camunda = await get_camunda_client()
        engines = await camunda.client.get('/engine')
        return {"status": "healthy", "engines": engines.json()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### 2. 同步状态监控

```python
# 记录同步延迟
sync_delay = datetime.utcnow() - instance.last_synced_at
if sync_delay.total_seconds() > 300:  # 5分钟
    logger.warning(
        "Process instance sync delayed",
        instance_id=str(instance.id),
        delay_seconds=sync_delay.total_seconds()
    )
```

---

## 🎯 总结

### 集成优势

1. **功能完整**：获得完整的 BPMN 2.0 支持
2. **可视化设计**：使用 Camunda Modeler 设计流程
3. **成熟稳定**：Camunda 是经过验证的企业级引擎
4. **灵活扩展**：保留本地数据，可添加业务逻辑

### 实施时间线

- 第1周：部署 Camunda 和开发 Client
- 第2周：改造模型和开发同步服务
- 第3周：改造 Service 和 API
- 第4周：测试和优化
- 第5周：文档和培训

### 后续优化

1. 实现 Camunda 外部任务（External Task）模式
2. 集成 Camunda Cockpit 监控界面
3. 实现流程版本管理和灰度发布
4. 优化同步性能和错误恢复

