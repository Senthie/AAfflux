"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/api/v1/__init__.py
Description: 模块初始化

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from fastapi import APIRouter

from app.api.v1 import (
    app_runtime,
    applications,
    auth,
    bpm_approvals,
    bpm_processes,
    bpm_tasks,
    executions,
    file as file_router,
    organizations,
    plugins,
    providers,
    teams,
    templates,
    users,
    workflows,
    workspaces,
)

router = APIRouter(prefix='/api/v1', tags=['API v1'])

# 认证路由（公开接口）
router.include_router(auth.router, tags=['Authentication'])

# 用户管理路由
router.include_router(users.router, tags=['User Management'])

# 组织管理路由
router.include_router(organizations.router, tags=['Organizations'])
router.include_router(teams.router, tags=['Teams'])
router.include_router(workspaces.router, tags=['Workspaces'])

# 应用管理路由
router.include_router(applications.router, tags=['Applications'])
router.include_router(executions.router, tags=['Executions'])
router.include_router(app_runtime.router, tags=['Runtime'])

# BPM路由
router.include_router(bpm_processes.router, prefix='/bpm/processes', tags=['BPM Processes'])
router.include_router(bpm_tasks.router, prefix='/bpm/tasks', tags=['BPM Tasks'])
router.include_router(bpm_approvals.router, prefix='/bpm/approvals', tags=['BPM Approvals'])

# 其他功能路由
router.include_router(file_router.router, prefix='/files', tags=['Files'])
router.include_router(workflows.router, tags=['Workflows'])
router.include_router(templates.router, tags=['Templates'])
router.include_router(providers.router, tags=['LLM Providers'])
router.include_router(plugins.router, tags=['Plugins'])

__all__ = ['router']
