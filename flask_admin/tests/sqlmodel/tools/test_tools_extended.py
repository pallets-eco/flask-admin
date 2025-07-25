"""
Extended tests for SQLModel tools module to improve coverage.
"""

from typing import Optional
from typing import Union
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlmodel import Field
from sqlmodel import SQLModel

from flask_admin.contrib.sqlmodel.tools import _get_python_type_info
from flask_admin.contrib.sqlmodel.tools import _get_sqlmodel_property_info
from flask_admin.contrib.sqlmodel.tools import _is_special_pydantic_type
from flask_admin.contrib.sqlmodel.tools import create_property_setter
from flask_admin.contrib.sqlmodel.tools import debug_model_fields
from flask_admin.contrib.sqlmodel.tools import filter_foreign_columns
from flask_admin.contrib.sqlmodel.tools import get_columns_for_field
from flask_admin.contrib.sqlmodel.tools import get_field_constraints
from flask_admin.contrib.sqlmodel.tools import get_field_python_type
from flask_admin.contrib.sqlmodel.tools import get_field_value_with_fallback
from flask_admin.contrib.sqlmodel.tools import get_model_field_summary
from flask_admin.contrib.sqlmodel.tools import get_model_fields
from flask_admin.contrib.sqlmodel.tools import get_readonly_fields
from flask_admin.contrib.sqlmodel.tools import get_wtform_compatible_fields
from flask_admin.contrib.sqlmodel.tools import is_field_optional
from flask_admin.contrib.sqlmodel.tools import is_sqlmodel_class
from flask_admin.contrib.sqlmodel.tools import make_computed_field_wtforms_compatible
from flask_admin.contrib.sqlmodel.tools import ModelField
from flask_admin.contrib.sqlmodel.tools import parse_like_term
from flask_admin.contrib.sqlmodel.tools import PYDANTIC_TYPES_AVAILABLE
from flask_admin.contrib.sqlmodel.tools import resolve_model
from flask_admin.contrib.sqlmodel.tools import set_field_value_with_fallback
from flask_admin.contrib.sqlmodel.tools import SQLMODEL_AVAILABLE
from flask_admin.contrib.sqlmodel.tools import tuple_operator_in
from flask_admin.contrib.sqlmodel.tools import validate_field_type


