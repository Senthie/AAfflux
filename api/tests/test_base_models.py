"""Tests for base model classes and mixins."""

import pytest
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from hypothesis import given, strategies as st
import inspect

from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin, AuditMixin, WorkspaceMixin


# Model classes for testing purposes
class SampleUser(BaseModel, TimestampMixin, table=True):
    """Sample model combining BaseModel and TimestampMixin."""

    email: str
    name: str


class SampleDocument(BaseModel, TimestampMixin, SoftDeleteMixin, table=True):
    """Sample model combining multiple mixins."""

    title: str
    content: str


class SampleWorkspaceItem(BaseModel, TimestampMixin, WorkspaceMixin, table=True):
    """Sample model with workspace isolation."""

    name: str


class SampleAuditedItem(BaseModel, TimestampMixin, AuditMixin, table=True):
    """Sample model with audit fields."""

    name: str


class TestBaseModel:
    """Test cases for BaseModel functionality."""

    def test_base_model_has_id_field(self):
        """Test that BaseModel provides UUID id field."""
        user = SampleUser(email="test@example.com", name="Test User")
        assert hasattr(user, "id")
        assert isinstance(user.id, UUID)

    def test_to_dict_serialization(self):
        """Test model serialization to dictionary."""
        user = SampleUser(email="test@example.com", name="Test User")
        result = user.to_dict()

        assert isinstance(result, dict)
        assert "id" in result
        assert "email" in result
        assert "name" in result
        assert "created_at" in result
        assert "updated_at" in result

        # Check UUID is converted to string
        assert isinstance(result["id"], str)
        # Check datetime is converted to ISO format
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)

    def test_update_from_dict(self):
        """Test model update from dictionary."""
        user = SampleUser(email="test@example.com", name="Test User")
        original_updated_at = user.updated_at

        # Small delay to ensure timestamp difference
        import time

        time.sleep(0.001)

        user.update_from_dict({"name": "Updated Name", "email": "updated@example.com"})

        assert user.name == "Updated Name"
        assert user.email == "updated@example.com"
        assert user.updated_at > original_updated_at

    def test_model_equality(self):
        """Test model equality comparison."""
        user1 = SampleUser(email="test@example.com", name="Test User")
        user2 = SampleUser(email="test@example.com", name="Test User")
        user3 = SampleUser(email="different@example.com", name="Test User")

        # Set same ID and timestamps for comparison
        user2.id = user1.id
        user2.created_at = user1.created_at
        user2.updated_at = user1.updated_at

        assert user1 == user2
        assert user1 != user3


class TestTimestampMixin:
    """Test cases for TimestampMixin functionality."""

    def test_timestamp_fields_auto_set(self):
        """Test that timestamp fields are automatically set on creation."""
        user = SampleUser(email="test@example.com", name="Test User")

        assert hasattr(user, "created_at")
        assert hasattr(user, "updated_at")
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_touch_method(self):
        """Test the touch method updates updated_at timestamp."""
        user = SampleUser(email="test@example.com", name="Test User")
        original_updated_at = user.updated_at

        # Small delay to ensure timestamp difference
        import time

        time.sleep(0.001)

        user.touch()

        assert user.updated_at > original_updated_at
        # created_at should remain unchanged
        assert user.created_at != user.updated_at


class TestSoftDeleteMixin:
    """Test cases for SoftDeleteMixin functionality."""

    def test_soft_delete_fields(self):
        """Test that soft delete fields are properly initialized."""
        doc = SampleDocument(title="Test Doc", content="Content")

        assert hasattr(doc, "deleted_at")
        assert hasattr(doc, "is_deleted")
        assert doc.deleted_at is None
        assert doc.is_deleted is False

    def test_soft_delete_method(self):
        """Test soft delete functionality."""
        doc = SampleDocument(title="Test Doc", content="Content")

        doc.soft_delete()

        assert doc.is_deleted is True
        assert doc.deleted_at is not None
        assert isinstance(doc.deleted_at, datetime)

    def test_restore_method(self):
        """Test restore functionality."""
        doc = SampleDocument(title="Test Doc", content="Content")

        # First soft delete
        doc.soft_delete()
        assert doc.is_deleted is True

        # Then restore
        doc.restore()
        assert doc.is_deleted is False
        assert doc.deleted_at is None


class TestMixinCombination:
    """Test cases for combining multiple mixins."""

    def test_multiple_mixins_compatibility(self):
        """Test that multiple mixins work together without conflicts."""
        doc = SampleDocument(title="Test Doc", content="Content")

        # Should have all fields from all mixins
        assert hasattr(doc, "id")  # BaseModel
        assert hasattr(doc, "created_at")  # TimestampMixin
        assert hasattr(doc, "updated_at")  # TimestampMixin
        assert hasattr(doc, "deleted_at")  # SoftDeleteMixin
        assert hasattr(doc, "is_deleted")  # SoftDeleteMixin

        # All functionality should work
        doc.touch()
        doc.soft_delete()
        doc.restore()

        result = doc.to_dict()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_workspace_mixin(self):
        """Test WorkspaceMixin functionality."""
        workspace_id = uuid4()
        item = SampleWorkspaceItem(name="Test Item", workspace_id=workspace_id)

        assert hasattr(item, "workspace_id")
        assert item.workspace_id == workspace_id

    def test_audit_mixin(self):
        """Test AuditMixin functionality."""
        created_by = uuid4()
        updated_by = uuid4()
        item = SampleAuditedItem(name="Test Item", created_by=created_by, updated_by=updated_by)

        assert hasattr(item, "created_by")
        assert hasattr(item, "updated_by")
        assert item.created_by == created_by
        assert item.updated_by == updated_by


class TestBaseModelPropertyTests:
    """Property-based tests for BaseModel functionality."""

    def create_test_model_class(self, class_name: str):
        """Create a test model class that inherits from BaseModel."""

        class TestModel(BaseModel):
            """Dynamically created test model for property testing."""

            name: str

        # Set the class name for better test output
        TestModel.__name__ = class_name
        TestModel.__qualname__ = class_name

        return TestModel

    @given(
        st.text(min_size=1, max_size=50).filter(
            lambda x: x.isidentifier() and not x.startswith("_")
        )
    )
    def test_base_class_field_inheritance_consistency(self, class_name: str):
        """
        # Feature: model-base-refactor, Property 1: 基类字段继承一致性

        Property test to verify that any model class inheriting from BaseModel
        contains an id field with UUID type.

        **Validates: Requirements 1.2**
        """
        # Create a test model class that inherits from BaseModel
        TestModel = self.create_test_model_class(class_name)

        # Check that id field is defined in the model fields (this is how Pydantic/SQLModel works)
        assert (
            "id" in TestModel.model_fields
        ), f"Model {class_name} should have 'id' in model_fields"

        # Verify the id field type is UUID
        id_field = TestModel.model_fields["id"]
        assert (
            id_field.annotation == UUID
        ), f"Model {class_name} id field should be of type UUID, got {id_field.annotation}"

        # Create an instance and verify the id field behavior
        instance = TestModel(name="test")

        # Verify instance has id attribute
        assert hasattr(instance, "id"), f"Model instance should have 'id' attribute"

        # Verify the id is actually a UUID instance
        assert isinstance(
            instance.id, UUID
        ), f"Model instance id should be UUID instance, got {type(instance.id)}"

        # Verify id is set (not None)
        assert instance.id is not None, f"Model instance id should not be None"
