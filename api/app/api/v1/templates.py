"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-17 11:38:54
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-17 12:20:05
FilePath: /api/app/api/v1/templates.py
Description: Prompt template management API endpoints.

This module provides RESTful API endpoints for managing prompt templates,
versions, and rendering operations.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.middleware.auth import get_current_user
from app.models.auth.user import User
from app.schemas.template import (
    PromptTemplateCreateRequest,
    PromptTemplateDeleteResponse,
    PromptTemplateListResponse,
    PromptTemplateResponse,
    PromptTemplateUpdateRequest,
    PromptTemplateVersionListResponse,
    PromptTemplateVersionResponse,
    TemplateAnalysisRequest,
    TemplateBulkDeleteRequest,
    TemplateBulkDeleteResponse,
    TemplateRenderRequest,
    TemplateRenderResponse,
    TemplateUsageResponse,
    TemplateValidationResponse,
)
from app.services.prompt_template_service import (
    PromptTemplateService,
    TemplateInUseError,
    TemplateNotFoundError,
    TemplateRenderError,
    TemplateValidationError,
    TemplateVersionNotFoundError,
)

router = APIRouter(prefix='/templates', tags=['Prompt Template Management'])

# Dependency injection definitions
DbSession = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


# ============================================================================
# Template CRUD Endpoints
# ============================================================================


@router.post(
    '/',
    response_model=PromptTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Create a new prompt template',
)
async def create_template(
    template_data: PromptTemplateCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
    workspace_id: UUID,
) -> PromptTemplateResponse:
    """
    Create a new prompt template in the specified workspace.

    Args:
        template_data: Template creation data
        current_user: Current authenticated user
        session: Database session
        workspace_id: ID of the workspace to create template in

    Returns:
        Created template

    Raises:
        HTTPException: If template validation fails
    """
    service = PromptTemplateService(session)

    try:
        template = await service.create_template(
            template_data=template_data,
            workspace_id=workspace_id,
            created_by=current_user.id,
        )

        # Convert variables dict to list for response
        response_data = template.model_dump()
        response_data['variables'] = template.variables.get('variables', [])

        return PromptTemplateResponse(**response_data)
    except TemplateValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to create template: {str(e)}',
        ) from e


@router.get(
    '/',
    response_model=PromptTemplateListResponse,
    summary='List prompt templates in workspace',
)
async def list_templates(
    workspace_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    skip: int = Query(0, ge=0, description='Number of records to skip'),
    limit: int = Query(100, ge=1, le=1000, description='Maximum number of records to return'),
    search: Optional[str] = Query(None, description='Search term for template names'),
) -> PromptTemplateListResponse:
    """
    List all prompt templates in the specified workspace.

    Args:
        workspace_id: ID of the workspace
        current_user: Current authenticated user
        session: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Optional search term for template names

    Returns:
        List of templates and total count
    """
    service = PromptTemplateService(session)

    templates, total = await service.list_templates(
        workspace_id=workspace_id, skip=skip, limit=limit, search=search
    )

    # Convert templates for response
    template_responses = []
    for template in templates:
        response_data = template.model_dump()
        response_data['variables'] = template.variables.get('variables', [])
        template_responses.append(PromptTemplateResponse(**response_data))

    return PromptTemplateListResponse(
        templates=template_responses,
        total=total,
    )


