"""
LLM提供商管理服务

本模块实现了LLM提供商的配置管理、API密钥验证、模型查询等功能。
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.application.llm_provider import LLMProvider
from app.schemas.provider import (
    LLMCallRequest,
    LLMCallResponse,
    LLMModelInfo,
    LLMProviderCreate,
    LLMProviderResponse,
    LLMProviderUpdate,
    LLMProviderValidationRequest,
    LLMProviderValidationResponse,
    mask_api_key,
)
from app.utils.llm import AnthropicClient, LLMClient, OpenAIClient
from app.utils.password import decrypt_text, encrypt_text

logger = logging.getLogger(__name__)


class LLMProviderService:
    """LLM提供商管理服务"""

    def __init__(self, session: AsyncSession):
        """初始化服务

        Args:
            session: 数据库会话
        """
        self.session = session

    async def create_provider(
        self, provider_data: LLMProviderCreate, workspace_id: UUID, created_by: UUID
    ) -> LLMProviderResponse:
        """创建LLM提供商配置

        Args:
            provider_data: 提供商创建数据
            workspace_id: 工作空间ID
            created_by: 创建者ID

        Returns:
            LLMProviderResponse: 创建的提供商配置

        Raises:
            ValueError: 当提供商名称已存在或API密钥无效时
        """
        # 检查名称是否已存在
        result = await self.session.execute(
            select(LLMProvider).where(
                LLMProvider.workspace_id == workspace_id,
                LLMProvider.name == provider_data.name,
                not LLMProvider.is_deleted,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f'Provider with name "{provider_data.name}" already exists')

        # 验证API密钥
        validation_result = await self.validate_api_key(
            LLMProviderValidationRequest(
                provider_type=provider_data.provider_type,
                api_key=provider_data.api_key,
                config=provider_data.config,
            )
        )

        if not validation_result.is_valid:
            raise ValueError(f'Invalid API key: {validation_result.error_message}')

        # 加密API密钥
        encrypted_api_key = encrypt_text(provider_data.api_key)

        # 创建提供商配置
        provider = LLMProvider(
            name=provider_data.name,
            provider_type=provider_data.provider_type,
            api_key_encrypted=encrypted_api_key,
            config=provider_data.config,
            workspace_id=workspace_id,
            created_by=created_by,
        )

        try:
            self.session.add(provider)
            await self.session.commit()
            await self.session.refresh(provider)

            return self._to_response(provider)
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f'Failed to create LLM provider: {e}')
            raise ValueError('Failed to create provider due to database constraint') from e

    async def update_provider(
        self, provider_id: UUID, provider_data: LLMProviderUpdate, workspace_id: UUID
    ) -> LLMProviderResponse:
        """更新LLM提供商配置

        Args:
            provider_id: 提供商ID
            provider_data: 更新数据
            workspace_id: 工作空间ID

        Returns:
            LLMProviderResponse: 更新后的提供商配置

        Raises:
            ValueError: 当提供商不存在或更新失败时
        """
        provider = self._get_provider_by_id(provider_id, workspace_id)

        # 检查名称冲突
        if provider_data.name and provider_data.name != provider.name:
            result = await self.session.execute(
                select(LLMProvider).where(
                    LLMProvider.workspace_id == workspace_id,
                    LLMProvider.name == provider_data.name,
                    LLMProvider.id != provider_id,
                    not LLMProvider.is_deleted,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                raise ValueError(f'Provider with name "{provider_data.name}" already exists')

        # 如果更新API密钥，需要验证
        if provider_data.api_key:
            validation_result = await self.validate_api_key(
                LLMProviderValidationRequest(
                    provider_type=provider.provider_type,
                    api_key=provider_data.api_key,
                    config=provider_data.config or provider.config,
                )
            )

            if not validation_result.is_valid:
                raise ValueError(f'Invalid API key: {validation_result.error_message}')

            provider.api_key_encrypted = encrypt_text(provider_data.api_key)

        # 更新其他字段
        if provider_data.name:
            provider.name = provider_data.name
        if provider_data.config is not None:
            provider.config = provider_data.config

        provider.touch()

        try:
            await self.session.commit()
            await self.session.refresh(provider)

            return self._to_response(provider)
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f'Failed to update LLM provider: {e}')
            raise ValueError('Failed to update provider due to database constraint') from e

    async def get_provider(self, provider_id: UUID, workspace_id: UUID) -> LLMProviderResponse:
        """获取LLM提供商配置

        Args:
            provider_id: 提供商ID
            workspace_id: 工作空间ID

        Returns:
            LLMProviderResponse: 提供商配置
        """
        provider = await self._get_provider_by_id(provider_id, workspace_id)
        return self._to_response(provider)

    async def list_providers(
        self, workspace_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[LLMProviderResponse]:
        """获取工作空间的LLM提供商列表

        Args:
            workspace_id: 工作空间ID
            skip: 跳过的记录数
            limit: 限制返回的记录数

        Returns:
            List[LLMProviderResponse]: 提供商配置列表
        """
        result = await self.session.execute(
            select(LLMProvider)
            .where(LLMProvider.workspace_id == workspace_id, not LLMProvider.is_deleted)
            .offset(skip)
            .limit(limit)
            .order_by(LLMProvider.created_at.desc())
        )
        providers = result.scalars().all()

        return [self._to_response(provider) for provider in providers]

    async def delete_provider(self, provider_id: UUID, workspace_id: UUID) -> None:
        """删除LLM提供商配置

        Args:
            provider_id: 提供商ID
            workspace_id: 工作空间ID

        Raises:
            ValueError: 当提供商不存在或被工作流引用时
        """
        provider = await self._get_provider_by_id(provider_id, workspace_id)

        # 检查是否被工作流引用
        if await self._is_provider_referenced(provider_id):
            raise ValueError('Cannot delete provider that is referenced by workflows')

        # 软删除
        provider.soft_delete()

        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(f'Failed to delete LLM provider: {e}')
            raise ValueError('Failed to delete provider') from e

    async def get_provider_models(
        self, provider_id: UUID, workspace_id: UUID
    ) -> List[LLMModelInfo]:
        """获取提供商支持的模型列表

        Args:
            provider_id: 提供商ID
            workspace_id: 工作空间ID

        Returns:
            List[LLMModelInfo]: 模型信息列表
        """
        provider = await self._get_provider_by_id(provider_id, workspace_id)
        client = await self._create_client(provider)

        try:
            model_names = await client.list_models()
            models = []

            for model_name in model_names:
                model_info = LLMModelInfo(
                    model_name=model_name,
                    display_name=self._get_model_display_name(model_name),
                    max_tokens=self._get_model_max_tokens(model_name),
                    supports_streaming=self._model_supports_streaming(model_name),
                    description=self._get_model_description(model_name),
                )
                models.append(model_info)

            return models
        finally:
            if hasattr(client, '__aexit__'):
                await client.__aexit__(None, None, None)

    async def call_llm(self, request: LLMCallRequest, workspace_id: UUID) -> LLMCallResponse:
        """调用LLM生成响应

        Args:
            request: LLM调用请求
            workspace_id: 工作空间ID

        Returns:
            LLMCallResponse: LLM响应
        """
        import time

        provider = await self._get_provider_by_id(request.provider_id, workspace_id)
        client = await self._create_client(provider)

        start_time = time.time()

        try:
            response = await client.call(
                model=request.model,
                prompt=request.prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                **request.additional_params,
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            return LLMCallResponse(
                content=response.content,
                model=response.model,
                usage=response.usage,
                finish_reason=response.finish_reason,
                response_time_ms=response_time_ms,
            )
        finally:
            if hasattr(client, '__aexit__'):
                await client.__aexit__(None, None, None)

    async def validate_api_key(
        self, request: LLMProviderValidationRequest
    ) -> LLMProviderValidationResponse:
        """验证API密钥是否有效

        Args:
            request: 验证请求

        Returns:
            LLMProviderValidationResponse: 验证结果
        """
        try:
            client = self._create_client_from_config(
                request.provider_type, request.api_key, request.config
            )

            # 验证API密钥
            is_valid = await client.validate_api_key()

            if is_valid:
                # 获取可用模型列表
                try:
                    models = await client.list_models()
                except Exception as e:
                    logger.warning(f'Failed to fetch models during validation: {e}')
                    models = []

                return LLMProviderValidationResponse(is_valid=True, available_models=models)
            else:
                return LLMProviderValidationResponse(
                    is_valid=False, error_message='Invalid API key'
                )

        except Exception as e:
            logger.error(f'Error validating API key: {e}')
            return LLMProviderValidationResponse(is_valid=False, error_message=str(e))
        finally:
            if 'client' in locals() and hasattr(client, '__aexit__'):
                await client.__aexit__(None, None, None)

    async def _get_provider_by_id(self, provider_id: UUID, workspace_id: UUID) -> LLMProvider:
        """根据ID获取提供商配置

        Args:
            provider_id: 提供商ID
            workspace_id: 工作空间ID

        Returns:
            LLMProvider: 提供商配置

        Raises:
            ValueError: 当提供商不存在时
        """
        result = await self.session.execute(
            select(LLMProvider).where(
                LLMProvider.id == provider_id,
                LLMProvider.workspace_id == workspace_id,
                not LLMProvider.is_deleted,
            )
        )
        provider = result.scalar_one_or_none()

        if not provider:
            raise ValueError(f'LLM provider with ID {provider_id} not found')

        return provider

    async def _create_client(self, provider: LLMProvider) -> LLMClient:
        """根据提供商配置创建客户端

        Args:
            provider: 提供商配置

        Returns:
            LLMClient: LLM客户端实例
        """
        api_key = decrypt_text(provider.api_key_encrypted)
        return self._create_client_from_config(provider.provider_type, api_key, provider.config)

    def _create_client_from_config(
        self, provider_type: str, api_key: str, config: Dict[str, Any]
    ) -> LLMClient:
        """根据配置创建客户端

        Args:
            provider_type: 提供商类型
            api_key: API密钥
            config: 配置

        Returns:
            LLMClient: LLM客户端实例

        Raises:
            ValueError: 当提供商类型不支持时
        """
        if provider_type == 'OPENAI':
            return OpenAIClient(api_key, config)
        elif provider_type == 'ANTHROPIC':
            return AnthropicClient(api_key, config)
        else:
            raise ValueError(f'Unsupported provider type: {provider_type}')

    async def _is_provider_referenced(self, provider_id: UUID) -> bool:
        """检查提供商是否被工作流引用

        Args:
            provider_id: 提供商ID

        Returns:
            bool: 是否被引用
        """
        # TODO: 实现检查工作流节点中是否引用了该提供商
        # 这需要查询工作流节点的配置，检查是否有节点使用了该提供商
        return False

    def _to_response(self, provider: LLMProvider) -> LLMProviderResponse:
        """将数据库模型转换为响应模型

        Args:
            provider: 数据库模型

        Returns:
            LLMProviderResponse: 响应模型
        """
        return LLMProviderResponse(
            id=provider.id,
            name=provider.name,
            provider_type=provider.provider_type,
            config=provider.config,
            workspace_id=provider.workspace_id,
            created_by=provider.created_by,
            created_at=provider.created_at,
            updated_at=provider.updated_at,
            api_key_masked=mask_api_key(decrypt_text(provider.api_key_encrypted)),
        )

    def _get_model_display_name(self, model_name: str) -> str:
        """获取模型的显示名称"""
        display_names = {
            'gpt-4': 'GPT-4',
            'gpt-4-turbo': 'GPT-4 Turbo',
            'gpt-3.5-turbo': 'GPT-3.5 Turbo',
            'claude-3-opus-20240229': 'Claude 3 Opus',
            'claude-3-sonnet-20240229': 'Claude 3 Sonnet',
            'claude-3-haiku-20240307': 'Claude 3 Haiku',
        }
        return display_names.get(model_name, model_name)

    def _get_model_max_tokens(self, model_name: str) -> Optional[int]:
        """获取模型的最大令牌数"""
        max_tokens = {
            'gpt-4': 8192,
            'gpt-4-turbo': 128000,
            'gpt-3.5-turbo': 4096,
            'claude-3-opus-20240229': 200000,
            'claude-3-sonnet-20240229': 200000,
            'claude-3-haiku-20240307': 200000,
        }
        return max_tokens.get(model_name)

    def _model_supports_streaming(self, model_name: str) -> bool:
        """检查模型是否支持流式输出"""
        # 大多数现代模型都支持流式输出
        return True

    def _get_model_description(self, model_name: str) -> Optional[str]:
        """获取模型描述"""
        descriptions = {
            'gpt-4': 'Most capable GPT-4 model, great for complex tasks',
            'gpt-4-turbo': 'Faster and more efficient GPT-4 model',
            'gpt-3.5-turbo': 'Fast and efficient model for most tasks',
            'claude-3-opus-20240229': 'Most powerful Claude model for complex reasoning',
            'claude-3-sonnet-20240229': 'Balanced Claude model for general use',
            'claude-3-haiku-20240307': 'Fastest Claude model for simple tasks',
        }
        return descriptions.get(model_name)
