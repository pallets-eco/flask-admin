"""
Test graceful degradation of SQLAlchemyExtendedMixin
when sqlalchemy-utils is not available.

This test ensures that the mixin fails gracefully when the optional sqlalchemy-utils
package is not installed, allowing regular SQLAlchemy field conversion to continue.
"""

import sys
from unittest.mock import Mock
from unittest.mock import patch

from sqlmodel import Field
from sqlmodel import SQLModel
from wtforms import fields

from flask_admin.contrib.sqlmodel.form import AdminModelConverter


class MockView:
    """Mock view for testing purposes."""

    def __init__(self):
        self.form_overrides = None
        self.form_columns = None


def test_mixin_graceful_degradation_import_error():
    """Test that mixin returns None when sqlalchemy-utils import fails."""

    class TestModel(SQLModel):
        id: int = Field(primary_key=True)
        name: str = Field()

    # Mock the import to fail
    with patch.dict("sys.modules", {"sqlalchemy_utils": None}):
        # Remove sqlalchemy_utils from sys.modules to simulate ImportError
        if "sqlalchemy_utils" in sys.modules:
            del sys.modules["sqlalchemy_utils"]

        # Force re-import of the mixin module
        if "flask_admin.contrib.sqlmodel.mixins" in sys.modules:
            del sys.modules["flask_admin.contrib.sqlmodel.mixins"]

        # This should trigger the ImportError fallback
        from flask_admin.contrib.sqlmodel.mixins import SQLAlchemyExtendedMixin

        # Test that mixin gracefully returns None
        mixin = SQLAlchemyExtendedMixin()

        # Create mock column that would normally be handled by sqlalchemy-utils
        mock_column = Mock()
        mock_column.type = Mock()
        field_args = {"validators": []}

        # Should return None when sqlalchemy-utils is not available
        result = mixin.handle_extended_types(TestModel, mock_column, field_args)
        assert result is None, (
            "Mixin should return None when sqlalchemy-utils is not available"
        )


def test_converter_continues_working_without_sqlalchemy_utils():
    """Test that AdminModelConverter continues to
    work when sqlalchemy-utils is missing."""

    class TestModel(SQLModel):
        id: int = Field(primary_key=True)
        name: str = Field()
        description: str = Field()

    # Mock sqlalchemy-utils import failure
    with patch("flask_admin.contrib.sqlmodel.mixins.SQLALCHEMY_UTILS_AVAILABLE", False):
        view = MockView()
        converter = AdminModelConverter(None, view)

        # Should be able to create converter without errors
        assert converter is not None
        assert hasattr(converter, "handle_extended_types")

        # Mock column for testing
        mock_column = Mock()
        mock_column.type = Mock()
        field_args = {"validators": []}

        # Extended types handler should return None gracefully
        result = converter.handle_extended_types(TestModel, mock_column, field_args)
        assert result is None


def test_form_creation_works_without_sqlalchemy_utils(app):
    """Test that form creation works normally when sqlalchemy-utils is not available."""

    class TestModel(SQLModel, table=True):
        __tablename__ = "test_graceful_degradation" # type: ignore

        id: int = Field(primary_key=True)
        name: str = Field()
        email: str = Field()  # This would be EmailType with sqlalchemy-utils
        description: str = Field()

    # Mock sqlalchemy-utils unavailability
    with patch("flask_admin.contrib.sqlmodel.mixins.SQLALCHEMY_UTILS_AVAILABLE", False):
        from sqlmodel import Session

        from flask_admin.contrib.sqlmodel.view import SQLModelView

        with app.app_context():
            session = Session()
            view = SQLModelView(TestModel, session)

            # Should be able to create form without errors
            form = view.create_form()
            assert form is not None

            # Basic fields should be present
            assert "name" in form._fields
            assert "email" in form._fields
            assert "description" in form._fields

            # Fields should be regular StringFields (not extended types)
            assert isinstance(form.name, fields.StringField) # type: ignore
            assert isinstance(form.email, fields.StringField) # type: ignore
            assert isinstance(form.description, fields.StringField) # type: ignore


def test_no_exception_on_mixin_initialization():
    """Test that mixin can be initialized without sqlalchemy-utils."""

    # Mock the import to fail during initialization
    with patch("flask_admin.contrib.sqlmodel.mixins.SQLALCHEMY_UTILS_AVAILABLE", False):
        # Should not raise any exceptions
        from flask_admin.contrib.sqlmodel.mixins import SQLAlchemyExtendedMixin

        mixin = SQLAlchemyExtendedMixin()
        assert mixin is not None
        assert hasattr(mixin, "handle_extended_types")

        # Method should return None without crashing
        result = mixin.handle_extended_types(None, None, {})
        assert result is None


def test_mixin_validates_availability_flag():
    """Test that SQLALCHEMY_UTILS_AVAILABLE flag works correctly."""

    # Test when available (normal case)
    with patch("flask_admin.contrib.sqlmodel.mixins.SQLALCHEMY_UTILS_AVAILABLE", True):
        from flask_admin.contrib.sqlmodel.mixins import SQLAlchemyExtendedMixin

        mixin = SQLAlchemyExtendedMixin()

        # Mock a column that doesn't match any extended types
        mock_column = Mock()
        mock_column.type = Mock()

        # Should process the request and return None for unknown type
        result = mixin.handle_extended_types(None, mock_column, {"validators": []})
        assert result is None  # None because mock doesn't match any real types

    # Test when not available
    with patch("flask_admin.contrib.sqlmodel.mixins.SQLALCHEMY_UTILS_AVAILABLE", False):
        from flask_admin.contrib.sqlmodel.mixins import SQLAlchemyExtendedMixin

        mixin = SQLAlchemyExtendedMixin()

        # Should immediately return None
        result = mixin.handle_extended_types(None, None, {"validators": []})
        assert result is None
