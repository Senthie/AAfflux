"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:53:45
FilePath: /api/app/services/__init__.py
Description: 模块初始化

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from app.services.bpm_approval_service import ApprovalService
from app.services.bpm_process_service import ProcessService
from app.services.bpm_task_service import TaskService

__all__ = [
    'ProcessService',
    'TaskService',
    'ApprovalService',
]
