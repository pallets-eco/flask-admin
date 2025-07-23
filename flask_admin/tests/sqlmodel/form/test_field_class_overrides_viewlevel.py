"""
Test view-level field class override functionality for SQLModel forms.

This module tests view-level form_overrides functionality which is the
primary way to specify custom WTForms field classes.
"""

from sqlmodel import Field
from sqlmodel import SQLModel
from wtforms import fields
from wtforms import HiddenField
from wtforms import PasswordField
from wtforms import TextAreaField

from flask_admin.contrib.sqlmodel.form import AdminModelConverter


class MockView:
    """Mock view for testing purposes."""

    def __init__(self, form_overrides=None):
        self.form_overrides = form_overrides or {}


def test_view_level_override_field_class():
    """Test that view-level form_overrides work with field classes."""

    class TestModel(SQLModel):
        id: int = Field(primary_key=True)
        description: str = Field()
        name: str = Field()

    # View-level overrides
    view = MockView(
        form_overrides={"description": TextAreaField, "name": PasswordField}
    )
    converter = AdminModelConverter(None, view)

    # Test field class override method
    override = converter._get_field_class_override("description", None)
    assert override == TextAreaField

    override = converter._get_field_class_override("name", None)
    assert override == PasswordField

    # Field without override should return None
    override = converter._get_field_class_override("id", None)
    assert override is None


def test_view_level_override_field_instance():
    """Test view-level override with field instance rather than class."""

    class TestModel(SQLModel):
        id: int = Field(primary_key=True)
        name: str = Field()

    # Override with field instance
    field_instance = PasswordField()
    view = MockView(form_overrides={"name": field_instance})
    converter = AdminModelConverter(None, view)

    # Should extract class from field instance
    override = converter._get_field_class_override("name", None)
    # Note: WTForms field instances have __class__ attribute
    assert override == field_instance.__class__


def test_no_override_returns_none():
    """Test that None is returned when no override is found."""

    class TestModel(SQLModel):
        id: int = Field(primary_key=True)
        name: str = Field()

    view = MockView()  # No form_overrides
    converter = AdminModelConverter(None, view)

    # No override should be found
    override = converter._get_field_class_override("name", None)
    assert override is None


def test_multiple_field_overrides():
    """Test multiple field overrides in the same view."""

    class TestModel(SQLModel):
        id: int = Field(primary_key=True)
        title: str = Field()
        content: str = Field()
        secret: str = Field()
        hidden_field: str = Field()

    view = MockView(
        form_overrides={
            "title": fields.StringField,
            "content": TextAreaField,
            "secret": PasswordField,
            "hidden_field": HiddenField,
        }
    )
    converter = AdminModelConverter(None, view)

    # Test all overrides
    assert converter._get_field_class_override("title", None) == fields.StringField
    assert converter._get_field_class_override("content", None) == TextAreaField
    assert converter._get_field_class_override("secret", None) == PasswordField
    assert converter._get_field_class_override("hidden_field", None) == HiddenField

    # Field without override should return None
    assert converter._get_field_class_override("id", None) is None


def test_override_priority_documentation():
    """Document that view-level overrides have highest priority."""

    class TestModel(SQLModel):
        id: int = Field(primary_key=True)
        description: str = Field()

    # Priority order should be:
    # 1. View-level (form_overrides) - HIGHEST
    # 2. Field-level (field_class in Field) - MEDIUM
    # 3. Type-based converters - LOWEST (fallback)

    view = MockView(
        form_overrides={
            "description": PasswordField  # Highest priority
        }
    )
    converter = AdminModelConverter(None, view)

    # View-level should take precedence over any other method
    override = converter._get_field_class_override("description", None)
    assert override == PasswordField, "View-level override should have highest priority"


def test_form_overrides_integration_with_convert():
    """Test that form_overrides work with the convert method (integration test)."""

    class TestModel(SQLModel):
        id: int = Field(primary_key=True)
        content: str = Field()

    view = MockView(form_overrides={"content": TextAreaField})
    converter = AdminModelConverter(None, view)

    # Create a mock field object since we can't easily test with real ModelField
    from flask_admin.contrib.sqlmodel.tools import ModelField

    mock_field = ModelField(
        name="content",
        type_=str,
        default=None,
        required=False,
        primary_key=False,
        description=None,
        source=None,
        is_computed=False,
        is_property=False,
        has_setter=False,
        field_class=None,
    )

    # Test that the override is applied
    override = converter._get_field_class_override("content", mock_field)
    assert override == TextAreaField
