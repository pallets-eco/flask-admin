"""
Focused tests for SQLModel fields module to improve coverage.

This file tests utility functions and basic field functionality that can be
properly tested without complex form binding.
"""

from unittest.mock import Mock

import pytest
from sqlmodel import Field
from sqlmodel import SQLModel
from wtforms import Form
from wtforms import ValidationError

from flask_admin.contrib.sqlmodel.fields import CheckboxListField
from flask_admin.contrib.sqlmodel.fields import get_field_id
from flask_admin.contrib.sqlmodel.fields import get_obj_pk
from flask_admin.contrib.sqlmodel.fields import get_pk_from_identity
from flask_admin.contrib.sqlmodel.fields import HstoreForm
from flask_admin.contrib.sqlmodel.fields import KeyValue
from flask_admin.contrib.sqlmodel.fields import QuerySelectField
from flask_admin.contrib.sqlmodel.fields import QuerySelectMultipleField


# Test models
class SimpleTestModel(SQLModel, table=True):
    """Simple test model."""

    __tablename__ = "simple_focused_test_model"

    id: int = Field(primary_key=True)
    name: str

    def __str__(self):
        return self.name


class MultiPKModel(SQLModel, table=True):
    """Model with multiple primary keys."""

    __tablename__ = "multi_pk_focused_model"

    pk1: int = Field(primary_key=True)
    pk2: str = Field(primary_key=True)
    name: str


class TestKeyValue:
    """Test the KeyValue class."""

    def test_init_default(self):
        """Test KeyValue initialization with defaults."""
        kv = KeyValue()
        assert kv.key is None
        assert kv.value is None

    def test_init_with_values(self):
        """Test KeyValue initialization with values."""
        kv = KeyValue("test_key", "test_value")
        assert kv.key == "test_key"
        assert kv.value == "test_value"


class TestHstoreForm:
    """Test the HstoreForm class."""

    def test_form_fields_exist(self):
        """Test that HstoreForm has the required fields."""
        form = HstoreForm()
        assert hasattr(form, "key")
        assert hasattr(form, "value")

    # def test_form_field_labels(self):
    #     """Test that HstoreForm fields have correct labels."""
    #     form = HstoreForm()
    #     assert str(form.key.label.text) == "Key"
    #     assert str(form.value.label.text) == "Value"


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_pk_from_identity_single_pk(self):
        """Test get_pk_from_identity with single primary key."""
        obj = SimpleTestModel(id=123, name="test")
        result = get_pk_from_identity(obj)
        assert result == "123"

    def test_get_pk_from_identity_multi_pk(self):
        """Test get_pk_from_identity with multiple primary keys."""
        obj = MultiPKModel(pk1=1, pk2="test", name="multi")
        result = get_pk_from_identity(obj)
        assert result == "1:test"

    def test_get_pk_from_identity_fallback_with_id(self):
        """Test get_pk_from_identity fallback for objects with id."""
        obj = Mock()
        obj.id = 456
        # Remove __table__ to trigger fallback
        if hasattr(obj, "__table__"):
            delattr(obj, "__table__")

        result = get_pk_from_identity(obj)
        assert result == "456"

    def test_get_pk_from_identity_fallback_without_id(self):
        """Test get_pk_from_identity fallback for objects without id."""
        obj = "string_object"
        result = get_pk_from_identity(obj)
        assert result == "string_object"

    def test_get_obj_pk_single(self):
        """Test get_obj_pk with single primary key."""
        obj = Mock()
        obj.test_pk = 789
        result = get_obj_pk(obj, "test_pk")
        assert result == "789"

    def test_get_obj_pk_tuple(self):
        """Test get_obj_pk with tuple primary keys."""
        obj = Mock()
        obj.pk1 = 1
        obj.pk2 = "test"
        result = get_obj_pk(obj, ("pk1", "pk2"))
        assert result == ("1", "test")

    def test_get_field_id_single(self):
        """Test get_field_id with single ID."""
        field = Mock()
        field.get_pk.return_value = 123
        result = get_field_id(field)
        assert result == "123"

    def test_get_field_id_tuple(self):
        """Test get_field_id with tuple ID."""
        field = Mock()
        field.get_pk.return_value = (1, "test")
        result = get_field_id(field)
        assert result == ("1", "test")


