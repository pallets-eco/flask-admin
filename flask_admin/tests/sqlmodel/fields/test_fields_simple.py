"""
Simple focused tests for SQLModel fields module to improve coverage.

This file tests key functionality and edge cases for fields classes.
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

    __tablename__ = "simple_test_model_fields"

    id: int = Field(primary_key=True)
    name: str

    def __str__(self):
        return self.name


class MultiPKModel(SQLModel, table=True):
    """Model with multiple primary keys."""

    __tablename__ = "multi_pk_model_fields"

    pk1: int = Field(primary_key=True)
    pk2: str = Field(primary_key=True)
    name: str


class MockForm(Form):
    """Mock form for field testing."""

    pass


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


class TestQuerySelectFieldBasics:
    """Test basic QuerySelectField functionality."""

    def test_widget_type(self):
        """Test that QuerySelectField uses Select2Widget."""
        from wtforms import Form

        from flask_admin.form import Select2Widget

        # Create field with minimal setup
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        assert isinstance(form.test_field.widget, Select2Widget)

    def test_get_pk_from_identity_function_assignment(self):
        """Test that get_pk defaults to get_pk_from_identity."""
        from wtforms import Form

        from flask_admin.contrib.sqlmodel.fields import get_pk_from_identity

        # Test during initialization
        query_factory = Mock()

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        assert form.test_field.get_pk == get_pk_from_identity

    def test_string_get_label_creates_attrgetter(self):
        """Test that string get_label creates an attrgetter."""
        from wtforms import Form

        query_factory = Mock()

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory, get_label="name")

        form = TestForm()

        # Should create an attrgetter
        test_obj = Mock()
        test_obj.name = "test_name"
        result = form.test_field.get_label(test_obj)
        assert result == "test_name"

    def test_allow_blank_and_blank_text(self):
        """Test allow_blank and blank_text parameters."""
        from wtforms import Form

        query_factory = Mock()

        class TestForm(Form):
            test_field = QuerySelectField(
                query_factory=query_factory,
                allow_blank=True,
                blank_text="Choose one...",
            )

        form = TestForm()
        assert form.test_field.allow_blank is True
        assert form.test_field.blank_text == "Choose one..."


class TestQuerySelectMultipleFieldBasics:
    """Test basic QuerySelectMultipleField functionality."""

    def test_widget_type(self):
        """Test that QuerySelectMultipleField uses Select2Widget with multiple=True."""
        from wtforms import Form

        from flask_admin.form import Select2Widget

        # Create field with minimal setup
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        assert isinstance(form.test_field.widget, Select2Widget)
        assert form.test_field.widget.multiple is True

    def test_default_initialization(self):
        """Test default initialization."""
        from wtforms import Form

        query_factory = Mock()

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        assert form.test_field.default == []
        assert form.test_field._invalid_formdata is False

    def test_custom_default(self):
        """Test initialization with custom default."""
        from wtforms import Form

        query_factory = Mock()
        custom_default = [Mock(), Mock()]

        class TestForm(Form):
            test_field = QuerySelectMultipleField(
                query_factory=query_factory, default=custom_default
            )

        form = TestForm()
        assert form.test_field.default == custom_default


class TestCheckboxListField:
    """Test the CheckboxListField class."""

    def test_inherits_from_query_select_multiple(self):
        """Test that CheckboxListField inherits from QuerySelectMultipleField."""
        assert issubclass(CheckboxListField, QuerySelectMultipleField)

    def test_widget_type(self):
        """Test that CheckboxListField uses CheckboxListInput widget."""
        from wtforms import Form

        from flask_admin.contrib.sqlmodel.widgets import CheckboxListInput

        # Create field with minimal setup
        query_factory = Mock(return_value=[])

        class TestForm(Form):
            test_field = CheckboxListField(query_factory=query_factory)

        form = TestForm()
        assert isinstance(form.test_field.widget, CheckboxListInput)


class TestFieldProcessing:
    """Test field data processing functionality."""

    def setup_method(self):
        """Set up test data."""
        self.obj1 = SimpleTestModel(id=1, name="Object 1")
        self.obj2 = SimpleTestModel(id=2, name="Object 2")
        self.test_objects = [self.obj1, self.obj2]

    def test_query_select_field_data_property_basic(self):
        """Test QuerySelectField data property basic functionality."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field

        # Test setter
        field.data = self.obj1
        assert field._data == self.obj1
        assert field._formdata is None

        # Test getter
        assert field.data == self.obj1

    def test_query_select_field_formdata_processing(self):
        """Test QuerySelectField formdata processing."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field

        # Test process_formdata
        field.process_formdata(["1"])
        assert field._formdata == "1"
        assert field._data is None

    def test_query_select_field_blank_processing(self):
        """Test QuerySelectField blank value processing."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory, allow_blank=True)

        form = TestForm()
        field = form.test_field

        # Test process_formdata with blank
        field.process_formdata(["__None"])
        assert field.data is None

    def test_query_select_multiple_field_formdata_processing(self):
        """Test QuerySelectMultipleField formdata processing."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field

        # Test process_formdata
        field.process_formdata(["1", "2", "1"])  # Test deduplication
        assert field._formdata == {"1", "2"}

    def test_query_select_multiple_field_data_setter(self):
        """Test QuerySelectMultipleField data setter."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field

        # Test setter
        field.data = [self.obj1, self.obj2]
        assert field._data == [self.obj1, self.obj2]
        assert field._formdata is None


