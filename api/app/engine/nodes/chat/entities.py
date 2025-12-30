"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-29 15:22:48
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-29 15:22:58
FilePath: /api/app/engine/nodes/chat/entities.py
Description:

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from app.engine.nodes.base import BaseNodeData


class ChatNodeData(BaseNodeData):
    # 代理策略相关字段
    prompt: str
