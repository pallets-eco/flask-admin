"""
Comprehensive tests for SQLModel fields module to improve coverage.

This file tests all field classes, utility functions, and edge cases
to improve test coverage for the fields module.
"""

from typing import Any
from typing import Optional
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import SQLModel
from wtforms import ValidationError

from flask_admin.contrib.sqlmodel.fields import CheckboxListField
from flask_admin.contrib.sqlmodel.fields import get_field_id
from flask_admin.contrib.sqlmodel.fields import get_obj_pk
from flask_admin.contrib.sqlmodel.fields import get_pk_from_identity
from flask_admin.contrib.sqlmodel.fields import HstoreForm
from flask_admin.contrib.sqlmodel.fields import InlineHstoreList
from flask_admin.contrib.sqlmodel.fields import InlineModelFormList
from flask_admin.contrib.sqlmodel.fields import InlineModelOneToOneField
from flask_admin.contrib.sqlmodel.fields import KeyValue
from flask_admin.contrib.sqlmodel.fields import QuerySelectField
from flask_admin.contrib.sqlmodel.fields import QuerySelectMultipleField


# Test models for field testing
class FieldTestModel(SQLModel, table=True):
    """Test model for field testing."""

    id: int = Field(primary_key=True)
    name: str
    email: Optional[str] = None
    active: bool = True

    def __str__(self) -> str:
        return f"FieldTest({self.name})"


class RelatedModel(SQLModel, table=True):
    """Related model for testing relationships."""

    id: int = Field(primary_key=True)
    name: str
    test_model_id: Optional[int] = Field(foreign_key="fieldtestmodel.id")


class MultiPKModel(SQLModel, table=True):
    """Model with multiple primary keys."""

    pk1: int = Field(primary_key=True)
    pk2: str = Field(primary_key=True)
    name: str


