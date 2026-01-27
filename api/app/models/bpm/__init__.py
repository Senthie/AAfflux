"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:48:08
FilePath: /api/app/models/bpm/__init__.py
Description: BPM 数据模块初始化

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from app.models.bpm.approval import Approval, ApprovalAction
from app.models.bpm.form import FormData, FormDefinition
from app.models.bpm.process import ProcessDefinition, ProcessInstance, ProcessStatus
from app.models.bpm.task import Task, TaskStatus, TaskType

__all__ = [
    'ProcessDefinition',
    'ProcessInstance',
    'ProcessStatus',
    'Task',
    'TaskStatus',
    'TaskType',
    'Approval',
    'ApprovalAction',
    'FormDefinition',
    'FormData',
]