class TestFieldInheritance:
    """Test field inheritance relationships."""

    def test_checkbox_list_field_inherits_from_query_select_multiple(self):
        """Test that CheckboxListField inherits from QuerySelectMultipleField."""
        assert issubclass(CheckboxListField, QuerySelectMultipleField)

    def test_query_select_multiple_field_inherits_from_query_select(self):
        """Test that QuerySelectMultipleField inherits from QuerySelectField."""
        assert issubclass(QuerySelectMultipleField, QuerySelectField)


class TestFormWithFields:
    """Test fields when properly bound to a form."""

    def test_query_select_field_in_form(self):
        """Test QuerySelectField when bound to a form."""
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()

        # Field should be properly bound
        assert hasattr(form.test_field, "query_factory")
        assert form.test_field.query_factory == query_factory

    def test_query_select_multiple_field_in_form(self):
        """Test QuerySelectMultipleField when bound to a form."""
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()

        # Field should be properly bound
        assert hasattr(form.test_field, "query_factory")
        assert form.test_field.query_factory == query_factory

    def test_checkbox_list_field_in_form(self):
        """Test CheckboxListField when bound to a form."""
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = CheckboxListField(query_factory=query_factory)

        form = TestForm()

        # Field should be properly bound and use CheckboxListInput widget
        from flask_admin.contrib.sqlmodel.widgets import CheckboxListInput

        assert isinstance(form.test_field.widget, CheckboxListInput)


class TestFieldParameters:
    """Test field parameter handling."""

    def test_query_select_field_default_parameters(self):
        """Test QuerySelectField default parameter assignment."""
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field

        # Test default parameters
        assert field.allow_blank is False
        assert field.blank_text == ""
        assert field.query is None
        assert field._object_list is None

    def test_query_select_field_custom_parameters(self):
        """Test QuerySelectField with custom parameters."""
        query_factory = Mock(return_value=[])
        custom_get_pk = Mock()

        class TestForm(Form):
            test_field = QuerySelectField(
                query_factory=query_factory,
                get_pk=custom_get_pk,
                allow_blank=True,
                blank_text="Choose one...",
            )

        form = TestForm()
        field = form.test_field

        # Test custom parameters
        assert field.get_pk == custom_get_pk
        assert field.allow_blank is True
        assert field.blank_text == "Choose one..."

    def test_query_select_field_string_get_label(self):
        """Test QuerySelectField with string get_label."""
        # import operator

        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory, get_label="name")

        form = TestForm()
        field = form.test_field

        # Should create an attrgetter
        test_obj = Mock()
        test_obj.name = "test_name"
        result = field.get_label(test_obj)
        assert result == "test_name"

    def test_query_select_multiple_field_default_list(self):
        """Test QuerySelectMultipleField default list behavior."""
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field

        # Default should be empty list
        assert field.default == []
        assert field._invalid_formdata is False


class TestFieldDataProcessing:
    """Test field data processing and validation."""

    def test_query_select_field_process_formdata_normal(self):
        """Test QuerySelectField process_formdata with normal value."""
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field

        # Test process_formdata
        field.process_formdata(["test_value"])
        assert field._formdata == "test_value"

    def test_query_select_field_process_formdata_blank(self):
        """Test QuerySelectField process_formdata with blank value."""
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory, allow_blank=True)

        form = TestForm()
        field = form.test_field

        # Test process_formdata with blank
        field.process_formdata(["__None"])
        assert field.data is None

    def test_query_select_field_process_formdata_empty(self):
        """Test QuerySelectField process_formdata with empty list."""
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field

        # Test process_formdata with empty list
        field.process_formdata([])
        # Should not change _formdata when empty
        assert field._formdata is None

    def test_query_select_multiple_field_process_formdata(self):
        """Test QuerySelectMultipleField process_formdata."""
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field

        # Test process_formdata with duplicates
        field.process_formdata(["value1", "value2", "value1"])
        assert field._formdata == {"value1", "value2"}


