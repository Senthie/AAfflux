"""
Upload Node Data Entities

Defines the data structures for upload node configuration.
"""

from typing import Optional

from pydantic import Field, field_validator
from pydantic_core import PydanticCustomError

from app.engine.nodes.base import BaseNodeData


class UploadNodeData(BaseNodeData):
    """Upload node configuration data.

    Attributes:
        max_size_mb: Maximum file size in MB (default: 100)
        allowed_types: List of allowed file types (default: ['png'])
        file_data: File data from frontend upload (contains filename, content, size, etc.)
    """

    max_size_mb: int = Field(default=100, frozen=True)
    allowed_types: list[str] = Field(default=['png'], frozen=True)
    file_data: Optional[dict] = Field(default=None)
    file_id: Optional[str] = Field(default=None)

    @field_validator('max_size_mb', mode='before')
    @classmethod
    def validate_max_size(cls, max_size_mb: int) -> int:
        """Validate maximum file size."""
        if not isinstance(max_size_mb, int):
            max_size_mb = int(max_size_mb)
        if max_size_mb <= 0:
            raise PydanticCustomError(
                'max_size_error',
                'max_size_mb must be a positive integer',
            )
        if max_size_mb > 100:
            raise PydanticCustomError(
                'max_size_error',
                'max_size_mb cannot exceed 100 MB',
            )
        return max_size_mb

    @field_validator('allowed_types', mode='before')
    @classmethod
    def validate_allowed_types(cls, allowed_types: list[str] | str) -> list[str]:
        """Validate allowed file types."""
        # Handle string input (from JSON config)
        if isinstance(allowed_types, str):
            allowed_types = [t.strip() for t in allowed_types.split(',')]

        if not isinstance(allowed_types, list) or not allowed_types:
            raise PydanticCustomError(
                'allowed_types_error',
                'allowed_types must be a non-empty list',
            )

        # Currently only support png
        supported_types = {'png'}
        for file_type in allowed_types:
            if file_type.lower() not in supported_types:
                raise PydanticCustomError(
                    'allowed_types_error',
                    'Unsupported file type: {file_type}. Only png is supported.',
                    {'file_type': file_type},
                )

        return [t.lower() for t in allowed_types]
