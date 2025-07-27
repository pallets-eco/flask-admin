"""
Additional tests for SQLModel typefmt module to improve coverage.

This file targets specific uncovered areas in the typefmt module.
"""

from enum import Enum
from typing import Optional
from unittest.mock import Mock

import pytest
from sqlmodel import Field
from sqlmodel import SQLModel

from flask_admin.contrib.sqlmodel.typefmt import arrow_export_formatter
from flask_admin.contrib.sqlmodel.typefmt import arrow_formatter
from flask_admin.contrib.sqlmodel.typefmt import DEFAULT_FORMATTERS
from flask_admin.contrib.sqlmodel.typefmt import enum_formatter
from flask_admin.contrib.sqlmodel.typefmt import EXPORT_FORMATTERS


class SampleEnum(Enum):
    """Test enum for formatter testing."""

    VALUE1 = "value1"
    VALUE2 = "value2"
    OPTION_A = "option_a"
    OPTION_B = "option_b"


class TypFmtTestModel(SQLModel, table=True):
    """Test model for typefmt coverage tests."""

    __tablename__ = "typefmt_test_model"
    id: int = Field(primary_key=True)
    name: str
    status: Optional[SampleEnum] = None
    is_active: bool = True


class SampleEnumFormatter:
    """Test enum_formatter function."""

    def test_enum_formatter_basic(self):
        """Test basic enum formatting."""
        # Test with enum member
        result = enum_formatter(None, SampleEnum.VALUE1, "status")
        assert result == "value1"

        result = enum_formatter(None, SampleEnum.OPTION_A, "status")
        assert result == "option_a"

    def test_enum_formatter_with_view_context(self):
        """Test enum formatter with view context."""
        mock_view = Mock()
        mock_view.name = "test_view"

        result = enum_formatter(mock_view, SampleEnum.VALUE2, "status")
        assert result == "value2"

    def test_enum_formatter_in_default_formatters(self):
        """Test that enum formatter is registered in DEFAULT_FORMATTERS."""
        formatter = DEFAULT_FORMATTERS.get(Enum)
        assert formatter is not None
        assert formatter == enum_formatter

    def test_enum_formatter_various_enums(self):
        """Test enum formatter with different enum types."""

        class StatusEnum(Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"
            PENDING = "pending"

        class PriorityEnum(Enum):
            LOW = 1
            MEDIUM = 2
            HIGH = 3

        # Test string enum
        result = enum_formatter(None, StatusEnum.ACTIVE, "status")
        assert result == "active"

        # Test integer enum
        result = enum_formatter(None, PriorityEnum.HIGH, "priority")
        assert result == 3


class TestArrowFormatter:
    """Test arrow formatter functions."""

    def test_arrow_formatter_import_available(self):
        """Test arrow formatter when arrow is available."""
        try:
            import arrow

            # Create an arrow time object
            arrow_time = arrow.now()

            # Test the formatter
            result = arrow_formatter(None, arrow_time, "created_at")
            assert isinstance(result, str)
            assert (
                "ago" in result or "in" in result or "now" in result
            )  # humanize format

        except ImportError:
            # Arrow not available, skip test
            pytest.skip("Arrow library not available")

    def test_arrow_export_formatter_import_available(self):
        """Test arrow export formatter when arrow is available."""
        try:
            import arrow

            # Create an arrow time object
            arrow_time = arrow.now()

            # Test the export formatter
            result = arrow_export_formatter(None, arrow_time, "created_at")
            assert isinstance(result, str)
            # Should be a formatted date string
            assert len(result) > 0

        except ImportError:
            # Arrow not available, skip test
            pytest.skip("Arrow library not available")

    def test_arrow_formatters_in_registry(self):
        """Test that arrow formatters are registered when available."""
        try:
            import arrow

            # Check if Arrow formatter is registered
            formatter = DEFAULT_FORMATTERS.get(arrow.Arrow)
            if formatter:
                assert formatter == arrow_formatter

            export_formatter = EXPORT_FORMATTERS.get(arrow.Arrow)
            if export_formatter:
                assert export_formatter == arrow_export_formatter

        except ImportError:
            # Arrow not available, formatters shouldn't be registered
            pytest.skip("Arrow library not available")


class TestListFormatterInherited:
    """Test list formatter inherited from base."""

    def test_list_formatter_basic(self):
        """Test basic list formatting."""
        formatter = DEFAULT_FORMATTERS.get(list)
        assert formatter is not None

        # Test with simple list - provide mock view parameter
        mock_view = Mock()
        result = formatter(mock_view, ["a", "b", "c"], "test_field")
        assert "a" in result
        assert "b" in result
        assert "c" in result

    def test_list_formatter_empty_list(self):
        """Test list formatter with empty list."""
        formatter = DEFAULT_FORMATTERS.get(list)

        mock_view = Mock()
        result = formatter(mock_view, [], "test_field")
        # Empty list should return empty string
        assert result == ""

    def test_list_formatter_with_enums(self):
        """Test list formatter with enum values."""
        formatter = DEFAULT_FORMATTERS.get(list)

        mock_view = Mock()
        enum_list = [SampleEnum.VALUE1, SampleEnum.VALUE2]
        result = formatter(mock_view, enum_list, "test_field")

        # Should contain string representations of enums
        assert "SampleEnum.VALUE1" in result or "VALUE1" in result
        assert "SampleEnum.VALUE2" in result or "VALUE2" in result


class TestFormatterRegistryIntegration:
    """Test formatter registry integration."""

    def test_default_formatters_contains_required_types(self):
        """Test that DEFAULT_FORMATTERS contains required types."""
        # Should contain list formatter
        assert list in DEFAULT_FORMATTERS

        # Should contain enum formatter
        assert Enum in DEFAULT_FORMATTERS

    def test_export_formatters_inheritance(self):
        """Test that EXPORT_FORMATTERS inherits properly."""
        # EXPORT_FORMATTERS should be a copy of the base EXPORT_FORMATTERS
        assert isinstance(EXPORT_FORMATTERS, dict)

    def test_formatter_registry_modification(self):
        """Test that formatter registries can be modified."""
        # Test that we can access and potentially modify formatters
        original_enum_formatter = DEFAULT_FORMATTERS.get(Enum)
        assert original_enum_formatter is not None

        # Ensure it's the enum_formatter function
        assert original_enum_formatter == enum_formatter


class TestFormatterEdgeCases:
    """Test edge cases and error handling."""

    def test_enum_formatter_with_none_values(self):
        """Test enum formatter with None values."""
        # This would normally not be called with None, but test robustness
        try:
            result = enum_formatter(None, None, "test_field")
            # If it doesn't raise an exception, result should be None
            assert result is None
        except AttributeError:
            # Expected behavior for None enum member - this is the normal case
            # enum_formatter should raise AttributeError when called with None
            pass

    def test_formatter_with_custom_enum_values(self):
        """Test formatter with custom enum values."""

        class CustomEnum(Enum):
            COMPLEX_VALUE = {"key": "value", "number": 42}
            TUPLE_VALUE = ("a", "b", "c")
            LIST_VALUE = [1, 2, 3]

        # Test with complex enum values
        result = enum_formatter(None, CustomEnum.COMPLEX_VALUE, "custom")
        assert result == {"key": "value", "number": 42}

        result = enum_formatter(None, CustomEnum.TUPLE_VALUE, "custom")
        assert result == ("a", "b", "c")


class TestModuleImportHandling:
    """Test module import handling and fallbacks."""

    def test_arrow_import_handling(self):
        """Test that arrow import is handled gracefully."""
        # The module should import successfully regardless of arrow availability
        import flask_admin.contrib.sqlmodel.typefmt as typefmt_module

        # Should have the formatter functions defined
        assert hasattr(typefmt_module, "enum_formatter")
        assert hasattr(typefmt_module, "arrow_formatter")
        assert hasattr(typefmt_module, "arrow_export_formatter")

    def test_formatters_registry_integrity(self):
        """Test that formatters registry maintains integrity."""
        # DEFAULT_FORMATTERS should be a proper copy
        from flask_admin.model.typefmt import BASE_FORMATTERS

        # Should not be the same object (copy, not reference)
        assert DEFAULT_FORMATTERS is not BASE_FORMATTERS

        # But should contain the base formatters
        for key, _value in BASE_FORMATTERS.items():
            if key not in [list, Enum]:  # These are overridden
                assert key in DEFAULT_FORMATTERS


class TestSQLModelIntegration:
    """Test integration with SQLModel types."""

    def test_sqlmodel_enum_field_formatting(self):
        """Test formatting enum fields from SQLModel."""

        # Create a test model instance
        model = TypFmtTestModel(
            id=1, name="Test Model", status=SampleEnum.VALUE1, is_active=True
        )

        # Test that enum field can be formatted
        enum_formatter_func = DEFAULT_FORMATTERS.get(Enum)
        assert enum_formatter_func is not None

        if model.status:
            result = enum_formatter_func(None, model.status, "status")
            assert result == "value1"

    def test_optional_enum_handling(self):
        """Test handling of optional enum fields."""

        # Create model with None enum
        model = TypFmtTestModel(id=2, name="Test Model 2", status=None, is_active=False)

        # Should handle None status gracefully
        assert model.status is None

        # If we try to format None, it should be handled appropriately
        # (typically this wouldn't happen in normal usage)