class TestFieldValidationBasics:
    """Test basic field validation."""

    def test_query_select_field_blank_validation_allowed(self):
        """Test QuerySelectField validation when blank is allowed."""
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory, allow_blank=True)

        form = TestForm()
        field = form.test_field
        field.data = None

        # Should not raise when blank is allowed and data is None
        field.pre_validate(form)

    def test_query_select_multiple_field_empty_data_validation(self):
        """Test QuerySelectMultipleField validation with empty data."""
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field
        field.data = []
        field._invalid_formdata = False

        # Should not raise with empty data
        field.pre_validate(form)

    def test_query_select_multiple_field_invalid_formdata_validation(self):
        """Test QuerySelectMultipleField validation with invalid formdata."""
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field
        field.gettext = Mock(return_value="Not a valid choice")
        field._invalid_formdata = True

        # Should raise with invalid formdata
        with pytest.raises(ValidationError, match="Not a valid choice"):
            field.pre_validate(form)


class TestInlineHstoreListBasics:
    """Test basic InlineHstoreList functionality."""

    def test_inline_hstore_list_inherits_from_inline_field_list(self):
        """Test InlineHstoreList inheritance."""
        from flask_admin.contrib.sqlmodel.fields import InlineHstoreList
        from flask_admin.model.fields import InlineFieldList

        assert issubclass(InlineHstoreList, InlineFieldList)


class TestWidgetAssignments:
    """Test that fields use correct widgets."""

    def test_query_select_field_uses_select2_widget(self):
        """Test that QuerySelectField uses Select2Widget."""
        from flask_admin.form import Select2Widget

        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        assert isinstance(form.test_field.widget, Select2Widget)
        assert not getattr(form.test_field.widget, "multiple", False)

    def test_query_select_multiple_field_uses_select2_widget_multiple(self):
        """Test that QuerySelectMultipleField uses Select2Widget with multiple=True."""
        from flask_admin.form import Select2Widget

        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        assert isinstance(form.test_field.widget, Select2Widget)
        assert form.test_field.widget.multiple is True

    def test_checkbox_list_field_uses_checkbox_widget(self):
        """Test that CheckboxListField uses CheckboxListInput widget."""
        from flask_admin.contrib.sqlmodel.widgets import CheckboxListInput

        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = CheckboxListField(query_factory=query_factory)

        form = TestForm()
        assert isinstance(form.test_field.widget, CheckboxListInput)


class TestInlineModelOneToOneFieldBasics:
    """Test basic InlineModelOneToOneField functionality."""

    def test_looks_empty_static_method(self):
        """Test InlineModelOneToOneField._looks_empty static method."""
        from flask_admin.contrib.sqlmodel.fields import InlineModelOneToOneField

        # Test with None
        assert InlineModelOneToOneField._looks_empty(None) is True

        # Test with empty string
        assert InlineModelOneToOneField._looks_empty("") is True

        # Test with non-empty string
        assert InlineModelOneToOneField._looks_empty("test") is False

        # Test with other objects
        assert InlineModelOneToOneField._looks_empty(123) is False
        assert InlineModelOneToOneField._looks_empty([]) is False
        assert InlineModelOneToOneField._looks_empty({}) is False


class TestInlineModelFormListBasics:
    """Test basic InlineModelFormList functionality."""

    def test_inline_model_form_list_inherits_from_inline_field_list(self):
        """Test InlineModelFormList inheritance."""
        from flask_admin.contrib.sqlmodel.fields import InlineModelFormList
        from flask_admin.model.fields import InlineFieldList

        assert issubclass(InlineModelFormList, InlineFieldList)

    def test_inline_model_one_to_one_field_inherits_from_inline_model_form_field(self):
        """Test InlineModelOneToOneField inheritance."""
        from flask_admin.contrib.sqlmodel.fields import InlineModelOneToOneField
        from flask_admin.model.fields import InlineModelFormField

        assert issubclass(InlineModelOneToOneField, InlineModelFormField)
