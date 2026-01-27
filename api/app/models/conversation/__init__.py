"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:48:47
FilePath: /api/app/models/conversation/__init__.py
Description: 对话域模块初始化

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from app.models.conversation.annotation import MessageAnnotation, MessageFeedback
from app.models.conversation.conversation import Conversation, Message
from app.models.conversation.end_user import EndUser

__all__ = [
    'Conversation',
    'Message',
    'MessageAnnotation',
    'MessageFeedback',
    'EndUser',
]