@router.get(
    '/{template_id}',
    response_model=PromptTemplateResponse,
    summary='Get template details',
)
async def get_template(
    template_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> PromptTemplateResponse:
    """
    Get detailed information about a prompt template.

    Args:
        template_id: ID of the template
        current_user: Current authenticated user
        session: Database session

    Returns:
        Template details
    """
    service = PromptTemplateService(session)

    try:
        template = await service.get_template(template_id)

        # Convert variables dict to list for response
        response_data = template.model_dump()
        response_data['variables'] = template.variables.get('variables', [])

        return PromptTemplateResponse(**response_data)
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.put(
    '/{template_id}',
    response_model=PromptTemplateResponse,
    summary='Update template',
)
async def update_template(
    template_id: UUID,
    template_data: PromptTemplateUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> PromptTemplateResponse:
    """
    Update a prompt template's properties.

    Args:
        template_id: ID of the template
        template_data: Template update data
        current_user: Current authenticated user
        session: Database session

    Returns:
        Updated template
    """
    service = PromptTemplateService(session)

    try:
        template = await service.update_template(template_id, template_data)

        # Convert variables dict to list for response
        response_data = template.model_dump()
        response_data['variables'] = template.variables.get('variables', [])

        return PromptTemplateResponse(**response_data)
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except TemplateValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@router.delete(
    '/{template_id}',
    response_model=PromptTemplateDeleteResponse,
    summary='Delete template',
)
async def delete_template(
    template_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> PromptTemplateDeleteResponse:
    """
    Delete a prompt template after checking for references.

    Args:
        template_id: ID of the template
        current_user: Current authenticated user
        session: Database session

    Returns:
        Deletion confirmation
    """
    service = PromptTemplateService(session)

    try:
        await service.delete_template(template_id)
        return PromptTemplateDeleteResponse(
            success=True,
            message='Template deleted successfully',
            template_id=template_id,
        )
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except TemplateInUseError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


# ============================================================================
# Template Version Endpoints
# ============================================================================


@router.get(
    '/{template_id}/versions',
    response_model=PromptTemplateVersionListResponse,
    summary='List template versions',
)
async def list_template_versions(
    template_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    skip: int = Query(0, ge=0, description='Number of records to skip'),
    limit: int = Query(100, ge=1, le=1000, description='Maximum number of records to return'),
) -> PromptTemplateVersionListResponse:
    """
    List all versions of a prompt template.

    Args:
        template_id: ID of the template
        current_user: Current authenticated user
        session: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of template versions and total count
    """
    service = PromptTemplateService(session)

    try:
        versions, total = await service.get_template_versions(
            template_id=template_id, skip=skip, limit=limit
        )

        return PromptTemplateVersionListResponse(
            versions=[PromptTemplateVersionResponse.model_validate(v) for v in versions],
            total=total,
        )
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get(
    '/{template_id}/versions/{version_number}',
    response_model=PromptTemplateVersionResponse,
    summary='Get specific template version',
)
async def get_template_version(
    template_id: UUID,
    version_number: int,
    current_user: CurrentUser,
    session: DbSession,
) -> PromptTemplateVersionResponse:
    """
    Get a specific version of a template.

    Args:
        template_id: ID of the template
        version_number: Version number to retrieve
        current_user: Current authenticated user
        session: Database session

    Returns:
        Template version details
    """
    service = PromptTemplateService(session)

    try:
        version = await service.get_template_version(template_id, version_number)
        return PromptTemplateVersionResponse.model_validate(version)
    except (TemplateNotFoundError, TemplateVersionNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    '/{template_id}/versions/{version_number}/revert',
    response_model=PromptTemplateResponse,
    summary='Revert to template version',
)
async def revert_to_version(
    template_id: UUID,
    version_number: int,
    current_user: CurrentUser,
    session: DbSession,
) -> PromptTemplateResponse:
    """
    Revert template to a previous version.

    Args:
        template_id: ID of the template
        version_number: Version number to revert to
        current_user: Current authenticated user
        session: Database session

    Returns:
        Updated template
    """
    service = PromptTemplateService(session)

    try:
        template = await service.revert_to_version(template_id, version_number)

        # Convert variables dict to list for response
        response_data = template.model_dump()
        response_data['variables'] = template.variables.get('variables', [])

        return PromptTemplateResponse(**response_data)
    except (TemplateNotFoundError, TemplateVersionNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


# ============================================================================
# Template Rendering Endpoints
# ============================================================================


@router.post(
    '/{template_id}/render',
    response_model=TemplateRenderResponse,
    summary='Render template with variables',
)
async def render_template(
    template_id: UUID,
    render_data: TemplateRenderRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> TemplateRenderResponse:
    """
    Render a template with provided variables.

    Args:
        template_id: ID of the template
        render_data: Variables to substitute in template
        current_user: Current authenticated user
        session: Database session

    Returns:
        Rendered template content
    """
    service = PromptTemplateService(session)

    try:
        rendered_content = await service.render_template(template_id, render_data)

        return TemplateRenderResponse(
            rendered_content=rendered_content,
            template_id=template_id,
            variables_used=render_data.variables,
        )
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except TemplateRenderError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@router.post(
    '/validate',
    response_model=TemplateValidationResponse,
    summary='Validate template content',
)
async def validate_template_content(
    analysis_data: TemplateAnalysisRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> TemplateValidationResponse:
    """
    Validate template content and return analysis.

    Args:
        analysis_data: Template content to analyze
        current_user: Current authenticated user
        session: Database session

    Returns:
        Validation results and template analysis
    """
    service = PromptTemplateService(session)

    analysis = await service.validate_template_content(analysis_data.content)

    return TemplateValidationResponse(
        is_valid=analysis['is_valid'],
        errors=analysis['errors'],
        variables=analysis['variables'],
        variable_count=analysis['variable_count'],
        character_count=analysis['character_count'],
        line_count=analysis['line_count'],
    )


# ============================================================================
# Template Usage and Reference Endpoints
# ============================================================================


@router.get(
    '/{template_id}/usage',
    response_model=TemplateUsageResponse,
    summary='Get template usage information',
)
async def get_template_usage(
    template_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> TemplateUsageResponse:
    """
    Get detailed usage information for a template.

    Args:
        template_id: ID of the template
        current_user: Current authenticated user
        session: Database session

    Returns:
        Template usage information
    """
    service = PromptTemplateService(session)

    try:
        usage_info = await service.get_template_usage(template_id)
        return TemplateUsageResponse(**usage_info)
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


# ============================================================================
# Bulk Operations Endpoints
# ============================================================================


@router.post(
    '/bulk-delete',
    response_model=TemplateBulkDeleteResponse,
    summary='Delete multiple templates',
)
async def bulk_delete_templates(
    delete_data: TemplateBulkDeleteRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> TemplateBulkDeleteResponse:
    """
    Delete multiple templates in bulk.

    Args:
        delete_data: List of template IDs to delete
        current_user: Current authenticated user
        session: Database session

    Returns:
        Bulk deletion results
    """
    service = PromptTemplateService(session)

    deleted_count, failed_deletions = await service.bulk_delete_templates(delete_data.template_ids)

    return TemplateBulkDeleteResponse(
        deleted_count=deleted_count,
        failed_deletions=failed_deletions,
        success=len(failed_deletions) == 0,
    )