# Test models
class MockSQLModelClass(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    email: Optional[str] = None
    active: bool = True

    @property
    def display_name(self) -> str:
        return f"User: {self.name}"

    @display_name.setter
    def display_name(self, value: str):
        self.name = value.replace("User: ", "")

    @property
    def readonly_field(self) -> str:
        return f"readonly_{self.name}"


class MockSQLAlchemyModelClass:
    """Mock SQLAlchemy model for testing."""

    __tablename__ = "test_table"

    def __init__(self):
        self.id = Column(Integer, primary_key=True)
        self.name = Column(String(50))


class TestParseLikeTerm:
    """Test parse_like_term function."""

    def test_parse_like_term_starts_with(self):
        """Test parsing term that starts with ^."""
        result = parse_like_term("^hello")
        assert result == "hello%"

    def test_parse_like_term_exact_match(self):
        """Test parsing term that starts with =."""
        result = parse_like_term("=exact")
        assert result == "exact"

    def test_parse_like_term_contains(self):
        """Test parsing normal term (contains)."""
        result = parse_like_term("search")
        assert result == "%search%"

    def test_parse_like_term_empty(self):
        """Test parsing empty term."""
        result = parse_like_term("")
        assert result == "%%"

    def test_parse_like_term_special_chars(self):
        """Test parsing term with special characters."""
        result = parse_like_term("test%_")
        assert result == "%test%_%"


class TestPythonTypeInfo:
    """Test _get_python_type_info function."""

    def test_simple_type(self):
        """Test simple type without Optional or Union."""
        info = _get_python_type_info(str)
        assert info["base_type"] is str
        assert not info["is_optional"]
        assert not info["is_union"]
        assert info["union_types"] == []

    def test_optional_type(self):
        """Test Optional type."""
        info = _get_python_type_info(Optional[str])
        assert info["base_type"] is str
        assert info["is_optional"]
        assert info["is_union"]
        assert type(None) in info["union_types"]

    def test_union_type(self):
        """Test Union type with multiple types."""
        info = _get_python_type_info(Union[str, int])
        assert info["base_type"] is str  # First type as base
        assert not info["is_optional"]
        assert info["is_union"]
        assert str in info["union_types"]
        assert int in info["union_types"]

    def test_union_with_none(self):
        """Test Union with None (equivalent to Optional)."""
        info = _get_python_type_info(Union[str, None])
        assert info["base_type"] is str
        assert info["is_optional"]
        assert info["is_union"]


class TestSpecialPydanticTypes:
    """Test _is_special_pydantic_type function."""

    def test_non_pydantic_type(self):
        """Test with regular Python type."""
        result = _is_special_pydantic_type(str)
        # Should return False regardless of PYDANTIC_TYPES_AVAILABLE
        assert not result

    def test_optional_type(self):
        """Test with Optional type."""
        result = _is_special_pydantic_type(Optional[str])
        assert not result

    @pytest.mark.skipif(
        not PYDANTIC_TYPES_AVAILABLE, reason="Pydantic types not available"
    )
    def test_email_str_type(self):
        """Test with EmailStr type."""
        from pydantic import EmailStr

        result = _is_special_pydantic_type(EmailStr)
        assert result

    @pytest.mark.skipif(
        not PYDANTIC_TYPES_AVAILABLE, reason="Pydantic types not available"
    )
    def test_optional_email_str(self):
        """Test with Optional EmailStr."""
        from pydantic import EmailStr

        result = _is_special_pydantic_type(Optional[EmailStr])
        assert result


class TestSQLModelPropertyInfo:
    """Test _get_sqlmodel_property_info function."""

    def test_property_with_setter(self):
        """Test property with setter."""
        info = _get_sqlmodel_property_info(MockSQLModelClass, "display_name")
        assert info["is_property"]
        assert not info["is_computed"]
        assert info["has_setter"]

    def test_property_without_setter(self):
        """Test property without setter."""
        info = _get_sqlmodel_property_info(MockSQLModelClass, "readonly_field")
        assert info["is_property"]
        assert not info["is_computed"]
        assert not info["has_setter"]

    def test_non_property(self):
        """Test regular field."""
        info = _get_sqlmodel_property_info(MockSQLModelClass, "name")
        assert not info["is_property"]
        assert not info["is_computed"]
        assert not info["has_setter"]

    def test_nonexistent_field(self):
        """Test nonexistent field."""
        info = _get_sqlmodel_property_info(MockSQLModelClass, "nonexistent")
        assert not info["is_property"]
        assert not info["is_computed"]
        assert not info["has_setter"]


class TestGetModelFields:
    """Test get_model_fields function."""

    def test_sqlmodel_fields(self):
        """Test getting fields from SQLModel."""
        fields = get_model_fields(MockSQLModelClass)
        field_names = [f.name for f in fields]

        assert "id" in field_names
        assert "name" in field_names
        assert "email" in field_names
        assert "active" in field_names
        assert "display_name" in field_names
        assert "readonly_field" in field_names

    def test_field_properties(self):
        """Test field properties are correctly set."""
        fields = get_model_fields(MockSQLModelClass)
        field_dict = {f.name: f for f in fields}

        # Check primary key
        assert field_dict["id"].primary_key
        assert not field_dict["name"].primary_key

        # Check properties
        assert field_dict["display_name"].is_property
        assert field_dict["display_name"].has_setter
        assert field_dict["readonly_field"].is_property
        assert not field_dict["readonly_field"].has_setter

    def test_non_sqlmodel_class(self):
        """Test with non-SQLModel class."""
        fields = get_model_fields(str)  # Regular Python class
        assert fields == []


class TestGetWTFormCompatibleFields:
    """Test get_wtform_compatible_fields function."""

    def test_wtform_compatible(self):
        """Test getting WTForm compatible fields."""
        fields = get_wtform_compatible_fields(MockSQLModelClass)
        field_names = [f.name for f in fields]

        # Regular fields should be included
        assert "id" in field_names
        assert "name" in field_names
        assert "email" in field_names
        assert "active" in field_names

        # Property with setter should be included
        assert "display_name" in field_names

        # Property without setter should be excluded
        assert "readonly_field" not in field_names


class TestGetReadonlyFields:
    """Test get_readonly_fields function."""

    def test_readonly_fields(self):
        """Test getting readonly fields."""
        fields = get_readonly_fields(MockSQLModelClass)
        field_names = [f.name for f in fields]

        # Only readonly property should be included
        assert "readonly_field" in field_names
        assert "display_name" not in field_names  # Has setter
        assert "name" not in field_names  # Regular field


class TestFilterForeignColumns:
    """Test filter_foreign_columns function."""

    def test_filter_columns(self):
        """Test filtering columns by table."""
        # Mock table and columns
        mock_table = Mock()
        mock_table.name = "test_table"

        mock_col1 = Mock()
        mock_col1.table = mock_table

        mock_col2 = Mock()
        mock_col2.table = Mock()  # Different table

        columns = [mock_col1, mock_col2]
        result = filter_foreign_columns(mock_table, columns)

        assert len(result) == 1
        assert result[0] == mock_col1


class TestIsSQLModelClass:
    """Test is_sqlmodel_class function."""

    def test_sqlmodel_class(self):
        """Test with SQLModel class."""
        if SQLMODEL_AVAILABLE:
            assert is_sqlmodel_class(MockSQLModelClass)
        else:
            assert not is_sqlmodel_class(MockSQLModelClass)

    def test_regular_class(self):
        """Test with regular class."""
        assert not is_sqlmodel_class(str)
        assert not is_sqlmodel_class(MockSQLAlchemyModelClass)

    def test_instance_vs_class(self):
        """Test with instance vs class."""
        if SQLMODEL_AVAILABLE:
            instance = MockSQLModelClass(id=1, name="test")
            assert not is_sqlmodel_class(instance)  # Instance, not class
            assert is_sqlmodel_class(MockSQLModelClass)  # Class


class TestTupleOperatorIn:
    """Test tuple_operator_in function."""

    def test_single_tuple(self):
        """Test with single tuple."""
        from sqlalchemy import Column
        from sqlalchemy import Integer

        mock_col1 = Column("col1", Integer)
        mock_col2 = Column("col2", Integer)
        model_pk = [mock_col1, mock_col2]
        ids = [(1, 2)]

        result = tuple_operator_in(model_pk, ids)
        assert result is not None

    def test_multiple_tuples(self):
        """Test with multiple tuples."""
        from sqlalchemy import Column
        from sqlalchemy import Integer

        mock_col1 = Column("col1", Integer)
        mock_col2 = Column("col2", Integer)
        model_pk = [mock_col1, mock_col2]
        ids = [(1, 2), (3, 4)]

        result = tuple_operator_in(model_pk, ids)
        assert result is not None

    def test_empty_ids(self):
        """Test with empty ids list."""
        from sqlalchemy import Column
        from sqlalchemy import Integer

        mock_col1 = Column("col1", Integer)
        model_pk = [mock_col1]
        ids = []

        result = tuple_operator_in(model_pk, ids)
        assert result is None


class TestUtilityFunctions:
    """Test various utility functions."""

    def test_create_property_setter(self):
        """Test create_property_setter function."""
        setter = create_property_setter(MockSQLModelClass, "test_field")

        assert callable(setter)
        assert setter.__name__ == "set_test_field"

        # Test the setter
        instance = MockSQLModelClass(id=1, name="test")
        setter(instance, "test_value")
        assert hasattr(instance, "_wtf_test_field")
        assert instance._wtf_test_field == "test_value" # type: ignore


    def test_make_computed_field_wtforms_compatible(self):
        """Test make_computed_field_wtforms_compatible function."""
        if SQLMODEL_AVAILABLE:
            # Create a test class
            class TestModel(SQLModel):
                name: str

            make_computed_field_wtforms_compatible(TestModel, "computed_field")
            assert hasattr(TestModel, "set_computed_field")

    def test_get_field_value_with_fallback(self):
        """Test get_field_value_with_fallback function."""
        instance = MockSQLModelClass(id=1, name="test")

        # Test getting actual field value
        result = get_field_value_with_fallback(instance, "name")
        assert result == "test"

        # Test fallback to private storage
        instance._wtf_custom_field = "fallback_value"
        result = get_field_value_with_fallback(instance, "custom_field")
        assert result == "fallback_value"

        # Test default value
        result = get_field_value_with_fallback(instance, "nonexistent", "default")
        assert result == "default"

    def test_set_field_value_with_fallback(self):
        """Test set_field_value_with_fallback function."""
        instance = MockSQLModelClass(id=1, name="test")

        # Test direct assignment
        set_field_value_with_fallback(instance, "name", "new_name")
        assert instance.name == "new_name"

        # Test fallback to private storage
        set_field_value_with_fallback(instance, "custom_field", "custom_value")
        assert instance._wtf_custom_field == "custom_value" # type: ignore

    def test_debug_model_fields(self):
        """Test debug_model_fields function."""
        debug_str = debug_model_fields(MockSQLModelClass)

        assert "Model: MockSQLModelClass" in debug_str
        assert "Is SQLModel:" in debug_str
        assert "Has table:" in debug_str
        assert "Fields:" in debug_str
        assert "id:" in debug_str
        assert "name:" in debug_str

    def test_get_model_field_summary(self):
        """Test get_model_field_summary function."""
        summary = get_model_field_summary(MockSQLModelClass)

        assert isinstance(summary, dict)
        assert "id" in summary
        assert "name" in summary
        assert "display_name" in summary
        assert "readonly_field" in summary

        # Check field properties
        assert summary["id"]["primary_key"]
        assert summary["display_name"]["is_property"]
        assert summary["display_name"]["has_setter"]
        assert summary["readonly_field"]["readonly"]


class TestFieldValidation:
    """Test field validation functions."""

    def test_get_field_python_type(self):
        """Test get_field_python_type function."""
        field = ModelField(
            name="test",
            type_=str,
            default=None,
            required=True,
            primary_key=False,
            description=None,
            source=None,
        )

        result = get_field_python_type(field)
        assert result is str

    def test_is_field_optional(self):
        """Test is_field_optional function."""
        required_field = ModelField(
            name="required",
            type_=str,
            default=None,
            required=True,
            primary_key=False,
            description=None,
            source=None,
        )

        optional_field = ModelField(
            name="optional",
            type_=Optional[str],
            default=None,
            required=False,
            primary_key=False,
            description=None,
            source=None,
        )

        assert not is_field_optional(required_field)
        assert is_field_optional(optional_field)

    def test_validate_field_type(self):
        """Test validate_field_type function."""
        field = ModelField(
            name="test",
            type_=str,
            default=None,
            required=True,
            primary_key=False,
            description=None,
            source=None,
        )

        # Valid value
        is_valid, error = validate_field_type("test_string", field)
        assert is_valid
        assert error == ""

        # Invalid value
        is_valid, error = validate_field_type(123, field)
        assert not is_valid
        assert "must be of type str" in error

        # None value for required field
        is_valid, error = validate_field_type(None, field)
        assert not is_valid
        assert "is required" in error


class TestMockingAndEdgeCases:
    """Test edge cases and functions requiring mocking."""

    @patch("flask_admin.contrib.sqlmodel.tools.SQLMODEL_AVAILABLE", False)
    def test_functions_without_sqlmodel(self):
        """Test functions when SQLModel is not available."""
        assert not is_sqlmodel_class(MockSQLModelClass)

    @patch("flask_admin.contrib.sqlmodel.tools.PYDANTIC_TYPES_AVAILABLE", False)
    def test_functions_without_pydantic_types(self):
        """Test functions when Pydantic types are not available."""
        result = _is_special_pydantic_type(str)
        assert not result

    def test_resolve_model_with_orm_instance(self):
        """Test resolve_model with ORM instance."""
        instance = MockSQLModelClass(id=1, name="test")
        result = resolve_model(instance)
        assert result == instance

    def test_resolve_model_with_invalid_object(self):
        """Test resolve_model with invalid object."""
        with pytest.raises(TypeError):
            resolve_model("invalid_object")

    def test_get_columns_for_field_invalid(self):
        """Test get_columns_for_field with invalid field."""
        with pytest.raises(Exception, match="Invalid field"):
            get_columns_for_field(None)

    def test_get_field_constraints(self):
        """Test get_field_constraints function."""
        field = ModelField(
            name="test",
            type_=str,
            default=None,
            required=True,
            primary_key=False,
            description=None,
            source=Mock(),
        )

        # Mock source with constraints
        field.source.constraints = {"max_length": 50}

        constraints = get_field_constraints(field)
        assert "max_length" in constraints
        assert constraints["max_length"] == 50