class TestQuerySelectField:
    """Test the QuerySelectField class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_session: Mock = Mock(spec=Session)
        self.query_factory: Mock = Mock()

        # Create test data
        self.test_obj1: FieldTestModel = FieldTestModel(id=1, name="Object 1")
        self.test_obj2: FieldTestModel = FieldTestModel(id=2, name="Object 2")
        self.test_objects: list[FieldTestModel] = [self.test_obj1, self.test_obj2]

        self.query_factory.return_value = self.test_objects

    def test_init_default_params(self) -> None:
        """Test QuerySelectField initialization with default parameters."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field

        assert field.query_factory == self.query_factory
        assert field.get_pk == get_pk_from_identity
        assert callable(field.get_label)
        assert not field.allow_blank
        assert field.blank_text == ""
        assert field.query is None
        assert field._object_list is None

    def test_init_custom_params(self) -> None:
        """Test QuerySelectField initialization with custom parameters."""
        from wtforms import Form

        custom_get_pk: Mock = Mock()

        # custom_get_label = lambda x: f"Label: {x.name}"
        def custom_get_label(x: Any) -> str:
            return f"Label: {x.name}"

        class TestForm(Form):
            test_field = QuerySelectField(
                query_factory=self.query_factory,
                get_pk=custom_get_pk,
                get_label=custom_get_label,
                allow_blank=True,
                blank_text="Select one...",
            )

        form: TestForm = TestForm()
        field: Any = form.test_field

        assert field.get_pk == custom_get_pk
        assert field.get_label == custom_get_label
        assert field.allow_blank
        assert field.blank_text == "Select one..."

    def test_init_string_get_label(self) -> None:
        """Test QuerySelectField with string get_label parameter."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(
                query_factory=self.query_factory, get_label="name"
            )

        form: TestForm = TestForm()
        field: Any = form.test_field

        # Should create an attrgetter for 'name'
        result: str = field.get_label(self.test_obj1)
        assert result == "Object 1"

    def test_data_property_getter(self) -> None:
        """Test data property getter without formdata."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field._data = self.test_obj1

        assert field.data == self.test_obj1

    def test_data_property_getter_with_formdata(self) -> None:
        """Test data property getter with formdata."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field._formdata = "1"
        field._data = None

        # Should find and set the object with pk "1"
        data: Any = field.data
        assert data == self.test_obj1

    def test_data_property_setter(self) -> None:
        """Test data property setter."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field._formdata = "some_data"

        field.data = self.test_obj2

        assert field._data == self.test_obj2
        assert field._formdata is None

    def test_get_object_list_basic(self) -> None:
        """Test _get_object_list with basic SQLModel objects."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field

        object_list: list[tuple[str, Any]] = field._get_object_list()

        assert len(object_list) == 2
        assert object_list[0] == ("1", self.test_obj1)
        assert object_list[1] == ("2", self.test_obj2)

    def test_get_object_list_with_row_objects(self) -> None:
        """Test _get_object_list with Row-like objects."""
        from wtforms import Form

        # Mock Row objects that have __len__ and indexing
        mock_row1: Mock = Mock()
        mock_row1.__len__ = Mock(return_value=1)
        mock_row1.__getitem__ = Mock(return_value=self.test_obj1)

        mock_row2: Mock = Mock()
        mock_row2.__len__ = Mock(return_value=1)
        mock_row2.__getitem__ = Mock(return_value=self.test_obj2)

        self.query_factory.return_value = [mock_row1, mock_row2]

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        object_list: list[tuple[str, Any]] = field._get_object_list()

        assert len(object_list) == 2
        # Should extract actual objects from Row objects
        assert object_list[0][1] == self.test_obj1
        assert object_list[1][1] == self.test_obj2

    def test_get_object_list_cached(self) -> None:
        """Test that _get_object_list caches results."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field

        # First call
        object_list1: list[tuple[str, Any]] = field._get_object_list()
        # Second call
        object_list2: list[tuple[str, Any]] = field._get_object_list()

        # Should be the same cached object
        assert object_list1 is object_list2
        # Query factory should only be called once
        self.query_factory.assert_called_once()

    def test_iter_choices_without_blank(self) -> None:
        """Test iter_choices without blank option."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field.data = self.test_obj1

        choices: list[tuple[str, Any, bool]] = list(field.iter_choices())

        assert len(choices) == 2
        # First choice should be selected (test_obj1)
        assert choices[0][0] == "1"
        assert choices[0][1] == self.test_obj1
        assert choices[0][2] is True
        assert choices[1][0] == "2"
        assert choices[1][1] == self.test_obj2
        assert choices[1][2] is False

    def test_iter_choices_with_blank(self) -> None:
        """Test iter_choices with blank option."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(
                query_factory=self.query_factory,
                allow_blank=True,
                blank_text="Choose one...",
            )

        form: TestForm = TestForm()
        field: Any = form.test_field
        field.data = None

        choices: list[tuple[str, Any, bool]] = list(field.iter_choices())

        assert len(choices) == 3
        # First choice should be blank and selected
        assert choices[0][0] == "__None"
        assert choices[0][1] == "Choose one..."
        assert choices[0][2] is True
        assert choices[1][0] == "1"
        assert choices[1][1] == self.test_obj1
        assert choices[1][2] is False
        assert choices[2][0] == "2"
        assert choices[2][1] == self.test_obj2
        assert choices[2][2] is False

    def test_process_formdata_normal_value(self) -> None:
        """Test process_formdata with normal value."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field

        field.process_formdata(["1"])

        assert field._data is None
        assert field._formdata == "1"

    def test_process_formdata_blank_value(self) -> None:
        """Test process_formdata with blank value."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(
                query_factory=self.query_factory, allow_blank=True
            )

        form: TestForm = TestForm()
        field: Any = form.test_field

        field.process_formdata(["__None"])

        assert field.data is None

    def test_process_formdata_empty_list(self) -> None:
        """Test process_formdata with empty value list."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field

        field.process_formdata([])

        # Should not change anything when valuelist is empty
        assert field._formdata is None

    def test_pre_validate_valid_choice(self) -> None:
        """Test pre_validate with valid choice."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field.data = self.test_obj1

        # Should not raise any exception
        field.pre_validate(None)

    def test_pre_validate_blank_allowed(self) -> None:
        """Test pre_validate with blank value when allowed."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(
                query_factory=self.query_factory, allow_blank=True
            )

        form: TestForm = TestForm()
        field: Any = form.test_field
        field.data = None

        # Should not raise any exception
        field.pre_validate(None)

    def test_pre_validate_invalid_choice(self) -> None:
        """Test pre_validate with invalid choice."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field.gettext = Mock(return_value="Not a valid choice")
        # Set data to an object not in the query
        invalid_obj: FieldTestModel = FieldTestModel(id=999, name="Invalid")
        field.data = invalid_obj

        with pytest.raises(ValidationError, match="Not a valid choice"):
            field.pre_validate(None)


