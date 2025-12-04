"""计费和订阅模型 - 2张表。

本模块定义了计费和订阅管理的数据模型。
支持订阅计划、用量追踪和计费统计。
"""

from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlmodel import Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from decimal import Decimal
from app.models.base import BaseModel, TimestampMixin, WorkspaceMixin


class Subscription(BaseModel, TimestampMixin, WorkspaceMixin, table=True):
    """订阅表 - 租户订阅管理。

    管理工作空间的订阅计划和配额限制。
    支持不同的订阅级别和计费周期。

    Attributes:
    已经继承
        id: 订阅记录唯一标识符（UUID）
        workspace_id: 所属工作空间ID（逻辑外键，租户隔离）
        created_at: 创建时间
        updated_at: 更新时间

        plan_type: 订阅计划类型（free-免费/starter-入门/pro-专业/enterprise-企业）
        plan_name: 计划名称
        status: 订阅状态（active-活跃/cancelled-已取消/expired-已过期/suspended-已暂停）
        billing_cycle: 计费周期（monthly-月付/yearly-年付/lifetime-终身）
        price: 订阅价格
        currency: 货币单位（USD/CNY等）
        quota_limits: 配额限制（JSONB格式）
            - api_calls_per_month: 每月API调用次数
            - tokens_per_month: 每月Token额度
            - storage_gb: 存储空间（GB）
            - team_members: 团队成员数量
            - workflows: 工作流数量
            - datasets: 知识库数量
            - messages_per_month: 每月消息数量
            - custom_plugins: 是否支持自定义插件
        current_period_start: 当前周期开始时间
        current_period_end: 当前周期结束时间
        trial_end: 试用期结束时间
        cancel_at_period_end: 是否在周期结束时取消
        cancelled_at: 取消时间


    业务规则：
        - 每个工作空间有一个活跃订阅
        - 订阅到期后自动续费或降级到免费版
        - 配额限制根据订阅计划动态调整
        - 支持试用期管理
    """

    __tablename__ = "subscriptions"

    plan_type: str = Field(max_length=50, index=True)  # free, starter, pro, enterprise
    plan_name: str = Field(max_length=100)
    status: str = Field(max_length=20, index=True)  # active, cancelled, expired, suspended
    billing_cycle: str = Field(max_length=20)  # monthly, yearly, lifetime
    price: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)
    currency: str = Field(max_length=10, default="USD")
    quota_limits: dict = Field(sa_column=Column(JSONB))  # 配额限制
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool = Field(default=False)
    cancelled_at: Optional[datetime] = None


class UsageRecord(BaseModel, WorkspaceMixin, table=True):
    """用量记录表 - 资源使用追踪。

    记录工作空间的资源使用情况，用于计费和配额控制。
    支持多种资源类型的用量统计。

    Attributes:
    已经继承
        id: 用量记录唯一标识符（UUID）
        workspace_id: 所属工作空间ID（逻辑外键，租户隔离）


        subscription_id: 订阅ID（逻辑外键）
        resource_type: 资源类型（api_call-API调用/token-Token/storage-存储/message-消息/workflow_execution-工作流执行）
        resource_name: 资源名称（具体的资源标识）
        quantity: 使用数量
        unit: 计量单位（count-次数/token-Token/gb-GB/mb-MB）
        cost: 费用（如果有）
        metadata: 额外元数据（JSONB格式）
            - application_id: 关联的应用ID
            - end_user_id: 关联的终端用户ID
            - model_name: 使用的模型名称
            - execution_id: 执行记录ID
        recorded_at: 记录时间
        period_start: 统计周期开始时间
        period_end: 统计周期结束时间

    业务规则：
        - 实时记录资源使用
        - 按周期汇总统计
        - 用于配额检查和超限告警
        - 支持详细的成本分析
    """

    __tablename__ = "usage_records"

    subscription_id: UUID = Field(index=True)  # Logical FK to subscriptions
    resource_type: str = Field(
        max_length=50, index=True
    )  # api_call, token, storage, message, workflow_execution
    resource_name: Optional[str] = Field(default=None, max_length=255)
    quantity: Decimal = Field(max_digits=20, decimal_places=4)
    unit: str = Field(max_length=20)  # count, token, gb, mb
    cost: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=4)
    custom_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    recorded_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    period_start: datetime = Field(index=True)
    period_end: datetime = Field(index=True)
