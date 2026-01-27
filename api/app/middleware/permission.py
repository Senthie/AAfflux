"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/middleware/permission.py
Description: Permission中间件

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.tenant_context import TenantContextManager
from app.utils.rbac import Permission, has_permission
from app.core.database import get_session


class PermissionMiddleware(BaseHTTPMiddleware):
    """权限验证中间件"""

    # 需要权限验证的路径模式
    PROTECTED_PATTERNS = [
        r'/api/v1/workspaces/.*',
        r'/api/v1/workflows/.*',
        r'/api/v1/applications/.*',
        r'/api/v1/files/.*',
    ]

    # 路径到权限的映射
    PATH_PERMISSIONS = {
        'GET': Permission.READ,
        'POST': Permission.CREATE,
        'PUT': Permission.UPDATE,
        'PATCH': Permission.UPDATE,
        'DELETE': Permission.DELETE,
    }

    async def dispatch(self, request: Request, call_next: Callable):
        """处理请求权限验证"""

        # 1. 检查是否需要权限验证
        if not self._needs_permission_check(request):
            return await call_next(request)

        # 2. 获取用户信息
        user = getattr(request.state, 'user', None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required'
            )

        # 3. 提取工作空间ID
        workspace_id = self._extract_workspace_id(request)
        if not workspace_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Workspace ID required'
            )

        # 4. 验证权限
        session_gen = get_session()
        session = await anext(session_gen)

        try:
            context_manager = TenantContextManager(session)
            context = await context_manager.get_user_context(user.id, workspace_id)

            if not context:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail='Access denied to workspace'
                )

            # 5. 检查操作权限
            required_permission = self.PATH_PERMISSIONS.get(request.method)
            if required_permission and not has_permission(context.role, required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f'Insufficient permissions for {request.method}',
                )

            # 6. 将上下文附加到请求
            request.state.tenant_context = context

        finally:
            await session_gen.aclose()

        return await call_next(request)

    def _needs_permission_check(self, request: Request) -> bool:
        """检查路径是否需要权限验证"""
        import re

        path = request.url.path
        return any(re.match(pattern, path) for pattern in self.PROTECTED_PATTERNS)

    def _extract_workspace_id(self, request: Request) -> Optional[str]:
        """从请求中提取工作空间ID"""
        # 1. 从路径参数中提取 (优先级最高)
        path_params = request.path_params
        if 'workspace_id' in path_params:
            return path_params['workspace_id']

        # 2. 从查询参数中提取
        query_params = request.query_params
        if 'workspace_id' in query_params:
            return query_params['workspace_id']

        # 3. 从请求头中提取
        workspace_header = request.headers.get('X-Workspace-ID')
        if workspace_header:
            return workspace_header

        # 4. 从请求体中提取 (仅限POST/PUT请求)
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                # 注意：这里需要小心处理，因为request.body()是异步的
                # 在中间件中直接读取body可能会影响后续处理
                # 建议使用其他方式或在路由层面处理
                pass
            except Exception:
                pass

        # 5. 从URL路径中解析 (如 /api/v1/workspaces/{workspace_id}/...)
        import re

        path = request.url.path
        workspace_match = re.search(r'/workspaces/([^/]+)', path)
        if workspace_match:
            return workspace_match.group(1)

        # 6. 从其他资源路径推断工作空间ID
        # 例如: /api/v1/workflows/{workflow_id} -> 需要查询workflow所属的workspace
        workflow_match = re.search(r'/workflows/([^/]+)', path)
        if workflow_match:
            # 这里需要查询数据库获取workflow对应的workspace_id
            # 为了避免在中间件中进行数据库查询，建议在路由层面处理
            pass

        return None
