"""标注模型 - 2张表。

本模块定义了消息标注和反馈的数据模型。
支持类似 Dify 的标注回复功能，用于改进AI效果。
"""

from uuid import UUID
from typing import Optional
from sqlmodel import Field
from app.models.base import BaseModel, TimestampMixin


class MessageAnnotation(BaseModel, TimestampMixin, table=True):
    """消息标注表 - 人工标注和修正。

    允许租户用户对AI回复进行标注和修正。
    标注数据可用于模型微调和效果改进。

    Attributes:
    已经继承
       id: 标注记录唯一标识符（UUID）
        created_at: 创建时间
        updated_at: 更新时间

        message_id: 关联的消息ID（逻辑外键）
        conversation_id: 所属对话ID（逻辑外键）
        application_id: 关联的应用ID（逻辑外键）
        content: 标注内容（修正后的回复）
        annotation_type: 标注类型（correction-修正/improvement-改进/example-示例）
        annotated_by: 标注者用户ID（逻辑外键，租户用户）


    业务规则：
        - 只有租户用户可以标注消息
        - 标注内容可用于构建训练数据
        - 支持多种标注类型
        - 一条消息可以有多个标注
    """

    __tablename__ = 'message_annotations'

    message_id: UUID = Field(index=True)  # Logical FK to messages
    conversation_id: UUID = Field(index=True)  # Logical FK to conversations
    application_id: UUID = Field(index=True)  # Logical FK to applications
    content: str
    annotation_type: str = Field(max_length=50, index=True)  # correction, improvement, example
    annotated_by: UUID = Field(index=True)  # Logical FK to users (租户用户)


class MessageFeedback(BaseModel, TimestampMixin, table=True):
    """消息反馈表 - 用户评价。

    收集终端用户对AI回复的反馈（点赞/点踩）。
    用于评估AI效果和识别问题。

    Attributes:
     已经继承
       id: 标注记录唯一标识符（UUID）
       created_at: 创建时间


        message_id: 关联的消息ID（逻辑外键）
        conversation_id: 所属对话ID（逻辑外键）
        application_id: 关联的应用ID（逻辑外键）
        end_user_id: 终端用户ID（逻辑外键）
        rating: 评分（like-点赞/dislike-点踩）
        content: 反馈内容（可选的文字说明）


    业务规则：
        - 终端用户可以对AI回复进行评价
        - 支持点赞/点踩和文字反馈
        - 一条消息一个用户只能反馈一次
        - 反馈数据用于效果评估
    """

    __tablename__ = 'message_feedbacks'

    message_id: UUID = Field(index=True)  # Logical FK to messages
    conversation_id: UUID = Field(index=True)  # Logical FK to conversations
    application_id: UUID = Field(index=True)  # Logical FK to applications
    end_user_id: UUID = Field(index=True)  # Logical FK to end_users
    rating: str = Field(max_length=20, index=True)  # like, dislike
    content: Optional[str] = None
