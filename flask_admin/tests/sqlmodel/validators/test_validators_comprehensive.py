"""
Comprehensive tests for SQLModel validators module to improve coverage.

This file tests all validator classes and functions including edge cases,
error handling, and various validation scenarios.
"""

from unittest.mock import Mock
from unittest.mock import patch

import pytest
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import SQLModel
from wtforms import Form
from wtforms import StringField
from wtforms import ValidationError

from flask_admin.contrib.sqlmodel.validators import ItemsRequired
from flask_admin.contrib.sqlmodel.validators import TimeZoneValidator
from flask_admin.contrib.sqlmodel.validators import Unique
from flask_admin.contrib.sqlmodel.validators import valid_color
from flask_admin.contrib.sqlmodel.validators import valid_currency


# Test models for validator testing
class ValidatorTestModel(SQLModel, table=True):
    """Test model for validator testing."""

    id: int = Field(primary_key=True)
    email: str = Field(unique=True)
    name: str
    currency_code: str
    color_field: str


class TestUniqueValidator:
    """Test the Unique validator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.mock_model = ValidatorTestModel
        self.mock_column = ValidatorTestModel.email

        # Mock form and field
        self.mock_form = Mock()
        self.mock_field = Mock()

    def test_init_default_message(self):
        """Test Unique validator initialization with default message."""
        validator = Unique(self.mock_session, self.mock_model, self.mock_column)

        assert validator.db_session == self.mock_session
        assert validator.model == self.mock_model
        assert validator.column == self.mock_column
        assert str(validator.message) == "Already exists."
        assert hasattr(validator, "field_flags")
        assert validator.field_flags == {"unique": True}

    def test_init_custom_message(self):
        """Test Unique validator initialization with custom message."""
        custom_message = "This email is already taken!"
        validator = Unique(
            self.mock_session, self.mock_model, self.mock_column, message=custom_message
        )

        assert validator.message == custom_message

    def test_call_with_none_data(self):
        """Test validator with None data (should pass)."""
        validator = Unique(self.mock_session, self.mock_model, self.mock_column)

        self.mock_field.data = None

        # Should not raise any exception
        validator(self.mock_form, self.mock_field)

    def test_call_with_unique_value(self):
        """Test validator with unique value (should pass)."""
        validator = Unique(self.mock_session, self.mock_model, self.mock_column)

        self.mock_field.data = "unique@example.com"

        # Mock session.exec to raise exception (no result found)
        mock_exec_result = Mock()
        mock_exec_result.one.side_effect = Exception("No result found")
        self.mock_session.exec.return_value = mock_exec_result

        # Should not raise ValidationError
        validator(self.mock_form, self.mock_field)

    def test_call_with_duplicate_value_no_form_obj(self):
        """Test validator with duplicate value and no form._obj."""
        validator = Unique(self.mock_session, self.mock_model, self.mock_column)

        self.mock_field.data = "duplicate@example.com"

        # Mock session.exec to return an existing object
        mock_obj = Mock()
        mock_exec_result = Mock()
        mock_exec_result.one.return_value = mock_obj
        self.mock_session.exec.return_value = mock_exec_result

        # Form has no _obj attribute
        del self.mock_form._obj

        with pytest.raises(ValidationError, match="Already exists"):
            validator(self.mock_form, self.mock_field)

    def test_call_with_duplicate_value_different_form_obj(self):
        """Test validator with duplicate value and different form._obj."""
        validator = Unique(self.mock_session, self.mock_model, self.mock_column)

        self.mock_field.data = "duplicate@example.com"

        # Mock session.exec to return an existing object
        mock_existing_obj = Mock()
        mock_exec_result = Mock()
        mock_exec_result.one.return_value = mock_existing_obj
        self.mock_session.exec.return_value = mock_exec_result

        # Form has different _obj
        mock_different_obj = Mock()
        self.mock_form._obj = mock_different_obj

        with pytest.raises(ValidationError, match="Already exists"):
            validator(self.mock_form, self.mock_field)

    def test_call_with_duplicate_value_same_form_obj(self):
        """Test validator with duplicate value but same form._obj (editing)."""
        validator = Unique(self.mock_session, self.mock_model, self.mock_column)

        self.mock_field.data = "existing@example.com"

        # Mock session.exec to return the same object as form._obj
        mock_existing_obj = Mock()
        mock_exec_result = Mock()
        mock_exec_result.one.return_value = mock_existing_obj
        self.mock_session.exec.return_value = mock_exec_result

        # Form has the same _obj (editing existing record)
        self.mock_form._obj = mock_existing_obj

        # Should not raise ValidationError (editing the same record)
        validator(self.mock_form, self.mock_field)

    def test_call_with_validation_error_reraise(self):
        """Test that ValidationError is re-raised."""
        validator = Unique(self.mock_session, self.mock_model, self.mock_column)

        self.mock_field.data = "test@example.com"

        # Mock to raise ValidationError inside try block
        def mock_exec_side_effect(*args, **kwargs):
            mock_result = Mock()
            mock_result.one.side_effect = lambda: exec(
                'raise ValidationError("Custom error")'
            )
            return mock_result

        self.mock_session.exec.side_effect = mock_exec_side_effect

        with pytest.raises(ValidationError):
            validator(self.mock_form, self.mock_field)

    def test_call_with_database_error(self):
        """Test validator handling database errors gracefully."""
        validator = Unique(self.mock_session, self.mock_model, self.mock_column)

        self.mock_field.data = "test@example.com"

        # Mock session.exec to raise a database error
        self.mock_session.exec.side_effect = Exception("Database connection error")

        # Should not raise any exception (database errors are ignored)
        validator(self.mock_form, self.mock_field)


class TestItemsRequiredValidator:
    """Test the ItemsRequired validator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_form = Mock()
        self.mock_field = Mock()

    def test_init_default_values(self):
        """Test ItemsRequired initialization with default values."""
        validator = ItemsRequired()

        assert validator.min == 1
        assert validator.message is None

    def test_init_custom_values(self):
        """Test ItemsRequired initialization with custom values."""
        custom_message = "You must select at least 3 items"
        validator = ItemsRequired(min=3, message=custom_message)

        assert validator.min == 3
        assert validator.message == custom_message

    def test_call_sufficient_items(self):
        """Test validator with sufficient items."""
        validator = ItemsRequired(min=2)

        # Mock field entries
        mock_entry1 = Mock()
        mock_entry2 = Mock()
        mock_entry3 = Mock()
        self.mock_field.entries = [mock_entry1, mock_entry2, mock_entry3]

        # Mock should_delete to return False for all (none should be deleted)
        self.mock_field.should_delete = Mock(return_value=False)

        # Should not raise any exception
        validator(self.mock_form, self.mock_field)

    def test_call_insufficient_items(self):
        """Test validator with insufficient items."""
        validator = ItemsRequired(min=3)

        # Mock field entries
        mock_entry1 = Mock()
        mock_entry2 = Mock()
        self.mock_field.entries = [mock_entry1, mock_entry2]

        # Mock should_delete to return False for all
        self.mock_field.should_delete = Mock(return_value=False)

        # Mock ngettext for pluralization
        self.mock_field.ngettext = Mock(return_value="At least 3 items are required")

        with pytest.raises(ValidationError, match="At least 3 items are required"):
            validator(self.mock_form, self.mock_field)

    def test_call_with_deleted_items(self):
        """Test validator with some items marked for deletion."""
        validator = ItemsRequired(min=2)

        # Mock field entries
        mock_entry1 = Mock()
        mock_entry2 = Mock()
        mock_entry3 = Mock()
        self.mock_field.entries = [mock_entry1, mock_entry2, mock_entry3]

        # Mock should_delete: first two are kept, last one is deleted
        def should_delete_side_effect(entry):
            return entry == mock_entry3

        self.mock_field.should_delete = Mock(side_effect=should_delete_side_effect)

        # Should not raise exception (2 items remaining >= min of 2)
        validator(self.mock_form, self.mock_field)

    def test_call_with_deleted_items_insufficient(self):
        """Test validator with too many items marked for deletion."""
        validator = ItemsRequired(min=2)

        # Mock field entries
        mock_entry1 = Mock()
        mock_entry2 = Mock()
        self.mock_field.entries = [mock_entry1, mock_entry2]

        # Mock should_delete: first is deleted, only one remains
        def should_delete_side_effect(entry):
            return entry == mock_entry1

        self.mock_field.should_delete = Mock(side_effect=should_delete_side_effect)
        self.mock_field.ngettext = Mock(return_value="At least 2 items are required")

        with pytest.raises(ValidationError, match="At least 2 items are required"):
            validator(self.mock_form, self.mock_field)

    def test_call_with_custom_message(self):
        """Test validator with custom error message."""
        custom_message = "Please select more items!"
        validator = ItemsRequired(min=5, message=custom_message)

        # Mock insufficient entries
        self.mock_field.entries = [Mock()]
        self.mock_field.should_delete = Mock(return_value=False)

        with pytest.raises(ValidationError, match="Please select more items!"):
            validator(self.mock_form, self.mock_field)

    def test_call_singular_vs_plural_message(self):
        """Test validator uses correct singular/plural messages."""
        # Test singular (min=1)
        validator_singular = ItemsRequired(min=1)
        self.mock_field.entries = []
        self.mock_field.should_delete = Mock(return_value=False)
        self.mock_field.ngettext = Mock(return_value="At least 1 item is required")

        with pytest.raises(ValidationError):
            validator_singular(self.mock_form, self.mock_field)

        # Verify ngettext was called with correct parameters
        self.mock_field.ngettext.assert_called_with(
            "At least %(num)d item is required",
            "At least %(num)d items are required",
            1,
        )

    def test_inheritance_from_input_required(self):
        """Test that ItemsRequired inherits from InputRequired."""
        from wtforms.validators import InputRequired

        validator = ItemsRequired()
        assert isinstance(validator, InputRequired)


