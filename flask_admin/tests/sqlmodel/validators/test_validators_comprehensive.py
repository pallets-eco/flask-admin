"""
Comprehensive tests for SQLModel validators module to improve coverage.

This file tests all validator classes and functions including edge cases,
error handling, and various validation scenarios.
"""

from unittest.mock import Mock

import pytest
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import SQLModel
from wtforms import Form
from wtforms import StringField
from wtforms import ValidationError

from flask_admin.contrib.sqlmodel.validators import ItemsRequired
from flask_admin.contrib.sqlmodel.validators import Unique


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


class TestValidatorIntegration:
    """Test validator integration scenarios."""

    def test_unique_validator_with_real_form(self):
        """Test Unique validator with a more realistic form setup."""

        # Create a simple form class
        class TestForm(Form):
            email = StringField("Email")

        form = TestForm()
        form._obj = None

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
        field.gettext = lambda x: x  # Simple gettext mock

        form = Mock()

        # Test ItemsRequired validator with real field
        items_validator = ItemsRequired(min=1)
        field.entries = [Mock()]
        field.should_delete = Mock(return_value=False)
        items_validator(form, field)

    def test_multiple_validators_chain(self):
        """Test multiple validators working together."""
        # This would test how validators work when chained together
        # in a real form validation scenario

        mock_field = Mock()
        mock_form = Mock()

        # Test ItemsRequired validator
        items_validator = ItemsRequired(min=2)
        mock_field.entries = [Mock(), Mock(), Mock()]
        mock_field.should_delete = Mock(return_value=False)
        items_validator(mock_form, mock_field)
