"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-22 10:26:13
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-24 15:54:10
FilePath: /api/app/services/application_service.py
Description:应用crud、发布、api密钥管理
"""

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlmodel import and_, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.application.application import Application
from app.models.auth.api_key import APIKey
from app.schemas.application import (
    APIKeyCreate,
    ApplicationCreate,
    ApplicationQuery,
    ApplicationUpdate,
)
from app.utils.api_key import APIKeyManager


class ApplicationService:
    """应用服务"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.api_key_manager = APIKeyManager()

    async def create_application(
        self, data: ApplicationCreate, user_id: UUID, workspace_id: UUID = None
    ) -> Application:
        """创建应用"""
        application = Application(
            name=data.name,
            workflow_id=data.workflow_id,
            config=data.config,
            is_published=False,
            created_by=user_id,
            updated_by=user_id,
            workspace_id=workspace_id
            or data.workflow_id,  # 使用提供的 workspace_id 或默认使用 workflow_id
        )

        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)

        # 生成API端点
        application.api_endpoint = f'/api/v1/runtime/apps/{application.id}/execute'
        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)

        return application

    async def get_application(self, application_id: UUID) -> Optional[Application]:
        """获取单个应用"""
        statement = select(Application).where(
            and_(Application.id == application_id, Application.is_deleted is not True)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def update_application(
        self, application_id: UUID, data: ApplicationUpdate, user_id: UUID
    ) -> Optional[Application]:
        """更新应用"""
        application = await self.get_application(application_id)
        if not application:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(application, key, value)

        application.updated_by = user_id
        application.updated_at = datetime.utcnow()

        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def delete_application(self, application_id: UUID, user_id: UUID) -> bool:
        """删除应用（软删除）"""
        application = await self.get_application(application_id)
        if not application:
            return False

        application.is_deleted = True
        application.deleted_at = datetime.utcnow()
        application.updated_by = user_id
        application.updated_at = datetime.utcnow()

        self.session.add(application)
        await self.session.commit()
        return True

    async def list_applications(
        self, query: ApplicationQuery, user_id: Optional[UUID] = None
    ) -> Tuple[List[Application], int]:
        """分页查询应用列表"""
        statement = select(Application).where(Application.is_deleted is not True)

        # 构建查询条件
        conditions = []
        if query.name:
            conditions.append(Application.name.ilike(f'%{query.name}%'))
        if query.is_published is not None:
            conditions.append(Application.is_published == query.is_published)
        if query.workflow_id:
            conditions.append(Application.workflow_id == query.workflow_id)
        if user_id:
            conditions.append(Application.created_by == user_id)

        if conditions:
            statement = statement.where(and_(*conditions))

        # 获取总数
        count_statement = (
            select(func.count()).select_from(Application).where(Application.is_deleted is not True)
        )
        if conditions:
            count_statement = count_statement.where(and_(*conditions))
        total_result = await self.session.execute(count_statement)
        total = total_result.scalar_one()

        # 分页
        statement = statement.order_by(Application.created_at.desc())
        statement = statement.offset((query.page - 1) * query.page_size)
        statement = statement.limit(query.page_size)

        result = await self.session.execute(statement)
        applications = list(result.scalars().all())
        return applications, total

    async def publish_application(
        self, application_id: UUID, is_published: bool, user_id: UUID
    ) -> Optional[Application]:
        """发布/取消发布应用"""
        application = await self.get_application(application_id)
        if not application:
            return None

        application.is_published = is_published
        application.updated_by = user_id
        application.updated_at = datetime.utcnow()

        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def create_api_key(
        self, application_id: UUID, data: APIKeyCreate, user_id: UUID
    ) -> Optional[dict]:
        """为应用创建API密钥"""
        application = await self.get_application(application_id)
        if not application:
            return None

        # 生成API密钥
        key_data = self.api_key_manager.create_api_key(
            name=data.name,
            prefix=f'app_{application_id.hex[:8]}',
            expires_in_days=data.expires_in_days,
        )

        # 创建API密钥记录
        # 将 salt 和 hashed_key 合并存储
        combined_hash = f'{key_data["salt"]}:{key_data["hashed_key"]}'
        api_key = APIKey(
            application_id=application_id,
            name=data.name,
            key_prefix=key_data['api_key'].split('_')[0]
            + '_'
            + key_data['api_key'].split('_')[1][:8]
            + '...',
            key_hash=combined_hash,
        )

        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)

        return {
            'id': api_key.id,
            'name': api_key.name,
            'api_key': key_data['api_key'],  # 完整密钥，只在创建时返回
            'key_prefix': api_key.key_prefix,
            'created_at': api_key.created_at,
            'expires_at': key_data.get('expires_at'),  # 从 key_data 获取
            'is_active': api_key.is_active,
        }

    async def list_api_keys(self, application_id: UUID) -> List[APIKey]:
        """获取应用的API密钥列表"""
        statement = (
            select(APIKey)
            .where(APIKey.application_id == application_id)
            .order_by(APIKey.created_at.desc())
        )

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def revoke_api_key(self, application_id: UUID, api_key_id: UUID, user_id: UUID) -> bool:
        """撤销API密钥"""
        statement = select(APIKey).where(
            and_(
                APIKey.id == api_key_id,
                APIKey.application_id == application_id,
            )
        )
        result = await self.session.execute(statement)
        api_key = result.scalar_one_or_none()

        if not api_key:
            return False

        api_key.is_active = False

        self.session.add(api_key)
        await self.session.commit()
        return True

    async def verify_api_key(self, api_key_str: str) -> Optional[APIKey]:
        """验证API密钥"""
        # 从密钥字符串中提取前缀
        if '_' not in api_key_str:
            return None

        parts = api_key_str.split('_')
        if len(parts) < 3:
            return None

        # 构建前缀模式：app_<8字符>
        # key_prefix 格式是 "app_12345678..."
        prefix_pattern = f'{parts[0]}_{parts[1]}%'

        statement = select(APIKey).where(
            and_(
                APIKey.key_prefix.like(prefix_pattern),
                APIKey.is_active.is_(True),
            )
        )

        result = await self.session.execute(statement)
        api_keys = list(result.scalars().all())

        for api_key in api_keys:
            # 从 key_hash 中提取 salt 和 hashed_key
            if ':' in api_key.key_hash:
                salt, hashed_key = api_key.key_hash.split(':', 1)
            else:
                continue

            if self.api_key_manager.verify_api_key(
                api_key_str,
                hashed_key,
                salt,
                api_key.created_at,
                None,  # 不检查过期
                api_key.is_active,
            ):
                # 更新最后使用时间
                api_key.last_used_at = datetime.utcnow()
                self.session.add(api_key)
                await self.session.commit()
                return api_key

        return None

    async def get_application_by_api_key(self, api_key_str: str) -> Optional[Application]:
        """通过API密钥获取应用"""
        api_key = await self.verify_api_key(api_key_str)
        if not api_key:
            return None

        return await self.get_application(api_key.application_id)
