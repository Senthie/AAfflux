"""
LLM提供商相关的Pydantic schemas

本模块定义了LLM提供商管理相关的数据验证和序列化模式。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class LLMProviderBase(BaseModel):
    """LLM提供商基础模式"""

    name: str = Field(..., min_length=1, max_length=255, description='提供商配置名称')
    provider_type: str = Field(..., description='提供商类型')
    config: Dict[str, Any] = Field(default_factory=dict, description='提供商特定配置')

    @validator('provider_type')
    def validate_provider_type(cls, v):
        """验证提供商类型"""
        allowed_types = ['OPENAI', 'ANTHROPIC', 'AZURE', 'CUSTOM']
        if v.upper() not in allowed_types:
            raise ValueError(f'Provider type must be one of: {allowed_types}')
        return v.upper()


class LLMProviderCreate(LLMProviderBase):
    """创建LLM提供商的请求模式"""

    api_key: str = Field(..., min_length=1, description='API密钥')

    @validator('api_key')
    def validate_api_key(cls, v):
        """验证API密钥格式"""
        if not v or not v.strip():
            raise ValueError('API key cannot be empty')
        return v.strip()


class LLMProviderUpdate(BaseModel):
    """更新LLM提供商的请求模式"""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description='提供商配置名称')
    api_key: Optional[str] = Field(None, min_length=1, description='API密钥')
    config: Optional[Dict[str, Any]] = Field(None, description='提供商特定配置')

    @validator('api_key')
    def validate_api_key(cls, v):
        """验证API密钥格式"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('API key cannot be empty')
        return v.strip() if v else v


class LLMProviderResponse(LLMProviderBase):
    """LLM提供商响应模式"""

    id: UUID = Field(..., description='提供商配置ID')
    workspace_id: UUID = Field(..., description='工作空间ID')
    created_by: UUID = Field(..., description='创建者ID')
    created_at: datetime = Field(..., description='创建时间')
    updated_at: datetime = Field(..., description='更新时间')

    # 不返回敏感的API密钥，只返回掩码
    api_key_masked: str = Field(..., description='掩码后的API密钥')

    class Config:
        from_attributes = True


class LLMModelInfo(BaseModel):
    """LLM模型信息"""

    model_name: str = Field(..., description='模型名称')
    display_name: Optional[str] = Field(None, description='显示名称')
    max_tokens: Optional[int] = Field(None, description='最大令牌数')
    supports_streaming: bool = Field(default=False, description='是否支持流式输出')
    description: Optional[str] = Field(None, description='模型描述')


class LLMProviderModelsResponse(BaseModel):
    """LLM提供商模型列表响应"""

    provider_id: UUID = Field(..., description='提供商ID')
    provider_name: str = Field(..., description='提供商名称')
    provider_type: str = Field(..., description='提供商类型')
    models: List[LLMModelInfo] = Field(..., description='支持的模型列表')


class LLMCallRequest(BaseModel):
    """LLM调用请求模式"""

    provider_id: UUID = Field(..., description='提供商ID')
    model: str = Field(..., description='模型名称')
    prompt: str = Field(..., min_length=1, description='输入提示词')
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description='温度参数')
    max_tokens: Optional[int] = Field(None, gt=0, description='最大令牌数')
    additional_params: Dict[str, Any] = Field(default_factory=dict, description='其他参数')


class LLMCallResponse(BaseModel):
    """LLM调用响应模式"""

    content: str = Field(..., description='生成的内容')
    model: str = Field(..., description='使用的模型')
    usage: Dict[str, Any] = Field(default_factory=dict, description='使用统计')
    finish_reason: Optional[str] = Field(None, description='完成原因')
    response_time_ms: int = Field(..., description='响应时间（毫秒）')


class LLMProviderValidationRequest(BaseModel):
    """LLM提供商验证请求模式"""

    provider_type: str = Field(..., description='提供商类型')
    api_key: str = Field(..., description='API密钥')
    config: Dict[str, Any] = Field(default_factory=dict, description='提供商配置')


class LLMProviderValidationResponse(BaseModel):
    """LLM提供商验证响应模式"""

    is_valid: bool = Field(..., description='API密钥是否有效')
    error_message: Optional[str] = Field(None, description='错误信息')
    available_models: List[str] = Field(default_factory=list, description='可用模型列表')


class LLMProviderListResponse(BaseModel):
    """LLM提供商列表响应模式"""

    providers: List[LLMProviderResponse] = Field(..., description='提供商列表')
    total: int = Field(..., description='总数量')
    page: int = Field(..., description='当前页码')
    page_size: int = Field(..., description='每页大小')


class LLMProviderUsageStats(BaseModel):
    """LLM提供商使用统计"""

    provider_id: UUID = Field(..., description='提供商ID')
    provider_name: str = Field(..., description='提供商名称')
    total_calls: int = Field(..., description='总调用次数')
    total_tokens: int = Field(..., description='总令牌数')
    success_rate: float = Field(..., description='成功率')
    avg_response_time_ms: float = Field(..., description='平均响应时间（毫秒）')
    last_used_at: Optional[datetime] = Field(None, description='最后使用时间')


def mask_api_key(api_key: str) -> str:
    """掩码API密钥，只显示前4位和后4位字符

    Args:
        api_key: 原始API密钥

    Returns:
        str: 掩码后的API密钥
    """
    if not api_key or len(api_key) <= 8:
        return '*' * len(api_key) if api_key else ''

    return f'{api_key[:4]}{"*" * (len(api_key) - 8)}{api_key[-4:]}'