class TestQuerySelectMultipleField:
    """Test the QuerySelectMultipleField class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_session: Mock = Mock(spec=Session)
        self.query_factory: Mock = Mock()

        # Create test data
        self.test_obj1: FieldTestModel = FieldTestModel(id=1, name="Object 1")
        self.test_obj2: FieldTestModel = FieldTestModel(id=2, name="Object 2")
        self.test_obj3: FieldTestModel = FieldTestModel(id=3, name="Object 3")
        self.test_objects: list[FieldTestModel] = [
            self.test_obj1,
            self.test_obj2,
            self.test_obj3,
        ]

        self.query_factory.return_value = self.test_objects

    def test_init_default_params(self) -> None:
        """Test QuerySelectMultipleField initialization."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field

        assert field.query_factory == self.query_factory
        assert field.default == []
        assert not field._invalid_formdata

    def test_init_custom_default(self) -> None:
        """Test QuerySelectMultipleField with custom default."""
        from wtforms import Form

        custom_default: list[FieldTestModel] = [self.test_obj1]

        class TestForm(Form):
            test_field = QuerySelectMultipleField(
                query_factory=self.query_factory, default=custom_default
            )

        form: TestForm = TestForm()
        field: Any = form.test_field

        assert field.default == custom_default

    def test_data_property_getter_no_formdata(self) -> None:
        """Test data property getter without formdata."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field._data = [self.test_obj1, self.test_obj2]

        assert field.data == [self.test_obj1, self.test_obj2]

    def test_data_property_getter_with_formdata(self) -> None:
        """Test data property getter with formdata."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field._formdata = {"1", "3"}  # Select objects 1 and 3
        field._data = None

        data: list[FieldTestModel] = field.data

        assert len(data) == 2
        assert self.test_obj1 in data
        assert self.test_obj3 in data
        assert self.test_obj2 not in data

    def test_data_property_getter_with_invalid_formdata(self) -> None:
        """Test data property getter with invalid formdata."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field._formdata = {"1", "999"}  # "999" is invalid
        field._data = None

        data: list[FieldTestModel] = field.data

        assert len(data) == 1
        assert self.test_obj1 in data
        assert field._invalid_formdata  # Should mark as invalid

    def test_data_property_setter(self) -> None:
        """Test data property setter."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field._formdata = {"some", "data"}

        field.data = [self.test_obj2, self.test_obj3]

        assert field._data == [self.test_obj2, self.test_obj3]
        assert field._formdata is None

    def test_iter_choices(self) -> None:
        """Test iter_choices."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field.data = [self.test_obj1, self.test_obj3]

        choices: list[tuple[str, Any, bool]] = list(field.iter_choices())

        assert len(choices) == 3
        assert choices[0][0] == "1"
        assert choices[0][1] == self.test_obj1
        assert choices[0][2] is True  # Selected
        assert choices[1][0] == "2"
        assert choices[1][1] == self.test_obj2
        assert choices[1][2] is False  # Not selected
        assert choices[2][0] == "3"
        assert choices[2][1] == self.test_obj3
        assert choices[2][2] is True  # Selected

    def test_process_formdata(self) -> None:
        """Test process_formdata."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field

        field.process_formdata(["1", "2", "1"])  # Duplicates should be handled

        assert field._formdata == {"1", "2"}

    def test_pre_validate_valid_data(self) -> None:
        """Test pre_validate with valid data."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field.data = [self.test_obj1, self.test_obj2]
        field._invalid_formdata = False

        # Should not raise any exception
        field.pre_validate(None)

    def test_pre_validate_invalid_formdata(self) -> None:
        """Test pre_validate with invalid formdata."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field.gettext = Mock(return_value="Not a valid choice")
        field._invalid_formdata = True

        with pytest.raises(ValidationError, match="Not a valid choice"):
            field.pre_validate(None)

    def test_pre_validate_invalid_object_in_data(self) -> None:
        """Test pre_validate with invalid object in data."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field.gettext = Mock(return_value="Not a valid choice")
        field._invalid_formdata = False

        # Add an object that's not in the query
        invalid_obj: FieldTestModel = FieldTestModel(id=999, name="Invalid")
        field.data = [self.test_obj1, invalid_obj]

        with pytest.raises(ValidationError, match="Not a valid choice"):
            field.pre_validate(None)

    def test_pre_validate_empty_data(self) -> None:
        """Test pre_validate with empty data."""
        from wtforms import Form

        class TestForm(Form):
            test_field = QuerySelectMultipleField(query_factory=self.query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field
        field.data = []
        field._invalid_formdata = False

        # Should not raise any exception
        field.pre_validate(None)


class TestCheckboxListField:
    """Test the CheckboxListField class."""

    def test_widget_type(self) -> None:
        """Test that CheckboxListField uses the correct widget."""
        from wtforms import Form

        from flask_admin.contrib.sqlmodel.widgets import CheckboxListInput

        query_factory: Mock = Mock(return_value=[])

        class TestForm(Form):
            test_field = CheckboxListField(query_factory=query_factory)

        form: TestForm = TestForm()
        field: Any = form.test_field

        # Should inherit from QuerySelectMultipleField but use CheckboxListInput
        assert isinstance(field.widget, CheckboxListInput)


class TestKeyValue:
    """Test the KeyValue class."""

    def test_init_default(self) -> None:
        """Test KeyValue initialization with defaults."""
        kv: KeyValue = KeyValue()

        assert kv.key is None
        assert kv.value is None

    def test_init_with_values(self) -> None:
        """Test KeyValue initialization with values."""
        kv: KeyValue = KeyValue("test_key", "test_value")

        assert kv.key == "test_key"
        assert kv.value == "test_value"


class TestHstoreForm:
    """Test the HstoreForm class."""

    def test_form_fields(self) -> None:
        """Test that HstoreForm has the correct fields."""
        form = HstoreForm()

        assert hasattr(form, "key")
        assert hasattr(form, "value")
        assert str(form.key.label.text) == "Key"
        assert str(form.value.label.text) == "Value"


class TestInlineHstoreList:
    """Test the InlineHstoreList class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_form_field = Mock()

    def test_process_with_dict_data(self) -> None:
        """Test process method with dict data."""
        from wtforms import Form
        from wtforms.fields import StringField
        from wtforms.fields.core import UnboundField

        # Create a proper UnboundField
        unbound_field = UnboundField(StringField)

        class TestForm(Form):
            pass

        # Create field and bind it manually
        form = TestForm()
        field = InlineHstoreList(unbound_field)
        field = field.bind(form=form, name="test_field")

        # Mock the superclass process method
        with patch(
            "flask_admin.contrib.sqlmodel.fields.InlineFieldList.process"
        ) as mock_super_process:
            test_data = {"key1": "value1", "key2": "value2"}

            field.process(None, test_data)

            # Should convert dict to KeyValue list
            mock_super_process.assert_called_once()
            processed_data = mock_super_process.call_args[0][1]

            assert len(processed_data) == 2
            assert all(isinstance(item, KeyValue) for item in processed_data)

    def test_process_with_non_dict_data(self) -> None:
        """Test process method with non-dict data."""
        from wtforms import Form
        from wtforms.fields import StringField
        from wtforms.fields.core import UnboundField

        # Create a proper UnboundField
        unbound_field = UnboundField(StringField)

        class TestForm(Form):
            pass

        # Create field and bind it manually
        form = TestForm()
        field = InlineHstoreList(unbound_field)
        field = field.bind(form=form, name="test_field")

        # Mock the superclass process method
        with patch(
            "flask_admin.contrib.sqlmodel.fields.InlineFieldList.process"
        ) as mock_super_process:
            test_data = ["not", "a", "dict"]

            field.process(None, test_data)

            # Should pass data unchanged
            mock_super_process.assert_called_once_with(None, test_data, None)

    def test_populate_obj(self) -> None:
        """Test populate_obj method."""
        from wtforms import Form
        from wtforms.fields import StringField
        from wtforms.fields.core import UnboundField

        # Create a proper UnboundField
        unbound_field = UnboundField(StringField)

        class TestForm(Form):
            pass

        # Create field and bind it manually
        form = TestForm()
        field = InlineHstoreList(unbound_field)
        field = field.bind(form=form, name="test_field")

        # Mock form field entries
        mock_entry1 = Mock()
        mock_entry2 = Mock()
        field.entries = [mock_entry1, mock_entry2]

        # Mock should_delete to return False
        field.should_delete = Mock(return_value=False)

        # Mock populate_obj behavior - simulate what the form fields would do
        def populate_entry1(obj, name):
            obj.data.key = "key1"
            obj.data.value = "value1"

        def populate_entry2(obj, name):
            obj.data.key = "key2"
            obj.data.value = "value2"

        mock_entry1.populate_obj.side_effect = populate_entry1
        mock_entry2.populate_obj.side_effect = populate_entry2

        # Test object
        test_obj = Mock()

        field.populate_obj(test_obj, "hstore_field")

        # Should set the hstore field as a dict
        expected_dict = {"key1": "value1", "key2": "value2"}
        # Check that setattr was called correctly
        # - the field should have set the attribute
        assert test_obj.hstore_field == expected_dict


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_pk_from_identity_sqlmodel_single_pk(self) -> None:
        """Test get_pk_from_identity with SQLModel instance (single PK)."""
        obj: FieldTestModel = FieldTestModel(id=123, name="test")

        result = get_pk_from_identity(obj)

        assert result == "123"

    def test_get_pk_from_identity_sqlmodel_multi_pk(self) -> None:
        """Test get_pk_from_identity with SQLModel instance (multiple PKs)."""
        obj: MultiPKModel = MultiPKModel(pk1=1, pk2="test", name="multi")

        result = get_pk_from_identity(obj)

        assert result == "1:test"

    def test_get_pk_from_identity_fallback(self) -> None:
        """Test get_pk_from_identity fallback for other objects."""
        # Object with id attribute
        obj_with_id = Mock()
        obj_with_id.id = 456
        obj_with_id.__table__ = None  # Not a SQLModel
        delattr(obj_with_id, "__table__")

        result = get_pk_from_identity(obj_with_id)

        assert result == "456"

    def test_get_pk_from_identity_fallback_no_id(self) -> None:
        """Test get_pk_from_identity fallback for objects without id."""
        obj = "string_object"

        result = get_pk_from_identity(obj)

        assert result == "string_object"

    def test_get_obj_pk_single(self) -> None:
        """Test get_obj_pk with single primary key."""
        obj = Mock()
        obj.id = 789

        result = get_obj_pk(obj, "id")

        assert result == "789"

    def test_get_obj_pk_tuple(self) -> None:
        """Test get_obj_pk with tuple primary keys."""
        obj = Mock()
        obj.pk1 = 1
        obj.pk2 = "test"

        result = get_obj_pk(obj, ("pk1", "pk2"))

        assert result == ("1", "test")

    def test_get_field_id_single(self) -> None:
        """Test get_field_id with single ID."""
        field = Mock()
        field.get_pk.return_value = 123

        result = get_field_id(field)

        assert result == "123"

    def test_get_field_id_tuple(self) -> None:
        """Test get_field_id with tuple ID."""
        field = Mock()
        field.get_pk.return_value = (1, "test")

        result = get_field_id(field)

        assert result == ("1", "test")


