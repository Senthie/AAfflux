"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-02 08:50:10
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-09 16:25:28
FilePath: : AAfflux: api: app: api: v1: __init__.py
Description: API v1 路由
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    bpm_approvals,
    bpm_processes,
    bpm_tasks,
    file as file_router,
    users,
    workflows,
)

router = APIRouter(prefix='/api/v1', tags=['API v1'])

# 注册认证路由（公开接口）
router.include_router(auth.router, tags=['Authentication'])

# 注册用户管理路由（需要认证）
router.include_router(users.router, tags=['User Management'])

# 注册 BPM 路由
router.include_router(bpm_processes.router, prefix='/bpm/processes', tags=['BPM Processes'])
router.include_router(bpm_tasks.router, prefix='/bpm/tasks', tags=['BPM Tasks'])
router.include_router(bpm_approvals.router, prefix='/bpm/approvals', tags=['BPM Approvals'])

# 注册文件路由
router.include_router(file_router.router, prefix='/files', tags=['Files'])

# 注册工作流路由
router.include_router(workflows.router, tags=['Workflows'])

__all__ = ['router']
