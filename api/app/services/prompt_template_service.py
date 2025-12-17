"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-17 11:37:40
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-17 12:20:17
FilePath: /api/app/services/prompt_template_service.py
Description:Prompt template management service.

This module provides CRUD operations for prompt templates and versions,
including template rendering, version management, and reference checking.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.application.prompt_template import PromptTemplate, PromptTemplateVersion
from app.schemas.template import (
    PromptTemplateCreateRequest,
    PromptTemplateUpdateRequest,
    TemplateRenderRequest,
)
from app.utils.template_renderer import TemplateRenderer, TemplateRenderError


class TemplateNotFoundError(Exception):
    """Exception raised when template is not found."""

    pass


class TemplateVersionNotFoundError(Exception):
    """Exception raised when template version is not found."""

    pass


class TemplateValidationError(Exception):
    """Exception raised when template validation fails."""

    pass


class TemplateInUseError(Exception):
    """Exception raised when trying to delete a template that is in use."""

    pass


class PromptTemplateService:
    """Service for managing prompt templates and versions."""

    def __init__(self, db: AsyncSession):
        """Initialize prompt template service.

        Args:
            db: Async database session
        """
        self.db = db
        self.renderer = TemplateRenderer

    # ========================================================================
    # Template CRUD Operations
    # ========================================================================

    async def create_template(
        self, template_data: PromptTemplateCreateRequest, workspace_id: UUID, created_by: UUID
    ) -> PromptTemplate:
        """Create a new prompt template.

        Args:
            template_data: Template creation data
            workspace_id: ID of the workspace
            created_by: ID of the user creating the template

        Returns:
            Created PromptTemplate object

        Raises:
            TemplateValidationError: If template syntax is invalid
        """
        # Validate template syntax
        is_valid, errors = self.renderer.validate_template_syntax(template_data.content)
        if not is_valid:
            raise TemplateValidationError(f'Invalid template syntax: {"; ".join(errors)}')

        # Extract variables from template
        variables = self.renderer.extract_variables(template_data.content)

        # Create template
        template = PromptTemplate(
            name=template_data.name,
            workspace_id=workspace_id,
            content=template_data.content,
            variables={'variables': variables},  # Store as dict for JSONB compatibility
            version=1,
            created_by=created_by,
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        # Create initial version record
        version = PromptTemplateVersion(
            template_id=template.id,
            version=1,
            content=template_data.content,
        )

        self.db.add(version)
        await self.db.commit()

        return template

    async def get_template(self, template_id: UUID) -> PromptTemplate:
        """Get a template by ID.

        Args:
            template_id: ID of the template

        Returns:
            PromptTemplate object

        Raises:
            TemplateNotFoundError: If template is not found
        """
        template = await self.db.get(PromptTemplate, template_id)
        if not template or template.is_deleted:
            raise TemplateNotFoundError(f'Template {template_id} not found')

        return template

    async def list_templates(
        self, workspace_id: UUID, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> Tuple[List[PromptTemplate], int]:
        """List templates in a workspace.

        Args:
            workspace_id: ID of the workspace
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Optional search term for template names

        Returns:
            Tuple of (list of templates, total count)
        """
        # Build query
        statement = (
            select(PromptTemplate)
            .where(PromptTemplate.workspace_id == workspace_id)
            .where(~PromptTemplate.is_deleted)
        )

        # Add search filter if provided
        if search:
            statement = statement.where(PromptTemplate.name.ilike(f'%{search}%'))

        # Apply pagination
        statement = statement.offset(skip).limit(limit)

        # Execute query
        result = await self.db.execute(statement)
        templates = result.scalars().all()

        # Count total
        count_statement = (
            select(PromptTemplate)
            .where(PromptTemplate.workspace_id == workspace_id)
            .where(~PromptTemplate.is_deleted)
        )

        if search:
            count_statement = count_statement.where(PromptTemplate.name.ilike(f'%{search}%'))

        count_result = await self.db.execute(count_statement)
        total = len(count_result.scalars().all())

        return list(templates), total

    async def update_template(
        self, template_id: UUID, template_data: PromptTemplateUpdateRequest
    ) -> PromptTemplate:
        """Update a template and create a new version if content changed.

        Args:
            template_id: ID of the template
            template_data: Template update data

        Returns:
            Updated PromptTemplate object

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateValidationError: If new template syntax is invalid
        """
        template = await self.get_template(template_id)

        # Track if content changed to create new version
        content_changed = False

        # Update fields
        if template_data.name is not None:
            template.name = template_data.name

        if template_data.content is not None:
            # Validate new template syntax
            is_valid, errors = self.renderer.validate_template_syntax(template_data.content)
            if not is_valid:
                raise TemplateValidationError(f'Invalid template syntax: {"; ".join(errors)}')

            # Check if content actually changed
            if template.content != template_data.content:
                content_changed = True
                template.content = template_data.content

                # Update variables
                variables = self.renderer.extract_variables(template_data.content)
                template.variables = {'variables': variables}

                # Increment version
                template.version += 1

        template.touch()

        await self.db.commit()
        await self.db.refresh(template)

        # Create new version record if content changed
        if content_changed:
            version = PromptTemplateVersion(
                template_id=template.id,
                version=template.version,
                content=template.content,
            )

            self.db.add(version)
            await self.db.commit()

        return template

    async def delete_template(self, template_id: UUID) -> None:
        """Delete a template after checking for references.

        Args:
            template_id: ID of the template

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateInUseError: If template is referenced by workflows
        """
        template = await self.get_template(template_id)

        # Check if template is in use
        is_in_use = await self.check_template_references(template_id)
        if is_in_use:
            raise TemplateInUseError(f'Template {template_id} is in use and cannot be deleted')

        # Soft delete the template
        template.soft_delete()

        # Soft delete all versions
        versions_statement = select(PromptTemplateVersion).where(
            PromptTemplateVersion.template_id == template_id
        )
        versions_result = await self.db.execute(versions_statement)
        versions = versions_result.scalars().all()

        for version in versions:
            if not version.is_deleted:
                version.soft_delete()

        await self.db.commit()

    # ========================================================================
    # Template Version Management
    # ========================================================================

    async def get_template_versions(
        self, template_id: UUID, skip: int = 0, limit: int = 100
    ) -> Tuple[List[PromptTemplateVersion], int]:
        """Get all versions of a template.

        Args:
            template_id: ID of the template
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of versions, total count)
        """
        # Verify template exists
        await self.get_template(template_id)

        # Query versions
        statement = (
            select(PromptTemplateVersion)
            .where(PromptTemplateVersion.template_id == template_id)
            .where(~PromptTemplateVersion.is_deleted)
            .order_by(PromptTemplateVersion.version.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(statement)
        versions = result.scalars().all()

        # Count total
        count_statement = (
            select(PromptTemplateVersion)
            .where(PromptTemplateVersion.template_id == template_id)
            .where(~PromptTemplateVersion.is_deleted)
        )

        count_result = await self.db.execute(count_statement)
        total = len(count_result.scalars().all())

        return list(versions), total

    async def get_template_version(
        self, template_id: UUID, version_number: int
    ) -> PromptTemplateVersion:
        """Get a specific version of a template.

        Args:
            template_id: ID of the template
            version_number: Version number to retrieve

        Returns:
            PromptTemplateVersion object

        Raises:
            TemplateVersionNotFoundError: If version is not found
        """
        # Verify template exists
        await self.get_template(template_id)

        statement = select(PromptTemplateVersion).where(
            PromptTemplateVersion.template_id == template_id,
            PromptTemplateVersion.version == version_number,
            ~PromptTemplateVersion.is_deleted,
        )

        result = await self.db.execute(statement)
        version = result.scalar_one_or_none()

        if not version:
            raise TemplateVersionNotFoundError(
                f'Version {version_number} of template {template_id} not found'
            )

        return version

    async def revert_to_version(self, template_id: UUID, version_number: int) -> PromptTemplate:
        """Revert template to a previous version.

        Args:
            template_id: ID of the template
            version_number: Version number to revert to

        Returns:
            Updated PromptTemplate object

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateVersionNotFoundError: If version is not found
        """
        template = await self.get_template(template_id)
        version = await self.get_template_version(template_id, version_number)

        # Update template with version content
        template.content = version.content

        # Update variables
        variables = self.renderer.extract_variables(version.content)
        template.variables = {'variables': variables}

        # Increment version number
        template.version += 1
        template.touch()

        await self.db.commit()
        await self.db.refresh(template)

        # Create new version record
        new_version = PromptTemplateVersion(
            template_id=template.id,
            version=template.version,
            content=template.content,
        )

        self.db.add(new_version)
        await self.db.commit()

        return template

    # ========================================================================
    # Template Rendering Operations
    # ========================================================================

    async def render_template(self, template_id: UUID, render_data: TemplateRenderRequest) -> str:
        """Render a template with provided variables.

        Args:
            template_id: ID of the template
            render_data: Rendering request data

        Returns:
            Rendered template content

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateRenderError: If rendering fails
        """
        template = await self.get_template(template_id)

        try:
            rendered_content = self.renderer.render_template(
                template.content, render_data.variables
            )
            return rendered_content
        except TemplateRenderError as e:
            raise e

    async def validate_template_content(self, content: str) -> Dict[str, Any]:
        """Validate template content and return analysis.

        Args:
            content: Template content to validate

        Returns:
            Dictionary containing validation results and analysis
        """
        return self.renderer.get_template_info(content)

    # ========================================================================
    # Reference Checking Operations
    # ========================================================================

    async def check_template_references(self, template_id: UUID) -> bool:
        """Check if a template is referenced by any workflows.

        Args:
            template_id: ID of the template

        Returns:
            True if template is in use, False otherwise
        """
        # TODO: Implement actual reference checking when workflow nodes are implemented
        # For now, we'll return False to allow deletion
        # This should check:
        # 1. LLM nodes that reference this template
        # 2. Any other components that might use templates

        # Placeholder implementation
        return False

    async def get_template_usage(self, template_id: UUID) -> Dict[str, Any]:
        """Get detailed usage information for a template.

        Args:
            template_id: ID of the template

        Returns:
            Dictionary containing usage information
        """
        template = await self.get_template(template_id)

        # TODO: Implement actual usage tracking when workflow nodes are implemented
        # This should return:
        # - List of workflows using this template
        # - Usage count
        # - Last used timestamp

        return {
            'template_id': template_id,
            'template_name': template.name,
            'usage_count': 0,
            'workflows_using': [],
            'can_delete': True,
        }

    # ========================================================================
    # Bulk Operations
    # ========================================================================

    async def bulk_delete_templates(
        self, template_ids: List[UUID]
    ) -> Tuple[int, List[Dict[str, str]]]:
        """Delete multiple templates in bulk.

        Args:
            template_ids: List of template IDs to delete

        Returns:
            Tuple of (deleted_count, failed_deletions)
        """
        deleted_count = 0
        failed_deletions = []

        for template_id in template_ids:
            try:
                await self.delete_template(template_id)
                deleted_count += 1
            except (TemplateNotFoundError, TemplateInUseError) as e:
                failed_deletions.append({'template_id': str(template_id), 'error': str(e)})

        return deleted_count, failed_deletions