class TestInlineModelFormList:
    """Test the InlineModelFormList class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_form = Mock()
        self.mock_session = Mock()
        self.mock_model = FieldTestModel
        self.mock_prop = "test_prop"
        self.mock_inline_view = Mock()
        self.mock_inline_view.form_widget_args = None
        self.mock_inline_view._form_rules = []

    def test_init(self) -> None:
        """Test InlineModelFormList initialization."""
        from wtforms import Form

        with patch(
            "flask_admin.contrib.sqlmodel.fields.get_primary_key"
        ) as mock_get_pk:
            mock_get_pk.return_value = "id"

            # Create the unbound field first
            unbound_field = InlineModelFormList(
                self.mock_form,
                self.mock_session,
                self.mock_model,
                self.mock_prop,
                self.mock_inline_view,
            )

            # Bind it to a form
            class TestForm(Form):
                pass

            form = TestForm()
            field = unbound_field.bind(form=form, name="test_field")

            assert field.form == self.mock_form
            assert field.session == self.mock_session
            assert field.model == self.mock_model
            assert field.prop == self.mock_prop
            assert field.inline_view == self.mock_inline_view
            assert field._pk == "id"

    def test_display_row_controls_with_pk(self) -> None:
        """Test display_row_controls when field has PK."""
        from wtforms import Form

        # Create the unbound field first
        unbound_field = InlineModelFormList(
            self.mock_form,
            self.mock_session,
            self.mock_model,
            self.mock_prop,
            self.mock_inline_view,
        )

        # Bind it to a form
        class TestForm(Form):
            pass

        form = TestForm()
        field = unbound_field.bind(form=form, name="test_field")

        mock_field = Mock()
        mock_field.get_pk.return_value = "123"

        result = field.display_row_controls(mock_field)

        assert result is True

    def test_display_row_controls_without_pk(self) -> None:
        """Test display_row_controls when field has no PK."""
        from wtforms import Form

        # Create the unbound field first
        unbound_field = InlineModelFormList(
            self.mock_form,
            self.mock_session,
            self.mock_model,
            self.mock_prop,
            self.mock_inline_view,
        )

        # Bind it to a form
        class TestForm(Form):
            pass

        form = TestForm()
        field = unbound_field.bind(form=form, name="test_field")

        mock_field = Mock()
        mock_field.get_pk.return_value = None

        result = field.display_row_controls(mock_field)

        assert result is False


class TestInlineModelOneToOneField:
    """Test the InlineModelOneToOneField class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_form = Mock()
        self.mock_session = Mock()
        self.mock_model = FieldTestModel
        self.mock_prop = "test_prop"
        self.mock_inline_view = Mock()
        self.mock_inline_view.form_widget_args = None
        self.mock_inline_view._form_rules = []

    def test_init(self) -> None:
        """Test InlineModelOneToOneField initialization."""
        from wtforms import Form

        with patch(
            "flask_admin.contrib.sqlmodel.fields.get_primary_key"
        ) as mock_get_pk:
            mock_get_pk.return_value = "id"

            # Create the unbound field first
            unbound_field = InlineModelOneToOneField(
                self.mock_form,
                self.mock_session,
                self.mock_model,
                self.mock_prop,
                self.mock_inline_view,
            )

            # Bind it to a form
            class TestForm(Form):
                pass

            form = TestForm()
            field = unbound_field.bind(form=form, name="test_field")

            assert field.form == self.mock_form
            assert field.session == self.mock_session
            assert field.model == self.mock_model
            assert field.prop == self.mock_prop
            assert field.inline_view == self.mock_inline_view
            assert field._pk == "id"

    def test_looks_empty_none(self) -> None:
        """Test _looks_empty with None."""
        result = InlineModelOneToOneField._looks_empty(None)
        assert result is True

    def test_looks_empty_empty_string(self) -> None:
        """Test _looks_empty with empty string."""
        result = InlineModelOneToOneField._looks_empty("")
        assert result is True

    def test_looks_empty_non_empty_string(self) -> None:
        """Test _looks_empty with non-empty string."""
        result = InlineModelOneToOneField._looks_empty("test")
        assert result is False

    def test_looks_empty_other_objects(self) -> None:
        """Test _looks_empty with other objects."""
        result = InlineModelOneToOneField._looks_empty(123)
        assert result is False

    def test_populate_obj_form_empty(self) -> None:
        """Test populate_obj when form is empty."""
        from wtforms import Form

        # Create the unbound field first
        unbound_field = InlineModelOneToOneField(
            self.mock_form,
            self.mock_session,
            self.mock_model,
            self.mock_prop,
            self.mock_inline_view,
        )

        # Bind it to a form
        class TestForm(Form):
            pass

        form = TestForm()
        field = unbound_field.bind(form=form, name="test_field")
        field._pk = "id"

        # Mock form fields to be empty
        mock_field1 = Mock()
        mock_field1.data = ""
        mock_field2 = Mock()
        mock_field2.data = None
        mock_id_field = Mock()
        mock_id_field.data = None  # Make sure ID field is also empty

        field.form._fields = {
            "field1": mock_field1,
            "field2": mock_field2,
            "id": mock_id_field,
        }

        test_model = Mock()

        # Should return early and not create anything
        field.populate_obj(test_model, "inline_field")

        # For empty forms, the method should return early without setting the field
        # Since we're using a Mock, we need to check if setattr was called
        # The actual implementation should not set the attribute for empty forms
        # Let's check that inline_view.on_model_change was not called
        field.inline_view.on_model_change.assert_not_called()

    def test_populate_obj_creates_new_model(self) -> None:
        """Test populate_obj creates new inline model."""
        from wtforms import Form

        # Create the unbound field first
        unbound_field = InlineModelOneToOneField(
            self.mock_form,
            self.mock_session,
            self.mock_model,
            self.mock_prop,
            self.mock_inline_view,
        )

        # Bind it to a form
        class TestForm(Form):
            pass

        form = TestForm()
        field = unbound_field.bind(form=form, name="test_field")
        field._pk = "id"

        # Mock form fields with data
        mock_field1 = Mock()
        mock_field1.data = "test_value"

        field.form._fields = {"field1": mock_field1, "id": Mock()}

        test_model = Mock()
        test_model.inline_field = None

        with patch.object(field, "model") as mock_model_class:
            mock_inline_instance = Mock()
            mock_model_class.return_value = mock_inline_instance

            field.populate_obj(test_model, "inline_field")

            # Should create new model and populate it
            mock_model_class.assert_called_once()
            mock_field1.populate_obj.assert_called_once_with(
                mock_inline_instance, "field1"
            )

            # Should set the inline model on the main model
            assert test_model.inline_field == mock_inline_instance

            # Should call on_model_change
            field.inline_view.on_model_change.assert_called_once()
