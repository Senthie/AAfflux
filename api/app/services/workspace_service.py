"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-10 14:41:43
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-09 12:04:01
FilePath: /api/app/services/workspace_service.py
Description:工作空间管理服务
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.response import ResponseSchemaModel, response_base
from app.models.application.application import Application
from app.models.file.reference import FileReference
from app.models.tenant.organization import Workspace, WorkspaceAccountUser
from app.models.workflow.workflow import Workflow
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate


class WorkspaceService:
    """工作空间管理服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_workspace(self, data: WorkspaceCreate, creator_id: UUID) -> Workspace:
        """创建工作空间"""
        workspace = Workspace(
            name=data.name,
            team_id=data.team_id,
            description=data.description,
            settings=data.settings or {},
            created_by=creator_id,
        )

        self.session.add(workspace)
        await self.session.commit()
        await self.session.refresh(workspace)

        return workspace

    async def get_workspace(self, workspace_id: UUID) -> Optional[Workspace]:
        """获取工作空间信息"""
        return await self.session.get(Workspace, workspace_id)

    async def update_workspace(
        self, workspace_id: UUID, data: WorkspaceUpdate
    ) -> Optional[Workspace]:
        """更新工作空间"""
        workspace = await self.session.get(Workspace, workspace_id)
        if not workspace:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(workspace, field, value)

        await self.session.commit()
        await self.session.refresh(workspace)

        return workspace

    async def delete_workspace(self, workspace_id: UUID) -> bool:
        """删除工作空间（级联删除资源）"""
        workspace = await self.session.get(Workspace, workspace_id)
        if not workspace:
            return False

        # 软删除工作空间
        workspace.soft_delete()

        # 级联软删除所有资源
        await self._cascade_delete_resources(workspace_id)

        await self.session.commit()
        return True

    async def _cascade_delete_resources(self, workspace_id: UUID):
        """级联删除工作空间下的所有资源"""
        # 软删除工作流
        workflows = await self.session.execute(
            select(Workflow).where(Workflow.workspace_id == workspace_id)
        )
        for workflow in workflows.scalars():
            workflow.soft_delete()

        # 软删除应用
        applications = await self.session.execute(
            select(Application).where(Application.workspace_id == workspace_id)
        )
        for app in applications.scalars():
            app.soft_delete()

        # 软删除文件引用
        files = await self.session.execute(
            select(FileReference).where(FileReference.workspace_id == workspace_id)
        )
        for file_ref in files.scalars():
            file_ref.soft_delete()

    async def move_resource(
        self, resource_id: UUID, resource_type: str, target_workspace_id: UUID
    ) -> bool:
        """移动资源到其他工作空间"""
        resource_models = {
            'workflow': Workflow,
            'application': Application,
            'file': FileReference,
        }

        model_class = resource_models.get(resource_type)
        if not model_class:
            return False

        resource = await self.session.get(model_class, resource_id)
        if not resource:
            return False

        resource.workspace_id = target_workspace_id
        await self.session.commit()

        return True

    async def list_resources(self, workspace_id: UUID) -> Dict[str, Any]:
        """获取工作空间资源列表"""
        # 查询工作流
        workflows = await self.session.execute(
            select(Workflow).where(
                Workflow.workspace_id == workspace_id, Workflow.is_deleted.is_(False)
            )
        )

        # 查询应用
        applications = await self.session.execute(
            select(Application).where(
                Application.workspace_id == workspace_id, Application.is_deleted.is_(False)
            )
        )

        # 查询文件
        files = await self.session.execute(
            select(FileReference).where(
                FileReference.workspace_id == workspace_id, FileReference.is_deleted.is_(False)
            )
        )

        return {
            'workflows': list(workflows.scalars().all()),
            'applications': list(applications.scalars().all()),
            'files': list(files.scalars().all()),
        }

    async def get_team_workspaces(self, team_id: UUID) -> List[Workspace]:
        """获取团队下的所有工作空间"""
        result = await self.session.execute(
            select(Workspace).where(Workspace.team_id == team_id, Workspace.is_deleted.is_(False))
        )
        return list(result.scalars().all())

    async def get_user_workspaces(
        self, user_id: UUID
    ) -> ResponseSchemaModel[list[WorkspaceResponse]]:
        """获取用户可访问的所有工作空间"""
        # 获取用户所属的所有团队
        workspace_accounts = await self.session.execute(
            select(WorkspaceAccountUser).where(WorkspaceAccountUser.user_id == user_id)
        )

        workspace_ids = [wa.workspace_id for wa in workspace_accounts.scalars().all()]

        if not workspace_ids:
            return response_base.success(data=[])

        # 获取这些团队下的所有工作空间
        result = await self.session.execute(
            select(Workspace).where(
                Workspace.id.in_(workspace_ids), Workspace.is_deleted.is_(False)
            )
        )
        lst = [WorkspaceResponse.model_validate(ws) for ws in result.scalars().all()]
        return response_base.success(data=lst)
