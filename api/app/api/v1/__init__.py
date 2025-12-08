"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-02 08:50:10
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-08 16:14:08
FilePath: : AAfflux: api: app: api: v1: __init__.py
Description:
"""

"""API v1 路由"""

from fastapi import APIRouter
from app.api.v1 import bpm_processes, bpm_tasks, bpm_approvals
from app.api.v1 import file as file_router

router = APIRouter(prefix='/api/v1', tags=['API v1'])

# 注册 BPM 路由
router.include_router(bpm_processes.router, prefix='/bpm/processes', tags=['BPM Processes'])
router.include_router(bpm_tasks.router, prefix='/bpm/tasks', tags=['BPM Tasks'])
router.include_router(bpm_approvals.router, prefix='/bpm/approvals', tags=['BPM Approvals'])

# 注册文件路由
router.include_router(file_router.router, prefix='/files', tags=['Files'])

__all__ = ['router']
