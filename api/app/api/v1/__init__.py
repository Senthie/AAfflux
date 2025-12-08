"""API v1 路由"""

from fastapi import APIRouter

from app.api.v1 import bpm_processes, bpm_tasks, bpm_approvals

router = APIRouter(prefix='/api/v1', tags=['API v1'])

# 注册 BPM 路由
router.include_router(bpm_processes.router, prefix='/bpm/processes', tags=['BPM Processes'])
router.include_router(bpm_tasks.router, prefix='/bpm/tasks', tags=['BPM Tasks'])
router.include_router(bpm_approvals.router, prefix='/bpm/approvals', tags=['BPM Approvals'])

__all__ = ['router']
