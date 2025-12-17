"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-17 11:37:10
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-17 12:20:31
FilePath: /api/app/schemas/template.py
Description:Prompt template-related Pydantic schemas for request/response validation.

This module defines the data transfer objects (DTOs) for prompt template management,
including schemas for templates, versions, and rendering operations.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Template Schemas
# ============================================================================


class PromptTemplateCreateRequest(BaseModel):
    """Request schema for creating a prompt template."""

    name: str = Field(..., min_length=1, max_length=255, description='Template name')
    content: str = Field(
        ..., min_length=1, description='Template content with {{variable}} placeholders'
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate template name."""
        if not v.strip():
            raise ValueError('Template name cannot be empty or whitespace only')
        return v.strip()


class PromptTemplateUpdateRequest(BaseModel):
    """Request schema for updating a prompt template."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description='Template name')
    content: Optional[str] = Field(
        None, min_length=1, description='Template content with {{variable}} placeholders'
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate template name."""
        if v is not None and not v.strip():
            raise ValueError('Template name cannot be empty or whitespace only')
        return v.strip() if v else v


class PromptTemplateResponse(BaseModel):
    """Response schema for a prompt template."""

    id: UUID
    name: str
    workspace_id: UUID
    content: str
    variables: List[str]
    version: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False

    model_config = {'from_attributes': True}


class PromptTemplateListResponse(BaseModel):
    """Response schema for prompt template list."""

    templates: List[PromptTemplateResponse]
    total: int


class PromptTemplateDeleteResponse(BaseModel):
    """Response schema for prompt template deletion."""

    success: bool
    message: str
    template_id: UUID


# ============================================================================
# Template Version Schemas
# ============================================================================


class PromptTemplateVersionResponse(BaseModel):
    """Response schema for a prompt template version."""

    id: UUID
    template_id: UUID
    version: int
    content: str
    created_at: datetime
    is_deleted: bool = False

    model_config = {'from_attributes': True}


class PromptTemplateVersionListResponse(BaseModel):
    """Response schema for template version list."""

    versions: List[PromptTemplateVersionResponse]
    total: int


# ============================================================================
# Template Rendering Schemas
# ============================================================================


class TemplateRenderRequest(BaseModel):
    """Request schema for rendering a template."""

    variables: Dict[str, Any] = Field(..., description='Variables to substitute in template')


class TemplateRenderResponse(BaseModel):
    """Response schema for template rendering."""

    rendered_content: str = Field(..., description='Template with variables substituted')
    template_id: UUID
    variables_used: Dict[str, Any]


class TemplateValidationResponse(BaseModel):
    """Response schema for template validation."""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    variables: List[str] = Field(default_factory=list)
    variable_count: int
    character_count: int
    line_count: int


# ============================================================================
# Template Analysis Schemas
# ============================================================================


class TemplateAnalysisRequest(BaseModel):
    """Request schema for analyzing template content."""

    content: str = Field(..., min_length=1, description='Template content to analyze')


class TemplateUsageResponse(BaseModel):
    """Response schema for template usage information."""

    template_id: UUID
    template_name: str
    usage_count: int
    workflows_using: List[Dict[str, Any]] = Field(default_factory=list)
    can_delete: bool


# ============================================================================
# Bulk Operations Schemas
# ============================================================================


class TemplateBulkDeleteRequest(BaseModel):
    """Request schema for bulk template deletion."""

    template_ids: List[UUID] = Field(
        ..., min_length=1, description='List of template IDs to delete'
    )


class TemplateBulkDeleteResponse(BaseModel):
    """Response schema for bulk template deletion."""

    deleted_count: int
    failed_deletions: List[Dict[str, str]] = Field(default_factory=list)
    success: bool


# ============================================================================
# Template Import/Export Schemas
# ============================================================================


class TemplateExportResponse(BaseModel):
    """Response schema for template export."""

    template: PromptTemplateResponse
    versions: List[PromptTemplateVersionResponse]
    export_timestamp: datetime


class TemplateImportRequest(BaseModel):
    """Request schema for template import."""

    name: str = Field(..., min_length=1, max_length=255, description='Template name')
    content: str = Field(..., min_length=1, description='Template content')
    preserve_versions: bool = Field(default=False, description='Whether to import version history')
    versions: Optional[List[Dict[str, Any]]] = Field(
        default=None, description='Version history to import'
    )


class TemplateImportResponse(BaseModel):
    """Response schema for template import."""

    template: PromptTemplateResponse
    imported_versions: int
    success: bool
    warnings: List[str] = Field(default_factory=list)