class TestValidCurrencyFunction:
    """Test the valid_currency function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_form = Mock()
        self.mock_field = Mock()

    def test_valid_currency_empty_data(self):
        """Test valid_currency with empty data."""
        self.mock_field.data = ""

        # Should not raise any exception
        valid_currency(self.mock_form, self.mock_field)

        # Test with None
        self.mock_field.data = None
        valid_currency(self.mock_form, self.mock_field)

    def test_valid_currency_valid_codes(self):
        """Test valid_currency with valid 3-letter codes."""
        valid_codes = ["USD", "EUR", "GBP", "JPY", "CNY", "CAD", "AUD"]

        for code in valid_codes:
            self.mock_field.data = code
            # Should not raise any exception
            valid_currency(self.mock_form, self.mock_field)

    def test_valid_currency_lowercase_valid(self):
        """Test valid_currency with valid lowercase codes."""
        self.mock_field.data = "usd"

        # Should not raise any exception (isalpha() accepts lowercase)
        valid_currency(self.mock_form, self.mock_field)

    def test_valid_currency_invalid_length(self):
        """Test valid_currency with invalid length codes."""
        self.mock_field.gettext = Mock(return_value="Not a valid ISO currency code")

        # Too short
        self.mock_field.data = "US"
        with pytest.raises(ValidationError, match="Not a valid ISO currency code"):
            valid_currency(self.mock_form, self.mock_field)

        # Too long
        self.mock_field.data = "USDX"
        with pytest.raises(ValidationError, match="Not a valid ISO currency code"):
            valid_currency(self.mock_form, self.mock_field)

    def test_valid_currency_invalid_characters(self):
        """Test valid_currency with non-alphabetic characters."""
        self.mock_field.gettext = Mock(return_value="Not a valid ISO currency code")

        invalid_codes = ["U1D", "US$", "12D", "U-D", "U D"]

        for code in invalid_codes:
            self.mock_field.data = code
            with pytest.raises(ValidationError, match="Not a valid ISO currency code"):
                valid_currency(self.mock_form, self.mock_field)

    def test_valid_currency_non_string_type(self):
        """Test valid_currency with non-string data types."""
        self.mock_field.gettext = Mock(return_value="Not a valid ISO currency code")

        # Integer
        self.mock_field.data = 123
        with pytest.raises(ValidationError, match="Not a valid ISO currency code"):
            valid_currency(self.mock_form, self.mock_field)

        # List
        self.mock_field.data = ["USD"]
        with pytest.raises(ValidationError, match="Not a valid ISO currency code"):
            valid_currency(self.mock_form, self.mock_field)


class TestValidColorFunction:
    """Test the valid_color function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_form = Mock()
        self.mock_field = Mock()

    def test_valid_color_empty_data(self):
        """Test valid_color with empty data."""
        self.mock_field.data = ""

        # Should not raise any exception
        valid_color(self.mock_form, self.mock_field)

        # Test with None
        self.mock_field.data = None
        valid_color(self.mock_form, self.mock_field)

    def test_valid_color_with_colour_library(self):
        """Test valid_color with colour library available."""
        # Mock the colour library to be available
        mock_color_class = Mock()
        mock_colour_module = Mock()
        mock_colour_module.Color = mock_color_class

        with patch.dict("sys.modules", {"colour": mock_colour_module}):
            self.mock_field.data = "red"

            # Should not raise exception if Color() doesn't raise
            valid_color(self.mock_form, self.mock_field)

            # Verify Color was called with the field data
            mock_color_class.assert_called_with("red")

    def test_valid_color_with_colour_library_invalid(self):
        """Test valid_color with colour library raising ValueError."""
        mock_color_class = Mock()
        mock_color_class.side_effect = ValueError("Invalid color")
        mock_colour_module = Mock()
        mock_colour_module.Color = mock_color_class

        with patch.dict("sys.modules", {"colour": mock_colour_module}):
            self.mock_field.data = "invalid_color"
            self.mock_field.gettext = Mock(return_value="Not a valid color")

            with pytest.raises(ValidationError, match="Not a valid color"):
                valid_color(self.mock_form, self.mock_field)

    def test_valid_color_fallback_hex_valid(self):
        """Test valid_color fallback with valid hex colors."""
        # Remove colour from sys.modules to trigger ImportError
        with patch.dict("sys.modules", {"colour": None}):
            valid_hex_colors = ["#ff0000", "#f00", "#123ABC", "#abc"]

            for color in valid_hex_colors:
                self.mock_field.data = color
                # Should not raise any exception
                valid_color(self.mock_form, self.mock_field)

    def test_valid_color_fallback_hex_invalid(self):
        """Test valid_color fallback with invalid hex colors."""
        # Remove colour from sys.modules to trigger ImportError
        with patch.dict("sys.modules", {"colour": None}):
            self.mock_field.gettext = Mock(return_value="Not a valid color")

            invalid_hex_colors = ["red", "#gg0000", "#12345", "ff0000", "#1234567"]

            for color in invalid_hex_colors:
                self.mock_field.data = color
                with pytest.raises(ValidationError, match="Not a valid color"):
                    valid_color(self.mock_form, self.mock_field)

    def test_valid_color_fallback_non_string(self):
        """Test valid_color fallback with non-string data."""
        # Remove colour from sys.modules to trigger ImportError
        with patch.dict("sys.modules", {"colour": None}):
            self.mock_field.gettext = Mock(return_value="Not a valid color")

            # Integer data
            self.mock_field.data = 123
            with pytest.raises(ValidationError, match="Not a valid color"):
                valid_color(self.mock_form, self.mock_field)


