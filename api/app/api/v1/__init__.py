"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-02 08:50:10
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-17 17:42:35
FilePath: : AAfflux: api: app: api: v1: __init__.py
Description: API v1 路由注册
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    bpm_approvals,
    bpm_processes,
    bpm_tasks,
    file as file_router,
    providers,
    templates,
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

# 注册模板路由
router.include_router(templates.router, tags=['Templates'])

# 注册LLM提供商路由
router.include_router(providers.router, tags=['LLM Providers'])

# 工作流管理路由
try:
    from app.api.v1.workflows import router as workflows_router

    router.include_router(workflows_router, tags=['Workflow Management'])
    print('✅ Workflows router registered')
except Exception as e:
    print(f'❌ Workflows router failed: {e}')

# LLM提供商管理路由
try:
    from app.api.v1.providers import router as providers_router

    router.include_router(providers_router, tags=['LLM Provider Management'])
    print('✅ Providers router registered')
except Exception as e:
    print(f'❌ Providers router failed: {e}')

# 模板管理路由
try:
    from app.api.v1.templates import router as templates_router

    router.include_router(templates_router, tags=['Template Management'])
    print('✅ Templates router registered')
except Exception as e:
    print(f'❌ Templates router failed: {e}')

# BPM流程管理路由
try:
    from app.api.v1.bpm_processes import router as bmp_processes_router

    router.include_router(bmp_processes_router, tags=['BPM Process Management'])
    print('✅ BPM Processes router registered')
except Exception as e:
    print(f'❌ BPM Processes router failed: {e}')

# BPM任务管理路由
try:
    from app.api.v1.bpm_tasks import router as bpm_tasks_router

    router.include_router(bpm_tasks_router, tags=['BPM Task Management'])
    print('✅ BPM Tasks router registered')
except Exception as e:
    print(f'❌ BPM Tasks router failed: {e}')

# BPM审批管理路由
try:
    from app.api.v1.bpm_approvals import router as bpm_approvals_router

    router.include_router(bpm_approvals_router, tags=['BPM Approval Management'])
    print('✅ BPM Approvals router registered')
except Exception as e:
    print(f'❌ BPM Approvals router failed: {e}')

__all__ = ['router']