class TestFieldValidation:
    """Test field validation functionality."""

    def setup_method(self):
        """Set up test data."""
        self.obj1 = SimpleTestModel(id=1, name="Object 1")
        self.obj2 = SimpleTestModel(id=2, name="Object 2")
        self.test_objects = [self.obj1, self.obj2]

    def test_query_select_field_valid_choice(self):
        """Test QuerySelectField validation with valid choice."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field
        field.data = self.obj1

        # Should not raise
        field.pre_validate(None)

    def test_query_select_field_blank_allowed(self):
        """Test QuerySelectField validation with blank when allowed."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory, allow_blank=True)

        form = TestForm()
        field = form.test_field
        field.data = None

        # Should not raise
        field.pre_validate(None)

    def test_query_select_field_invalid_choice(self):
        """Test QuerySelectField validation with invalid choice."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field
        field.gettext = Mock(return_value="Not a valid choice")

        # Set invalid data
        invalid_obj = SimpleTestModel(id=999, name="Invalid")
        field.data = invalid_obj

        with pytest.raises(ValidationError, match="Not a valid choice"):
            field.pre_validate(None)

    def test_query_select_multiple_field_valid_data(self):
        """Test QuerySelectMultipleField validation with valid data."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field
        field.data = [self.obj1]
        field._invalid_formdata = False

        # Should not raise
        field.pre_validate(None)

    def test_query_select_multiple_field_invalid_formdata(self):
        """Test QuerySelectMultipleField validation with invalid formdata."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field
        field.gettext = Mock(return_value="Not a valid choice")
        field._invalid_formdata = True

        with pytest.raises(ValidationError, match="Not a valid choice"):
            field.pre_validate(None)

    def test_query_select_multiple_field_invalid_object(self):
        """Test QuerySelectMultipleField validation with invalid object."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field
        field.gettext = Mock(return_value="Not a valid choice")
        field._invalid_formdata = False

        invalid_obj = SimpleTestModel(id=999, name="Invalid")
        field.data = [self.obj1, invalid_obj]

        with pytest.raises(ValidationError, match="Not a valid choice"):
            field.pre_validate(None)