class TestTimeZoneValidator:
    """Test the TimeZoneValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_form = Mock()
        self.mock_field = Mock()
        self.mock_coerce_function = Mock()

    def test_init(self):
        """Test TimeZoneValidator initialization."""
        validator = TimeZoneValidator(self.mock_coerce_function)

        assert validator.coerce_function == self.mock_coerce_function

    def test_call_valid_timezone(self):
        """Test validator with valid timezone."""
        validator = TimeZoneValidator(self.mock_coerce_function)

        self.mock_field.data = "America/New_York"

        # Mock coerce function to succeed
        self.mock_coerce_function.return_value = "timezone_object"

        # Should not raise any exception
        validator(self.mock_form, self.mock_field)

        # Verify coerce function was called with string data
        self.mock_coerce_function.assert_called_once_with("America/New_York")

    def test_call_invalid_timezone(self):
        """Test validator with invalid timezone."""
        validator = TimeZoneValidator(self.mock_coerce_function)

        self.mock_field.data = "Invalid/Timezone"
        self.mock_field.gettext = Mock(return_value="Not a valid timezone")

        # Mock coerce function to raise exception
        self.mock_coerce_function.side_effect = ValueError("Invalid timezone")

        with pytest.raises(ValidationError, match="Not a valid timezone"):
            validator(self.mock_form, self.mock_field)

    def test_call_with_non_string_data(self):
        """Test validator with non-string data (gets converted to string)."""
        validator = TimeZoneValidator(self.mock_coerce_function)

        self.mock_field.data = 12345

        # Should convert to string before passing to coerce function
        validator(self.mock_form, self.mock_field)

        self.mock_coerce_function.assert_called_once_with("12345")

    def test_call_various_exceptions(self):
        """Test validator with various exception types from coerce function."""
        validator = TimeZoneValidator(self.mock_coerce_function)

        self.mock_field.data = "test"
        self.mock_field.gettext = Mock(return_value="Not a valid timezone")

        # Test different exception types
        exceptions = [
            ValueError("Invalid"),
            TypeError("Wrong type"),
            KeyError("Not found"),
            Exception("Generic error"),
        ]

        for exc in exceptions:
            self.mock_coerce_function.side_effect = exc

            with pytest.raises(ValidationError, match="Not a valid timezone"):
                validator(self.mock_form, self.mock_field)

    def test_expected_error_message_format(self):
        """Test that error message includes expected timezone format examples."""
        validator = TimeZoneValidator(self.mock_coerce_function)

        self.mock_field.data = "invalid"

        # Mock gettext to return the actual message
        expected_msg = (
            'Not a valid timezone (e.g. "America/New_York", '
            '"Africa/Johannesburg", "Asia/Singapore").'
        )
        self.mock_field.gettext = Mock(return_value=expected_msg)

        self.mock_coerce_function.side_effect = ValueError("Invalid")

        with pytest.raises(ValidationError, match="America/New_York"):
            validator(self.mock_form, self.mock_field)


class TestValidatorIntegration:
    """Test validator integration scenarios."""

    def test_unique_validator_with_real_form(self):
        """Test Unique validator with a more realistic form setup."""

        # Create a simple form class
        class TestForm(Form):
            email = StringField("Email")

        form = TestForm()
        form._obj = None # type: ignore

        mock_session = Mock()
        mock_model = ValidatorTestModel

        # Create validator
        validator = Unique(mock_session, mock_model, mock_model.email)

        # Mock session to return no results (unique email)
        mock_exec_result = Mock()
        mock_exec_result.one.side_effect = Exception("No result found")
        mock_session.exec.return_value = mock_exec_result

        # Test with unique value
        form.email.data = "unique@test.com"
        validator(form, form.email)  # Should not raise

    def test_validators_with_wtforms_integration(self):
        """Test validators working with WTForms field setup."""
        # Test that validators work with actual WTForms field objects
        from wtforms import StringField

        field = StringField("Test Field")
        field.data = "USD"
        field.gettext = lambda x: x  # type: ignore # Simple gettext mock

        form = Mock()

        # Should work with real field
        valid_currency(form, field)

    def test_multiple_validators_chain(self):
        """Test multiple validators working together."""
        # This would test how validators work when chained together
        # in a real form validation scenario

        mock_field = Mock()
        mock_form = Mock()

        # Test currency validator
        mock_field.data = "USD"
        mock_field.gettext = lambda x: x
        valid_currency(mock_form, mock_field)

        # Test color validator
        mock_field.data = "#ff0000"
        with patch.dict("sys.modules", {"colour": None}):
            valid_color(mock_form, mock_field)
