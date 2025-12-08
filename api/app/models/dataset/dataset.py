"""知识库模型 - 4张表。

本模块定义了知识库（Dataset）的数据模型。
支持文档上传、分段、向量化和检索。
"""

from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlmodel import Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import BaseModel, TimestampMixin, WorkspaceMixin, AuditMixin, SoftDeleteMixin


class Dataset(BaseModel, TimestampMixin, AuditMixin, WorkspaceMixin, SoftDeleteMixin, table=True):
    """知识库表 - 数据集管理。

    存储知识库的基本信息和配置。
    知识库包含多个文档，用于RAG检索增强生成。

    Attributes:
     已经继承
        id: 终端用户唯一标识符（UUID）
        workspace_id: 所属工作空间ID（逻辑外键，租户隔离）
        created_by: 创建者用户ID（逻辑外键）
        created_at: 创建时间
        updated_at: 更新时间
        deleted_at: Optional[datetime] = Field(default=None)
        is_deleted: bool = Field(default=False)

        name: 知识库名称
        description: 知识库描述
        icon: 知识库图标
        embedding_model: 使用的嵌入模型
        embedding_model_provider: 嵌入模型提供商
        retrieval_model_config: 检索模型配置（JSONB格式）
        indexing_technique: 索引技术（high_quality-高质量/economy-经济型）
        document_count: 文档数量
        word_count: 总字数

    业务规则：
        - 知识库属于工作空间，实现租户隔离
        - 支持不同的嵌入模型和索引技术
        - 记录文档和字数统计
        - 可以被多个应用引用
    """

    __tablename__ = 'datasets'

    name: str = Field(max_length=255, index=True)
    description: Optional[str] = None
    icon: Optional[str] = Field(default=None, max_length=255)
    embedding_model: str = Field(max_length=100)
    embedding_model_provider: str = Field(max_length=100)
    retrieval_model_config: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    indexing_technique: str = Field(max_length=50, default='high_quality')  # high_quality, economy
    document_count: int = Field(default=0)
    word_count: int = Field(default=0)


class Document(BaseModel, TimestampMixin, AuditMixin, SoftDeleteMixin,table=True):
    """文档表 - 知识库文档。

    存储上传到知识库的文档信息。
    文档会被分段处理和向量化。

    Attributes:
    已经继承
        id: 文档唯一标识符（UUID）
        created_by: UUID = Field(index=True)  # Logical FK to users
        created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
        updated_at: datetime = Field(default_factory=datetime.utcnow)
        deleted_at: Optional[datetime] = Field(default=None)
        is_deleted: bool = Field(default=False)

        dataset_id: 所属知识库ID（逻辑外键）
        name: 文档名称
        data_source_type: 数据源类型（upload_file-上传文件/notion-Notion/web-网页）
        data_source_info: 数据源信息（JSONB格式）
        file_id: 文件ID（逻辑外键，关联到file_references）
        position: 显示位置排序
        word_count: 字数
        tokens: Token数
        indexing_status: 索引状态（waiting-等待/parsing-解析中/splitting-分段中/indexing-索引中/completed-完成/error-错误）
        error: 错误信息（如果失败）
        enabled: 是否启用
        disabled_at: 禁用时间
        disabled_by: 禁用者用户ID
        archived: 是否归档

    业务规则：
        - 文档属于知识库
        - 支持多种数据源类型
        - 文档需要经过解析、分段、索引流程
        - 可以禁用或归档文档
    """

    __tablename__ = 'documents'

    dataset_id: UUID = Field(index=True)  # Logical FK to datasets
    name: str = Field(max_length=255)
    data_source_type: str = Field(max_length=50, index=True)  # upload_file, notion, web
    data_source_info: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    file_id: Optional[UUID] = Field(default=None, index=True)  # Logical FK to file_references
    position: int = Field(default=0)
    word_count: int = Field(default=0)
    tokens: int = Field(default=0)
    indexing_status: str = Field(
        max_length=50, index=True, default='waiting'
    )  # waiting, parsing, splitting, indexing, completed, error
    error: Optional[str] = None
    enabled: bool = Field(default=True, index=True)
    disabled_at: Optional[datetime] = None
    disabled_by: Optional[UUID] = None  # Logical FK to users
    archived: bool = Field(default=False, index=True)


class DocumentSegment(BaseModel, TimestampMixin, AuditMixin, SoftDeleteMixin,table=True):
    """文档段落表 - 文档分段。

    存储文档分段后的段落信息。
    每个段落会被向量化用于检索。

    Attributes:
    已经继承
        id: 段落唯一标识符（UUID）
        created_by: 创建者用户ID（逻辑外键）
        created_at: 创建时间
        updated_at: 更新时间
        deleted_at: Optional[datetime] = Field(default=None)
        is_deleted: bool = Field(default=False)

        document_id: 所属文档ID（逻辑外键）
        dataset_id: 所属知识库ID（逻辑外键）
        position: 段落位置序号
        content: 段落内容
        word_count: 字数
        tokens: Token数
        keywords: 关键词列表（JSONB格式）
        index_node_id: 向量索引节点ID
        index_node_hash: 向量索引哈希值
        hit_count: 命中次数（检索统计）
        enabled: 是否启用
        disabled_at: 禁用时间
        disabled_by: 禁用者用户ID
        status: 段落状态（waiting-等待/indexing-索引中/completed-完成/error-错误）
        error: 错误信息（如果失败）


    业务规则：
        - 段落属于文档和知识库
        - 段落会被向量化并存储到向量数据库
        - 记录命中次数用于统计和优化
        - 可以禁用特定段落
    """

    __tablename__ = 'document_segments'

    document_id: UUID = Field(index=True)  # Logical FK to documents
    dataset_id: UUID = Field(index=True)  # Logical FK to datasets
    position: int = Field(default=0, index=True)
    content: str
    word_count: int = Field(default=0)
    tokens: int = Field(default=0)
    keywords: Optional[list] = Field(default=None, sa_column=Column(JSONB))
    index_node_id: Optional[str] = Field(default=None, max_length=255)
    index_node_hash: Optional[str] = Field(default=None, max_length=255)
    hit_count: int = Field(default=0)
    enabled: bool = Field(default=True, index=True)
    disabled_at: Optional[datetime] = None
    disabled_by: Optional[UUID] = None  # Logical FK to users
    status: str = Field(
        max_length=50, index=True, default='waiting'
    )  # waiting, indexing, completed, error
    error: Optional[str] = None


class DatasetApplicationJoin(BaseModel, TimestampMixin, table=True):
    """知识库应用关联表 - 多对多关系。

    建立知识库和应用之间的关联关系。
    一个应用可以使用多个知识库，一个知识库可以被多个应用使用。

    Attributes:
    已经继承
        id: 关联记录唯一标识符（UUID）
        created_at: 创建时间

        dataset_id: 知识库ID（逻辑外键）
        application_id: 应用ID（逻辑外键）


    业务规则：
        - 应用可以关联多个知识库
        - 知识库可以被多个应用使用
        - 用于RAG检索增强生成
    """

    __tablename__ = 'dataset_application_joins'

    dataset_id: UUID = Field(index=True)  # Logical FK to datasets
    application_id: UUID = Field(index=True)  # Logical FK to applications
