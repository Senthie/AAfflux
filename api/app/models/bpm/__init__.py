"""BPM 数据模型"""

from api.app.models.bpm.process import ProcessDefinition, ProcessInstance, ProcessStatus
from api.app.models.bpm.task import Task, TaskStatus, TaskType
from api.app.models.bpm.approval import Approval, ApprovalAction
from api.app.models.bpm.form import FormDefinition, FormData

__all__ = [
    "ProcessDefinition",
    "ProcessInstance",
    "ProcessStatus",
    "Task",
    "TaskStatus",
    "TaskType",
    "Approval",
    "ApprovalAction",
    "FormDefinition",
    "FormData",
]
