"""元数据模型定义"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlmodel import Field, Column, JSON, Relationship
from enum import Enum

from app.models.base import BaseModel, TimestampMixin, AuditMixin, WorkspaceMixin


class ModelStatus(str, Enum):
    """模型状态"""

    DRAFT = "draft"  # 草稿
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"  # 已归档


class FieldType(str, Enum):
    """字段类型"""

    # 基本类型
    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"

    # 特殊类型
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    JSON = "json"
    UUID = "uuid"

    # 关系类型
    FOREIGN_KEY = "foreign_key"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"


class MetadataModel(BaseModel, TimestampMixin, AuditMixin, WorkspaceMixin, table=True):
    """数据模型元数据表

    存储用户定义的数据模型信息，支持动态创建数据库表和 API。

    Attributes:
        继承字段:
            id: 模型唯一标识符（UUID）
            workspace_id: 所属工作空间ID（租户隔离）
            created_by: 创建者用户ID
            created_at: 创建时间
            updated_at: 更新时间

        业务字段:
            name: 模型名称（英文，如 customer）
            display_name: 显示名称（中文，如 客户）
            description: 模型描述
            table_name: 数据库表名
            schema_definition: JSON Schema 定义
            version: 版本号
            is_latest: 是否最新版本
            status: 模型状态（draft/published/archived）
            enable_audit: 是否启用审计字段
            enable_soft_delete: 是否启用软删除
            permissions: 权限配置
            published_at: 发布时间

    业务规则:
        - 模型名称在工作空间内唯一
        - 只有已发布的模型才会生成数据库表和 API
        - 支持版本控制，可以有多个版本但只有一个最新版本
        - 删除模型时会同时删除相关的字段、关系等
    """

    __tablename__ = "metadata_models"

    # 模型信息
    name: str = Field(max_length=255, index=True, description="模型名称（英文）")
    display_name: str = Field(max_length=255, description="显示名称（中文）")
    description: Optional[str] = Field(default=None, description="模型描述")

    # 数据库信息
    table_name: str = Field(max_length=255, description="数据库表名")
    schema_name: Optional[str] = Field(default=None, max_length=255, description="数据库模式")

    # 模型配置
    icon: Optional[str] = Field(default=None, max_length=255, description="图标")
    category: Optional[str] = Field(default=None, max_length=100, description="分类")

    # JSON Schema 定义
    schema_definition: dict = Field(
        default_factory=dict, sa_column=Column(JSON), description="JSON Schema 定义"
    )

    # 版本控制
    version: int = Field(default=1, description="版本号")
    is_latest: bool = Field(default=True, description="是否最新版本")

    # 状态
    status: ModelStatus = Field(default=ModelStatus.DRAFT, description="模型状态")

    # 配置选项
    enable_audit: bool = Field(default=True, description="启用审计字段")
    enable_soft_delete: bool = Field(default=True, description="启用软删除")
    enable_versioning: bool = Field(default=False, description="启用版本控制")

    # 权限配置
    permissions: dict = Field(default_factory=dict, sa_column=Column(JSON), description="权限配置")

    # 发布时间
    published_at: Optional[datetime] = Field(default=None, description="发布时间")

    # 统计
    record_count: int = Field(default=0, description="记录数量")

    # 关系
    fields: List["MetadataField"] = Relationship(back_populates="model")


class MetadataField(BaseModel, TimestampMixin, table=True):
    """字段元数据表

    存储数据模型中每个字段的详细配置信息。

    Attributes:
        继承字段:
            id: 字段唯一标识符（UUID）
            created_at: 创建时间
            updated_at: 更新时间

        业务字段:
            model_id: 所属模型ID
            name: 字段名称（英文）
            display_name: 显示名称（中文）
            description: 字段描述
            field_type: 逻辑字段类型
            db_type: 数据库字段类型
            is_required: 是否必填
            is_unique: 是否唯一
            is_indexed: 是否建立索引
            is_primary_key: 是否主键
            default_value: 默认值
            validation_rules: 验证规则
            ui_config: UI配置
            relation_config: 关系配置
            position: 显示顺序

    业务规则:
        - 字段名称在模型内唯一
        - 主键字段自动设置为必填和唯一
        - 外键字段需要配置关系信息
        - 删除字段时需要检查是否被其他模型引用
    """

    __tablename__ = "metadata_fields"

    # 所属模型
    model_id: UUID = Field(index=True, description="所属模型ID")  # Logical FK to metadata_models

    # 字段信息
    name: str = Field(max_length=255, description="字段名称（英文）")
    display_name: str = Field(max_length=255, description="显示名称（中文）")
    description: Optional[str] = Field(default=None, description="字段描述")

    # 字段类型
    field_type: FieldType = Field(description="逻辑字段类型")
    db_type: Optional[str] = Field(default=None, max_length=50, description="数据库字段类型")

    # 字段属性
    is_required: bool = Field(default=False, description="是否必填")
    is_unique: bool = Field(default=False, description="是否唯一")
    is_indexed: bool = Field(default=False, description="是否建立索引")
    is_primary_key: bool = Field(default=False, description="是否主键")

    # 默认值
    default_value: Optional[str] = Field(default=None, description="默认值")

    # 验证规则
    validation_rules: dict = Field(
        default_factory=dict, sa_column=Column(JSON), description="验证规则"
    )
    # 示例：
    # {
    #   "min_length": 2,
    #   "max_length": 100,
    #   "pattern": "^[a-zA-Z]+$",
    #   "min": 0,
    #   "max": 100,
    #   "enum": ["active", "inactive"]
    # }

    # UI 配置
    ui_config: dict = Field(default_factory=dict, sa_column=Column(JSON), description="UI配置")
    # 示例：
    # {
    #   "widget": "input",  # input, textarea, select, date-picker, etc.
    #   "placeholder": "请输入客户名称",
    #   "help_text": "客户的全称",
    #   "width": "100%",
    #   "options": [{"label": "选项1", "value": "value1"}]
    # }

    # 关系配置（用于外键字段）
    relation_config: Optional[dict] = Field(
        default=None, sa_column=Column(JSON), description="关系配置"
    )
    # 示例：
    # {
    #   "target_model": "user",
    #   "relation_type": "many_to_one",
    #   "on_delete": "CASCADE",
    #   "display_field": "name"
    # }

    # 显示顺序
    position: int = Field(default=0, description="显示顺序")

    # 关系
    model: MetadataModel = Relationship(back_populates="fields")


class MetadataRelation(BaseModel, TimestampMixin, table=True):
    """关系元数据表

    存储模型之间的关系定义，支持一对一、一对多、多对多关系。

    Attributes:
        继承字段:
            id: 关系唯一标识符（UUID）
            created_at: 创建时间
            updated_at: 更新时间

        业务字段:
            source_model_id: 源模型ID
            target_model_id: 目标模型ID
            name: 关系名称
            relation_type: 关系类型
            foreign_key_field: 外键字段名
            on_delete: 删除时的级联操作
            on_update: 更新时的级联操作
            junction_table: 中间表名（多对多关系）

    业务规则:
        - 关系名称在源模型内唯一
        - 多对多关系需要指定中间表
        - 级联操作影响数据完整性
    """

    __tablename__ = "metadata_relations"

    # 源模型和目标模型
    source_model_id: UUID = Field(description="源模型ID")  # Logical FK to metadata_models
    target_model_id: UUID = Field(description="目标模型ID")  # Logical FK to metadata_models

    # 关系信息
    name: str = Field(max_length=255, description="关系名称")
    relation_type: str = Field(
        max_length=50, description="关系类型"
    )  # one_to_one, one_to_many, many_to_many

    # 外键字段
    foreign_key_field: str = Field(max_length=255, description="外键字段名")

    # 级联操作
    on_delete: str = Field(default="CASCADE", max_length=50, description="删除时级联操作")
    on_update: str = Field(default="CASCADE", max_length=50, description="更新时级联操作")

    # 中间表（用于多对多）
    junction_table: Optional[str] = Field(default=None, max_length=255, description="中间表名")


class MetadataIndex(BaseModel, TimestampMixin, table=True):
    """索引元数据表

    存储自定义索引配置，支持单字段和复合索引。

    Attributes:
        继承字段:
            id: 索引唯一标识符（UUID）
            created_at: 创建时间
            updated_at: 更新时间

        业务字段:
            model_id: 所属模型ID
            name: 索引名称
            fields: 索引字段列表
            is_unique: 是否唯一索引

    业务规则:
        - 索引名称在模型内唯一
        - 唯一索引会影响数据插入
        - 复合索引的字段顺序很重要
    """

    __tablename__ = "metadata_indexes"

    # 所属模型
    model_id: UUID = Field(description="所属模型ID")  # Logical FK to metadata_models

    # 索引信息
    name: str = Field(max_length=255, description="索引名称")
    fields: List[str] = Field(sa_column=Column(JSON), description="索引字段列表")
    is_unique: bool = Field(default=False, description="是否唯一索引")


class MetadataVersion(BaseModel, TimestampMixin, AuditMixin, table=True):
    """元数据版本表

    存储元数据的版本历史，支持版本回滚和变更追踪。

    Attributes:
        继承字段:
            id: 版本记录唯一标识符（UUID）
            created_at: 创建时间
            updated_at: 更新时间

        业务字段:
            entity_type: 实体类型（model/field/relation）
            entity_id: 实体ID
            version: 版本号
            content: 版本内容快照
            change_log: 变更日志
            created_by: 创建者
     # 创建者
    created_by: UUID = Field(description="创建者")  # Logical FK to users
    业务规则:
        - 每次修改都会创建新的版本记录
        - 版本号递增
        - 支持回滚到任意版本
    """

    __tablename__ = "metadata_versions"

    # 实体信息
    entity_type: str = Field(max_length=50, description="实体类型")  # model, field, relation
    entity_id: UUID = Field(description="实体ID")

    # 版本信息
    version: int = Field(description="版本号")
    content: dict = Field(sa_column=Column(JSON), description="版本内容快照")
    change_log: Optional[str] = Field(default=None, description="变更日志")


class MetadataPage(BaseModel, TimestampMixin, AuditMixin, WorkspaceMixin, table=True):
    """页面元数据表

    存储动态页面的配置信息，支持可视化页面构建。

    Attributes:
        继承字段:
            id: 页面唯一标识符（UUID）
            workspace_id: 所属工作空间ID（租户隔离）
            created_by: 创建者用户ID
            created_at: 创建时间
            updated_at: 更新时间

        业务字段:
            name: 页面名称
            display_name: 显示名称
            description: 页面描述
            route_path: 路由路径
            layout_config: 布局配置
            components: 组件配置
            data_binding: 数据绑定
            permissions: 权限配置
            version: 版本号
            status: 页面状态

    业务规则:
        - 页面名称在工作空间内唯一
        - 路由路径不能冲突
        - 支持组件拖拽和配置
    """

    __tablename__ = "metadata_pages"

    # 页面信息
    name: str = Field(max_length=255, index=True, description="页面名称")
    display_name: str = Field(max_length=255, description="显示名称")
    description: Optional[str] = Field(default=None, description="页面描述")

    # 路由信息
    route_path: str = Field(max_length=500, description="路由路径")

    # 布局配置
    layout_config: dict = Field(
        default_factory=dict, sa_column=Column(JSON), description="布局配置"
    )

    # 组件配置
    components: List[dict] = Field(
        default_factory=list, sa_column=Column(JSON), description="组件配置"
    )

    # 数据绑定
    data_binding: dict = Field(default_factory=dict, sa_column=Column(JSON), description="数据绑定")

    # 权限配置
    permissions: dict = Field(default_factory=dict, sa_column=Column(JSON), description="权限配置")

    # 版本控制
    version: int = Field(default=1, description="版本号")
    status: str = Field(max_length=50, default="draft", description="页面状态")