class TestFieldChoices:
    """Test field choice iteration functionality."""

    def setup_method(self):
        """Set up test data."""
        self.obj1 = SimpleTestModel(id=1, name="Object 1")
        self.obj2 = SimpleTestModel(id=2, name="Object 2")
        self.test_objects = [self.obj1, self.obj2]

    def test_query_select_field_choices_without_blank(self):
        """Test QuerySelectField choices without blank."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field
        field.data = self.obj1

        choices = list(field.iter_choices())
        assert len(choices) == 2

        # Check choice format (value, label, selected)
        assert choices[0][0] == "1"  # value
        assert choices[0][1] == self.obj1  # label
        assert choices[0][2] is True  # selected

        assert choices[1][0] == "2"
        assert choices[1][1] == self.obj2
        assert choices[1][2] is False

    def test_query_select_field_choices_with_blank(self):
        """Test QuerySelectField choices with blank."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectField(
                query_factory=query_factory, allow_blank=True, blank_text="Select..."
            )

        form = TestForm()
        field = form.test_field
        field.data = None

        choices = list(field.iter_choices())
        assert len(choices) == 3

        # First choice should be blank
        assert choices[0][0] == "__None"
        assert choices[0][1] == "Select..."
        assert choices[0][2] is True  # selected (data is None)

    def test_query_select_multiple_field_choices(self):
        """Test QuerySelectMultipleField choices."""
        from wtforms import Form

        query_factory = Mock(return_value=self.test_objects)

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field
        field.data = [self.obj1]

        choices = list(field.iter_choices())
        assert len(choices) == 2

        assert choices[0][0] == "1"
        assert choices[0][2] is True  # selected
        assert choices[1][0] == "2"
        assert choices[1][2] is False  # not selected


class TestRowObjectHandling:
    """Test handling of Row-like objects in queries."""

    def test_query_select_field_row_objects(self):
        """Test QuerySelectField with Row-like objects."""
        from wtforms import Form

        obj1 = SimpleTestModel(id=1, name="Object 1")
        obj2 = SimpleTestModel(id=2, name="Object 2")

        # Mock Row objects
        row1 = Mock()
        row1.__len__ = Mock(return_value=1)
        row1.__getitem__ = Mock(return_value=obj1)

        row2 = Mock()
        row2.__len__ = Mock(return_value=1)
        row2.__getitem__ = Mock(return_value=obj2)

        query_factory = Mock(return_value=[row1, row2])

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field

        # Should handle Row objects correctly
        object_list = field._get_object_list()

        assert len(object_list) == 2
        assert object_list[0][1] == obj1  # Extracted from row
        assert object_list[1][1] == obj2  # Extracted from row

    def test_query_select_field_direct_objects(self):
        """Test QuerySelectField with direct SQLModel objects."""
        from wtforms import Form

        obj1 = SimpleTestModel(id=1, name="Object 1")
        obj2 = SimpleTestModel(id=2, name="Object 2")

        query_factory = Mock(return_value=[obj1, obj2])

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field

        object_list = field._get_object_list()

        assert len(object_list) == 2
        assert object_list[0] == ("1", obj1)
        assert object_list[1] == ("2", obj2)


class TestObjectListCaching:
    """Test object list caching functionality."""

    def test_query_select_field_caching(self):
        """Test that QuerySelectField caches object list."""
        from wtforms import Form

        obj1 = SimpleTestModel(id=1, name="Object 1")
        query_factory = Mock(return_value=[obj1])

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field

        # First call
        list1 = field._get_object_list()
        # Second call
        list2 = field._get_object_list()

        # Should be the same cached object
        assert list1 is list2
        # Query factory should only be called once
        query_factory.assert_called_once()

    def test_query_select_multiple_field_inherits_caching(self):
        """Test that QuerySelectMultipleField inherits caching."""
        from wtforms import Form

        obj1 = SimpleTestModel(id=1, name="Object 1")
        query_factory = Mock(return_value=[obj1])

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=query_factory)

        form = TestForm()
        field = form.test_field

        # First call
        list1 = field._get_object_list()
        # Second call
        list2 = field._get_object_list()

        # Should be the same cached object
        assert list1 is list2
        query_factory.assert_called_once()
