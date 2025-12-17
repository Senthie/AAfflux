"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-17 11:36:46
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-17 12:20:45
FilePath: /api/app/utils/template_renderer.py
Description:Template rendering and variable parsing utilities.

This module provides functionality for rendering prompt templates with variable substitution
and extracting variables from template content.

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

import re
from typing import Any, Dict, List, Set


class TemplateRenderError(Exception):
    """Exception raised when template rendering fails."""

    pass


class TemplateRenderer:
    """Template renderer for prompt templates with variable substitution."""

    # Regular expression to match {{variable_name}} patterns
    VARIABLE_PATTERN = re.compile(r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}')

    @classmethod
    def extract_variables(cls, template_content: str) -> List[str]:
        """Extract variable names from template content.

        Args:
            template_content: Template content with {{variable_name}} placeholders

        Returns:
            List of unique variable names found in the template

        Example:
            >>> TemplateRenderer.extract_variables("Hello {{name}}, your age is {{age}}")
            ['name', 'age']
        """
        matches = cls.VARIABLE_PATTERN.findall(template_content)
        # Return unique variables while preserving order
        seen: Set[str] = set()
        variables = []
        for var in matches:
            if var not in seen:
                variables.append(var)
                seen.add(var)
        return variables

    @classmethod
    def validate_template_syntax(cls, template_content: str) -> tuple[bool, List[str]]:
        """Validate template syntax for proper variable placeholders.

        Args:
            template_content: Template content to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check for unmatched braces
        open_braces = template_content.count('{')
        close_braces = template_content.count('}')

        if open_braces != close_braces:
            errors.append('Unmatched braces in template')

        # Find all brace patterns (both single and double)
        all_brace_patterns = re.findall(r'\{[^}]*\}+', template_content)

        for pattern in all_brace_patterns:
            # Check if it's a valid double-brace pattern
            if not re.match(r'^\{\{[a-zA-Z_][a-zA-Z0-9_]*\}\}$', pattern):
                errors.append(f'Invalid variable pattern: {pattern}')

        return len(errors) == 0, errors

    @classmethod
    def render_template(cls, template_content: str, variables: Dict[str, Any]) -> str:
        """Render template by replacing variable placeholders with values.

        Args:
            template_content: Template content with {{variable_name}} placeholders
            variables: Dictionary mapping variable names to their values

        Returns:
            Rendered template with variables substituted

        Raises:
            TemplateRenderError: If template syntax is invalid or required variables are missing

        Example:
            >>> template = "Hello {{name}}, your age is {{age}}"
            >>> variables = {"name": "John", "age": 30}
            >>> TemplateRenderer.render_template(template, variables)
            "Hello John, your age is 30"
        """
        # Validate template syntax first
        is_valid, errors = cls.validate_template_syntax(template_content)
        if not is_valid:
            raise TemplateRenderError(f'Invalid template syntax: {"; ".join(errors)}')

        # Extract required variables
        required_vars = cls.extract_variables(template_content)

        # Check for missing variables
        missing_vars = [var for var in required_vars if var not in variables]
        if missing_vars:
            raise TemplateRenderError(f'Missing required variables: {", ".join(missing_vars)}')

        # Render template
        rendered = template_content
        for var_name in required_vars:
            placeholder = f'{{{{{var_name}}}}}'
            value = str(variables[var_name])  # Convert to string for substitution
            rendered = rendered.replace(placeholder, value)

        return rendered

    @classmethod
    def get_template_info(cls, template_content: str) -> Dict[str, Any]:
        """Get comprehensive information about a template.

        Args:
            template_content: Template content to analyze

        Returns:
            Dictionary containing template analysis information
        """
        is_valid, errors = cls.validate_template_syntax(template_content)
        variables = cls.extract_variables(template_content)

        return {
            'is_valid': is_valid,
            'errors': errors,
            'variables': variables,
            'variable_count': len(variables),
            'character_count': len(template_content),
            'line_count': template_content.count('\n') + 1 if template_content else 0,
        }
