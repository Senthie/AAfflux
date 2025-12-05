"""BPM 数据模型"""

from app.models.bpm.process import ProcessDefinition, ProcessInstance, ProcessStatus
from app.models.bpm.task import Task, TaskStatus, TaskType
from app.models.bpm.approval import Approval, ApprovalAction
from app.models.bpm.form import FormDefinition, FormData

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
