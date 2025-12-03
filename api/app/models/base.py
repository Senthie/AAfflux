"""Base model classes and mixins for the application."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class BaseModel(SQLModel):
    """Abstract base class for all data models.

    Provides common fields and behaviors that all models should have.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary representation.

        Returns:
            Dictionary containing all model fields and their values.
        """
        result = {}
        for field_name in self.__class__.model_fields:
            value = getattr(self, field_name)
            if isinstance(value, UUID):
                result[field_name] = str(value)
            elif isinstance(value, datetime):
                result[field_name] = value.isoformat()
            else:
                result[field_name] = value
        return result

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary data.

        Args:
            data: Dictionary containing field names and new values.
        """
        for field_name, value in data.items():
            if hasattr(self, field_name):
                setattr(self, field_name, value)

        # Update timestamp if available
        if hasattr(self, "updated_at"):
            setattr(self, "updated_at", datetime.now(timezone.utc))

    def __eq__(self, other: object) -> bool:
        """Check equality based on all field values.

        Args:
            other: Another model instance to compare with.

        Returns:
            True if all fields are equal, False otherwise.
        """
        if not isinstance(other, self.__class__):
            return False

        for field_name in self.__class__.model_fields:
            if getattr(self, field_name) != getattr(other, field_name):
                return False

        return True


class TimestampMixin:
    """Mixin class providing timestamp fields and related methods."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now(timezone.utc)


class SoftDeleteMixin:
    """Mixin class providing soft delete functionality."""

    deleted_at: Optional[datetime] = Field(default=None)
    is_deleted: bool = Field(default=False)

    def soft_delete(self) -> None:
        """Mark the record as deleted without removing it from database."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """Mixin class providing audit fields for tracking who created/updated records."""

    created_by: UUID = Field(foreign_key="user.id")
    updated_by: Optional[UUID] = Field(default=None, foreign_key="user.id")


class WorkspaceMixin:
    """Mixin class providing workspace isolation functionality."""

    workspace_id: UUID = Field(foreign_key="workspace.id", index=True)
