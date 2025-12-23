"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-22 10:26:13
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-22 15:04:43
FilePath: : AAfflux: api: app: services: application_service.py
Description:应用crud、发布、api密钥管理
"""

from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID
from sqlmodel import select, func, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.application.application import Application
from app.models.auth.api_key import APIKey
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationQuery,
    APIKeyCreate,
)
from app.utils.api_key import APIKeyManager


class ApplicationService:
    """应用服务"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.api_key_manager = APIKeyManager()

    async def create_application(self, data: ApplicationCreate, user_id: UUID) -> Application:
        """创建应用"""
        application = Application(
            name=data.name,
            description=data.description,
            workflow_id=data.workflow_id,
            config=data.config,
            is_published=False,
            created_by=user_id,
            updated_by=user_id,
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
        api_key = APIKey(
            application_id=application_id,
            name=data.name,
            key_prefix=key_data['api_key'].split('_')[0]
            + '_'
            + key_data['api_key'].split('_')[1][:8]
            + '...',
            hashed_key=key_data['hashed_key'],
            salt=key_data['salt'],
            expires_at=key_data['expires_at'],
            created_by=user_id,
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
            'expires_at': api_key.expires_at,
            'is_active': api_key.is_active,
        }

    async def list_api_keys(self, application_id: UUID) -> List[APIKey]:
        """获取应用的API密钥列表"""
        statement = (
            select(APIKey)
            .where(and_(APIKey.application_id == application_id, APIKey.is_deleted is False))
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
                APIKey.is_deleted is False,
            )
        )
        result = await self.session.execute(statement)
        api_key = result.scalar_one_or_none()

        if not api_key:
            return False

        api_key.is_active = False
        api_key.updated_by = user_id
        api_key.updated_at = datetime.utcnow()

        self.session.add(api_key)
        await self.session.commit()
        return True

    async def verify_api_key(self, api_key_str: str) -> Optional[APIKey]:
        """验证API密钥"""
        # 从密钥字符串中提取前缀
        if '_' not in api_key_str:
            return None

        prefix_part = api_key_str.split('_')[0] + '_' + api_key_str.split('_')[1][:8] + '...'

        statement = select(APIKey).where(
            and_(
                APIKey.key_prefix.like(
                    f'{prefix_part.split("_")[0]}_{prefix_part.split("_")[1][:8]}%'
                ),
                APIKey.is_active is True,
                APIKey.is_deleted is False,
            )
        )

        result = await self.session.execute(statement)
        api_keys = list(result.scalars().all())

        for api_key in api_keys:
            if self.api_key_manager.verify_api_key(
                api_key_str,
                api_key.hashed_key,
                api_key.salt,
                api_key.created_at,
                (api_key.expires_at - api_key.created_at).days if api_key.expires_at else None,
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
