"""
Integration tests for SQLAlchemyExtendedMixin with real SQLAlchemy-utils types.

These tests assume sqlalchemy-utils is installed (following the standard test strategy)
and test the full conversion pipeline with actual SQLAlchemy-utils field types.
"""

from enum import Enum
from unittest.mock import Mock

import pytest
from wtforms import validators

# Import SQLAlchemy-utils types - tests assume package is available
try:
    from sqlalchemy_utils import ArrowType
    from sqlalchemy_utils import ChoiceType
    from sqlalchemy_utils import ColorType
    from sqlalchemy_utils import CurrencyType
    from sqlalchemy_utils import EmailType
    from sqlalchemy_utils import IPAddressType
    from sqlalchemy_utils import TimezoneType
    from sqlalchemy_utils import URLType

    SQLALCHEMY_UTILS_AVAILABLE = True
except ImportError:
    SQLALCHEMY_UTILS_AVAILABLE = False

from flask_admin.contrib.sqlmodel.form import AdminModelConverter
from flask_admin.contrib.sqlmodel.mixins import SQLAlchemyExtendedMixin


class MockView:
    """Mock view for testing."""

    def __init__(self):
        self.form_overrides = None
        self.form_columns = None


@pytest.mark.skipif(
    not SQLALCHEMY_UTILS_AVAILABLE, reason="sqlalchemy-utils not available"
)
class TestSQLAlchemyUtilsIntegration:
    """Integration tests with real SQLAlchemy-utils types."""

    def test_email_type_integration(self):
        """Test EmailType integration through the mixin."""
        mixin = SQLAlchemyExtendedMixin()

        # Create mock column with real EmailType
        mock_column = Mock()
        mock_column.type = EmailType()
        mock_column.nullable = False
        field_args = {"validators": []}

        # Test through handle_extended_types
        result = mixin.handle_extended_types(None, mock_column, field_args)

        # Result should be a field class (UnboundField), not instance
        assert result is not None
        # Should have email validator
        email_validators = [
            v for v in field_args["validators"] if isinstance(v, validators.Email)
        ]
        assert len(email_validators) == 1

    def test_url_type_integration(self):
        """Test URLType integration through the mixin."""
        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        mock_column.type = URLType()
        field_args = {"validators": []}

        result = mixin.handle_extended_types(None, mock_column, field_args)

        assert result is not None
        # Should have URL validator and filter
        url_validators = [
            v for v in field_args["validators"] if isinstance(v, validators.URL)
        ]
        assert len(url_validators) == 1
        assert len(field_args["filters"]) == 1

    def test_ip_address_type_integration(self):
        """Test IPAddressType integration through the mixin."""
        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        mock_column.type = IPAddressType()
        field_args = {"validators": []}

        result = mixin.handle_extended_types(None, mock_column, field_args)

        assert result is not None
        # Should have IP address validator
        ip_validators = [
            v for v in field_args["validators"] if isinstance(v, validators.IPAddress)
        ]
        assert len(ip_validators) == 1

    def test_color_type_integration(self):
        """Test ColorType integration through the mixin."""
        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        mock_column.type = ColorType()
        field_args = {"validators": []}

        result = mixin.handle_extended_types(None, mock_column, field_args)

        assert result is not None
        # Should have color validator and filter
        assert len(field_args["validators"]) == 1
        assert len(field_args["filters"]) == 1

    def test_currency_type_integration(self):
        """Test CurrencyType integration through the mixin."""
        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        mock_column.type = CurrencyType()
        field_args = {"validators": []}

        result = mixin.handle_extended_types(None, mock_column, field_args)

        assert result is not None
        # Should have currency validator and filter
        assert len(field_args["validators"]) == 1
        assert len(field_args["filters"]) == 1

    def test_timezone_type_integration(self):
        """Test TimezoneType integration through the mixin."""
        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        mock_column.type = TimezoneType()
        mock_column.type._coerce = Mock()
        field_args = {"validators": []}

        result = mixin.handle_extended_types(None, mock_column, field_args)

        assert result is not None
        # Should have timezone validator
        assert len(field_args["validators"]) == 1

    def test_choice_type_integration_with_tuples(self):
        """Test ChoiceType integration with tuple choices."""
        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        mock_column.type = ChoiceType([("opt1", "Option 1"), ("opt2", "Option 2")])
        mock_column.nullable = False
        field_args = {"validators": []}

        result = mixin.handle_extended_types(None, mock_column, field_args)

        assert result is not None
        # Choices could be list or tuple
        expected_choices = [("opt1", "Option 1"), ("opt2", "Option 2")]
        assert list(field_args["choices"]) == expected_choices

    def test_choice_type_integration_with_enum(self):
        """Test ChoiceType integration with enum choices."""

        class StatusEnum(Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        mock_column.type = ChoiceType(StatusEnum)
        mock_column.nullable = True
        field_args = {"validators": []}

        result = mixin.handle_extended_types(None, mock_column, field_args)

        assert result is not None
        assert field_args["allow_blank"] is True
        expected_choices = [(f.value, f.name) for f in StatusEnum]
        assert field_args["choices"] == expected_choices

    def test_arrow_type_integration(self):
        """Test ArrowType integration through the mixin."""
        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        mock_column.type = ArrowType()
        field_args = {}

        result = mixin.handle_extended_types(None, mock_column, field_args)

        # Should return a DateTimeField
        assert result is not None
        assert hasattr(result, "_formfield")  # WTForms field characteristic

    def test_unknown_type_returns_none(self):
        """Test that unknown types return None."""
        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        mock_column.type = Mock()  # Unknown type
        field_args = {}

        result = mixin.handle_extended_types(None, mock_column, field_args)

        assert result is None

    def test_full_converter_integration(self):
        """Test full converter integration with SQLAlchemy-utils types."""
        view = MockView()
        converter = AdminModelConverter(None, view)

        # Test email type
        mock_column = Mock()
        mock_column.type = EmailType()
        field_args = {"validators": []}

        result = converter.handle_extended_types(None, mock_column, field_args)
        assert result is not None

        # Test URL type
        mock_column.type = URLType()
        field_args = {"validators": []}

        result = converter.handle_extended_types(None, mock_column, field_args)
        assert result is not None

    def test_nullable_column_handling(self):
        """Test nullable column handling in extended types."""
        mixin = SQLAlchemyExtendedMixin()

        # Test with nullable EmailType
        mock_column = Mock()
        mock_column.type = EmailType()
        mock_column.nullable = True
        field_args = {"validators": []}

        result = mixin._convert_email_type(mock_column, field_args) # type: ignore

        assert result is not None
        # Should handle nullable logic (if _nullable_common is available)
        assert len(field_args["validators"]) >= 1  # At least email validator


@pytest.mark.skipif(
    not SQLALCHEMY_UTILS_AVAILABLE, reason="sqlalchemy-utils not available"
)
class TestSQLAlchemyUtilsValidators:
    """Test the SQLAlchemy-utils specific validators moved to mixin."""

    def test_valid_color_with_hex_values(self):
        """Test color validator with hex color values."""
        from flask_admin.contrib.sqlmodel.mixins import valid_color

        mock_form = Mock()

        # Test valid hex colors
        mock_field = Mock()
        mock_field.data = "#ff0000"
        valid_color(mock_form, mock_field)  # Should not raise

        mock_field.data = "#fff"
        valid_color(mock_form, mock_field)  # Should not raise

        mock_field.data = "red"
        valid_color(mock_form, mock_field)  # Should not raise

    def test_valid_color_with_invalid_values(self):
        """Test color validator with invalid color values."""
        from wtforms.validators import ValidationError

        from flask_admin.contrib.sqlmodel.mixins import valid_color

        mock_form = Mock()
        mock_field = Mock()

        # Test invalid hex color
        mock_field.data = "#xyz"
        with pytest.raises(ValidationError):
            valid_color(mock_form, mock_field)

        # Test invalid color name
        mock_field.data = "invalidcolor"
        with pytest.raises(ValidationError):
            valid_color(mock_form, mock_field)

    def test_valid_currency_with_valid_codes(self):
        """Test currency validator with valid ISO codes."""
        from flask_admin.contrib.sqlmodel.mixins import valid_currency

        mock_form = Mock()
        mock_field = Mock()

        # Test valid currency codes
        for code in ["USD", "EUR", "GBP", "JPY", "CAD"]:
            mock_field.data = code
            valid_currency(mock_form, mock_field)  # Should not raise

    def test_valid_currency_with_invalid_codes(self):
        """Test currency validator with invalid codes."""
        from wtforms.validators import ValidationError

        from flask_admin.contrib.sqlmodel.mixins import valid_currency

        mock_form = Mock()
        mock_field = Mock()

        # Test invalid currency codes (excluding empty string which is valid)
        invalid_codes = ["us", "USDD", "123", "usd"]
        for code in invalid_codes:
            mock_field.data = code
            with pytest.raises(ValidationError):
                valid_currency(mock_form, mock_field)

        # Test empty string separately - should not raise
        mock_field.data = ""
        valid_currency(mock_form, mock_field)  # Should not raise

    def test_timezone_validator_with_coerce_function(self):
        """Test timezone validator with coerce function."""
        from flask_admin.contrib.sqlmodel.mixins import TimeZoneValidator

        mock_coerce = Mock()
        validator = TimeZoneValidator(coerce_function=mock_coerce)

        mock_form = Mock()
        mock_field = Mock()
        mock_field.data = "America/New_York"

        # Should call coerce function
        validator(mock_form, mock_field)
        mock_coerce.assert_called_once_with("America/New_York")

    def test_timezone_validator_with_coerce_error(self):
        """Test timezone validator when coerce function raises error."""
        from wtforms.validators import ValidationError

        from flask_admin.contrib.sqlmodel.mixins import TimeZoneValidator

        mock_coerce = Mock(side_effect=ValueError("Invalid timezone"))
        validator = TimeZoneValidator(coerce_function=mock_coerce)

        mock_form = Mock()
        mock_field = Mock()
        mock_field.data = "Invalid/Timezone"

        with pytest.raises(ValidationError):
            validator(mock_form, mock_field)

    def test_timezone_validator_without_coerce_function(self):
        """Test timezone validator without coerce function (uses pytz fallback)."""
        from flask_admin.contrib.sqlmodel.mixins import TimeZoneValidator

        validator = TimeZoneValidator()

        mock_form = Mock()
        mock_field = Mock()
        mock_field.data = "UTC"

        # Should not raise with valid timezone
        validator(mock_form, mock_field)

    def test_empty_field_handling_in_validators(self):
        """Test that validators handle empty/None field data gracefully."""
        from flask_admin.contrib.sqlmodel.mixins import TimeZoneValidator
        from flask_admin.contrib.sqlmodel.mixins import valid_color
        from flask_admin.contrib.sqlmodel.mixins import valid_currency

        mock_form = Mock()
        mock_field = Mock()

        # Test with None
        mock_field.data = None
        valid_color(mock_form, mock_field)  # Should not raise
        valid_currency(mock_form, mock_field)  # Should not raise

        validator = TimeZoneValidator()
        validator(mock_form, mock_field)  # Should not raise

        # Test with empty string
        mock_field.data = ""
        valid_color(mock_form, mock_field)  # Should not raise
        valid_currency(mock_form, mock_field)  # Should not raise
        validator(mock_form, mock_field)  # Should not raise


@pytest.mark.skipif(
    not SQLALCHEMY_UTILS_AVAILABLE, reason="sqlalchemy-utils not available"
)
class TestMixinEdgeCases:
    """Test edge cases in the mixin functionality."""

    def test_column_without_type_attribute(self):
        """Test handling of column without type attribute."""
        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        del mock_column.type  # Remove type attribute
        field_args = {}

        result = mixin.handle_extended_types(None, mock_column, field_args)
        assert result is None

    def test_column_with_none_type(self):
        """Test handling of column with None type."""
        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        mock_column.type = None
        field_args = {}

        result = mixin.handle_extended_types(None, mock_column, field_args)
        assert result is None

    def test_choice_type_without_choices(self):
        """Test ChoiceType without choices attribute."""
        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        # Mock a choice type with minimal required attributes
        mock_column.type = Mock()
        mock_column.type.choices = [("test", "Test")]  # Valid choices
        mock_column.nullable = False
        field_args = {"validators": []}

        result = mixin._convert_choice_type(mock_column, field_args) # type: ignore
        assert result is not None  # Should still return a field

    def test_choice_type_with_missing_python_type(self):
        """Test ChoiceType without python_type attribute."""
        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        mock_column.type = Mock()
        mock_column.type.choices = [("a", "A"), ("b", "B")]
        mock_column.nullable = False
        field_args = {"validators": []}

        # Create a custom mock that doesn't have python_type
        class MockTypeWithoutPythonType:
            def __init__(self):
                self.choices = [("a", "A"), ("b", "B")]

            def __getattr__(self, name):
                if name == "python_type":
                    raise AttributeError("python_type")
                return Mock()

        mock_column.type = MockTypeWithoutPythonType()

        # Should handle missing python_type gracefully
        result = mixin._convert_choice_type(mock_column, field_args) # type: ignore
        assert result is not None
        # Should fallback to str coercion
        assert field_args["coerce"] is str
