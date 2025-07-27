"""
Additional tests for SQLModel filters module to improve coverage.

This file targets specific uncovered areas in the filters module.
"""

import enum
from unittest.mock import Mock

from sqlmodel import Field
from sqlmodel import SQLModel

from flask_admin.contrib.sqlmodel.filters import BaseSQLModelFilter
from flask_admin.contrib.sqlmodel.filters import FilterConverter


# Test models and enums
class MockEnum(enum.Enum):
    VALUE1 = "value1"
    VALUE2 = "value2"


class FiltersTestModel(SQLModel, table=True):
    """Test model for filters testing."""

    id: int = Field(primary_key=True)
    name: str
    count: int
    price: float
    active: bool
    status: MockEnum


class TestImportFallbacks:
    """Test import fallbacks for SQLModel functions."""

    def test_sqlmodel_imports_available(self):
        """Test normal case when sqlmodel imports are available."""
        # This tests the try block succeeds normally
        from flask_admin.contrib.sqlmodel.filters import not_
        from flask_admin.contrib.sqlmodel.filters import or_

        # Should have imported successfully
        assert not_ is not None
        assert or_ is not None


class TestBaseSQLModelFilterComputed:
    """Test BaseSQLModelFilter computed field handling."""

    def test_convert_computed_field_known_pattern(self):
        """Test computed field conversion with known pattern."""
        # Create a mock property with specific function name
        mock_prop = Mock()
        mock_fget = Mock()
        mock_fget.__name__ = "number_of_pixels"
        mock_prop.fget = mock_fget

        filter_instance = BaseSQLModelFilter(column=Mock(), name="test")
        result = filter_instance._convert_computed_field_to_sql(mock_prop)

        # Should return tuple for known pattern
        assert result == ("computed_number_of_pixels", mock_prop)

    def test_convert_computed_field_unknown_pattern(self):
        """Test computed field conversion with unknown pattern."""
        # Create a mock property with unknown function name
        mock_prop = Mock()
        mock_fget = Mock()
        mock_fget.__name__ = "unknown_function"
        mock_prop.fget = mock_fget

        filter_instance = BaseSQLModelFilter(column=Mock(), name="test")
        result = filter_instance._convert_computed_field_to_sql(mock_prop)

        # Should return property as-is
        assert result == mock_prop

    def test_convert_computed_field_no_fget(self):
        """Test computed field conversion with no fget."""
        mock_prop = Mock()
        mock_prop.fget = None

        filter_instance = BaseSQLModelFilter(column=Mock(), name="test")
        result = filter_instance._convert_computed_field_to_sql(mock_prop)

        # Should return property as-is
        assert result == mock_prop

    def test_convert_computed_field_no_name(self):
        """Test computed field conversion with fget but no __name__."""
        mock_prop = Mock()
        mock_fget = Mock()
        del mock_fget.__name__  # Remove __name__ attribute
        mock_prop.fget = mock_fget

        filter_instance = BaseSQLModelFilter(column=Mock(), name="test")
        result = filter_instance._convert_computed_field_to_sql(mock_prop)

        # Should return property as-is
        assert result == mock_prop


class TestBaseSQLModelFilterGetColumn:
    """Test BaseSQLModelFilter.get_column method."""

    def test_get_column_computed_number_of_pixels(self):
        """Test get_column with computed number_of_pixels."""
        # Create filter with computed field tuple
        mock_prop = Mock()
        computed_column = ("computed_number_of_pixels", mock_prop)
        filter_instance = BaseSQLModelFilter(column=computed_column, name="test")

        # Mock alias with width and height attributes that can be multiplied
        mock_alias = Mock()
        mock_width = Mock()
        mock_height = Mock()
        mock_result = Mock()

        # Mock the multiplication operation
        mock_width.__mul__ = Mock(return_value=mock_result)
        mock_alias.width = mock_width
        mock_alias.height = mock_height

        result = filter_instance.get_column(mock_alias)

        # Should return width * height expression
        assert result == mock_result
        mock_width.__mul__.assert_called_once_with(mock_height)

    def test_get_column_with_key_no_alias(self):
        """Test get_column with column that has key, no alias."""
        mock_column = Mock()
        mock_column.key = "test_key"
        filter_instance = BaseSQLModelFilter(column=mock_column, name="test")

        result = filter_instance.get_column(None)

        assert result == mock_column

    def test_get_column_with_key_with_alias(self):
        """Test get_column with column that has key, with alias."""
        mock_column = Mock()
        mock_column.key = "test_key"
        filter_instance = BaseSQLModelFilter(column=mock_column, name="test")

        mock_alias = Mock()
        mock_alias.test_key = "aliased_column"

        result = filter_instance.get_column(mock_alias)

        assert result == "aliased_column"


class TestFilterConverterSQLTypes:
    """Test FilterConverter SQL type handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = FilterConverter()

    def test_convert_integer_types(self):
        """Test conversion of integer SQL types."""
        mock_column = Mock()
        mock_type = Mock()
        mock_type.__class__.__name__ = "Integer"
        mock_column.type = mock_type

        # Ensure the column doesn't look like a relationship
        del mock_column.property

        # Mock conv_int method
        self.converter.conv_int = Mock(return_value=["int_filter"])

        result = self.converter.convert("sqltype", mock_column, "test_name")

        self.converter.conv_int.assert_called_once()
        assert result == ["int_filter"]

    def test_convert_biginteger_type(self):
        """Test conversion of BIGINTEGER SQL type."""
        mock_column = Mock()
        mock_type = Mock()
        mock_type.__class__.__name__ = "BigInteger"
        mock_column.type = mock_type

        # Ensure the column doesn't look like a relationship
        del mock_column.property

        self.converter.conv_int = Mock(return_value=["int_filter"])

        _result = self.converter.convert("sqltype", mock_column, "test_name")

        self.converter.conv_int.assert_called_once()

    def test_convert_smallinteger_type(self):
        """Test conversion of SMALLINTEGER SQL type."""
        mock_column = Mock()
        mock_type = Mock()
        mock_type.__class__.__name__ = "SmallInteger"
        mock_column.type = mock_type

        # Ensure the column doesn't look like a relationship
        del mock_column.property

        self.converter.conv_int = Mock(return_value=["int_filter"])

        _result = self.converter.convert("sqltype", mock_column, "test_name")

        self.converter.conv_int.assert_called_once()

    def test_convert_float_types(self):
        """Test conversion of float SQL types."""
        for sql_type in ["Float", "Numeric", "Decimal"]:
            mock_column = Mock()
            mock_type = Mock()
            mock_type.__class__.__name__ = sql_type
            mock_column.type = mock_type

            # Ensure the column doesn't look like a relationship
            del mock_column.property

            self.converter.conv_float = Mock(return_value=["float_filter"])

            _result = self.converter.convert("sqltype", mock_column, "test_name")

            self.converter.conv_float.assert_called_once()

    def test_convert_boolean_type(self):
        """Test conversion of BOOLEAN SQL type."""
        mock_column = Mock()
        mock_type = Mock()
        mock_type.__class__.__name__ = "Boolean"
        mock_column.type = mock_type

        # Ensure the column doesn't look like a relationship
        del mock_column.property

        self.converter.conv_bool = Mock(return_value=["bool_filter"])

        _result = self.converter.convert("sqltype", mock_column, "test_name")

        self.converter.conv_bool.assert_called_once()

    def test_convert_date_type(self):
        """Test conversion of DATE SQL type."""
        mock_column = Mock()
        mock_type = Mock()
        mock_type.__class__.__name__ = "Date"
        mock_column.type = mock_type

        # Ensure the column doesn't look like a relationship
        del mock_column.property

        self.converter.conv_date = Mock(return_value=["date_filter"])

        _result = self.converter.convert("sqltype", mock_column, "test_name")

        self.converter.conv_date.assert_called_once()

    def test_convert_datetime_types(self):
        """Test conversion of datetime SQL types."""
        for sql_type in ["DateTime", "Timestamp"]:
            mock_column = Mock()
            mock_type = Mock()
            mock_type.__class__.__name__ = sql_type
            mock_column.type = mock_type

            # Ensure the column doesn't look like a relationship
            del mock_column.property

            self.converter.conv_datetime = Mock(return_value=["datetime_filter"])

            _result = self.converter.convert("sqltype", mock_column, "test_name")

            self.converter.conv_datetime.assert_called_once()

    def test_convert_time_type(self):
        """Test conversion of TIME SQL type."""
        mock_column = Mock()
        mock_type = Mock()
        mock_type.__class__.__name__ = "Time"
        mock_column.type = mock_type

        # Ensure the column doesn't look like a relationship
        del mock_column.property

        self.converter.conv_time = Mock(return_value=["time_filter"])

        _result = self.converter.convert("sqltype", mock_column, "test_name")

        self.converter.conv_time.assert_called_once()

    def test_convert_uuid_type(self):
        """Test conversion of UUID SQL type."""
        mock_column = Mock()
        mock_type = Mock()
        mock_type.__class__.__name__ = "UUID"
        mock_column.type = mock_type

        # Ensure the column doesn't look like a relationship
        del mock_column.property

        self.converter.conv_uuid = Mock(return_value=["uuid_filter"])

        _result = self.converter.convert("sqltype", mock_column, "test_name")

        self.converter.conv_uuid.assert_called_once()

    def test_convert_unknown_type_defaults_to_string(self):
        """Test conversion of unknown SQL type defaults to string."""
        mock_column = Mock()
        mock_type = Mock()
        mock_type.__class__.__name__ = "UnknownType"
        mock_column.type = mock_type

        # Ensure the column doesn't look like a relationship
        del mock_column.property

        self.converter.conv_string = Mock(return_value=["string_filter"])

        _result = self.converter.convert("sqltype", mock_column, "test_name")

        self.converter.conv_string.assert_called_once()

    def test_convert_no_type_returns_none(self):
        """Test conversion when no type can be determined."""
        mock_column = Mock()
        mock_column.type = None

        result = self.converter.convert("sqltype", mock_column, "test_name")

        assert result is None


class TestFilterConverterSQLAlchemyUtils:
    """Test FilterConverter SQLAlchemy-utils type converters."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = FilterConverter()

    def test_conv_sqla_utils_choice(self):
        """Test SQLAlchemy-utils ChoiceType converter."""
        mock_column = Mock()

        # Mock the choice_type_filters
        mock_filter1 = Mock(return_value="choice_filter1")
        mock_filter2 = Mock(return_value="choice_filter2")
        self.converter.choice_type_filters = [mock_filter1, mock_filter2]

        result = self.converter.conv_sqla_utils_choice(mock_column, "test_name")

        assert result == ["choice_filter1", "choice_filter2"]
        mock_filter1.assert_called_once_with(mock_column, "test_name")
        mock_filter2.assert_called_once_with(mock_column, "test_name")

    def test_conv_sqla_utils_arrow(self):
        """Test SQLAlchemy-utils ArrowType converter."""
        mock_column = Mock()

        # Mock the arrow_type_filters
        mock_filter1 = Mock(return_value="arrow_filter1")
        mock_filter2 = Mock(return_value="arrow_filter2")
        self.converter.arrow_type_filters = [mock_filter1, mock_filter2]

        result = self.converter.conv_sqla_utils_arrow(mock_column, "test_name")

        assert result == ["arrow_filter1", "arrow_filter2"]
        mock_filter1.assert_called_once_with(mock_column, "test_name")
        mock_filter2.assert_called_once_with(mock_column, "test_name")

    def test_conv_time_filters(self):
        """Test time filters converter."""
        mock_column = Mock()

        # Mock the time_filters
        mock_filter1 = Mock(return_value="time_filter1")
        mock_filter2 = Mock(return_value="time_filter2")
        self.converter.time_filters = [mock_filter1, mock_filter2]

        result = self.converter.conv_time(mock_column, "test_name")

        assert result == ["time_filter1", "time_filter2"]
        mock_filter1.assert_called_once_with(mock_column, "test_name")
        mock_filter2.assert_called_once_with(mock_column, "test_name")

    def test_conv_uuid_filters(self):
        """Test UUID filters converter."""
        mock_column = Mock()

        # Mock the uuid_filters
        mock_filter1 = Mock(return_value="uuid_filter1")
        mock_filter2 = Mock(return_value="uuid_filter2")
        self.converter.uuid_filters = [mock_filter1, mock_filter2]

        result = self.converter.conv_uuid(mock_column, "test_name")

        assert result == ["uuid_filter1", "uuid_filter2"]
        mock_filter1.assert_called_once_with(mock_column, "test_name")
        mock_filter2.assert_called_once_with(mock_column, "test_name")


class TestFilterConverterEnum:
    """Test FilterConverter enum handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = FilterConverter()

    def test_conv_enum_with_options(self):
        """Test enum converter with provided options."""
        mock_column = Mock()
        options = [("opt1", "Option 1"), ("opt2", "Option 2")]

        # Mock the enum filters
        mock_filter1 = Mock(return_value="enum_filter1")
        mock_filter2 = Mock(return_value="enum_filter2")
        self.converter.enum = [mock_filter1, mock_filter2]

        result = self.converter.conv_enum(mock_column, "test_name", options=options)

        assert result == ["enum_filter1", "enum_filter2"]
        mock_filter1.assert_called_once_with(mock_column, "test_name", options)
        mock_filter2.assert_called_once_with(mock_column, "test_name", options)

    def test_conv_enum_without_options(self):
        """Test enum converter without provided options (generates from type)."""
        mock_column = Mock()
        mock_type = Mock()
        mock_type.enums = ["value1", "value2", "value3"]
        mock_column.type = mock_type

        # Mock the enum filters
        mock_filter1 = Mock(return_value="enum_filter1")
        self.converter.enum = [mock_filter1]

        _result = self.converter.conv_enum(mock_column, "test_name")

        expected_options = [
            ("value1", "value1"),
            ("value2", "value2"),
            ("value3", "value3"),
        ]
        mock_filter1.assert_called_once_with(mock_column, "test_name", expected_options)


class TestFilterConverterApplyMethod:
    """Test FilterConverter functionality with filter application."""

    def test_convert_creates_applicable_filters(self):
        """Test that convert method creates filters that can be applied."""
        converter = FilterConverter()

        # Create mock column
        mock_column = Mock()
        mock_type = Mock()
        mock_type.__class__.__name__ = "String"
        mock_column.type = mock_type

        # Ensure the column doesn't look like a relationship
        del mock_column.property

        # Test conversion
        result = converter.convert("test_type", mock_column, "test_name")

        # Should return a list of filter instances
        assert isinstance(result, list)
        assert len(result) > 0

        # Each filter should be a filter instance with apply method
        for filter_instance in result:
            assert hasattr(filter_instance, "apply")
            assert hasattr(filter_instance, "operation")


class TestFilteredConverterEdgeCases:
    """Test edge cases and error conditions."""

    def test_converter_with_invalid_column(self):
        """Test converter behavior with invalid column."""
        converter = FilterConverter()

        # Test with None column
        result = converter.convert("test_type", None, "test_name")
        assert result is None

        # Test with column that has no type attribute
        mock_column = Mock()
        del mock_column.type

        result = converter.convert("test_type", mock_column, "test_name")
        assert result is None

    def test_converter_with_column_type_no_get_col_spec(self):
        """Test converter with column type that has no get_col_spec method."""
        converter = FilterConverter()

        mock_column = Mock()
        mock_type = Mock()
        del mock_type.get_col_spec  # Remove get_col_spec method
        mock_column.type = mock_type

        result = converter.convert("test_type", mock_column, "test_name")
        assert result is None


class TestFilterConverterStringTypes:
    """Test FilterConverter string type handling."""

    def test_convert_string_types(self):
        """Test conversion of various string SQL types."""
        converter = FilterConverter()

        string_types = ["String", "Text", "Varchar"]

        for sql_type in string_types:
            mock_column = Mock()
            mock_type = Mock()
            mock_type.__class__.__name__ = sql_type
            mock_column.type = mock_type

            # Ensure the column doesn't look like a relationship
            del mock_column.property

            converter.conv_string = Mock(return_value=["string_filter"])

            result = converter.convert("test_type", mock_column, "test_name")

            converter.conv_string.assert_called_once()
            assert result == ["string_filter"]


class TestFilterConverterSpecialCases:
    """Test FilterConverter special cases and edge conditions."""

    def test_get_column_without_computed_field(self):
        """Test get_column with regular column."""
        mock_column = Mock()
        # Remove the key attribute to test different code path
        del mock_column.key

        filter_instance = BaseSQLModelFilter(column=mock_column, name="test")
        result = filter_instance.get_column(None)

        # Should return the column itself
        assert result == mock_column

    def test_convert_computed_field_with_hasattr_failure(self):
        """Test computed field conversion when hasattr fails."""
        # Create a mock property that raises when accessing __name__
        mock_prop = Mock()
        mock_fget = Mock()

        # Use a side effect that raises AttributeError
        def side_effect(name):
            if name == "__name__":
                raise AttributeError("No __name__")
            return getattr(mock_fget, name)

        mock_fget.__getattribute__ = side_effect
        mock_prop.fget = mock_fget

        filter_instance = BaseSQLModelFilter(column=Mock(), name="test")
        result = filter_instance._convert_computed_field_to_sql(mock_prop)

        # Should return property as-is when hasattr fails
        assert result == mock_prop

    def test_convert_fallback_behavior(self):
        """Test conversion fallback behavior for edge cases."""
        converter = FilterConverter()

        # Test with column that has type but get_col_spec raises exception
        mock_column = Mock()
        mock_type = Mock()
        mock_type.get_col_spec.side_effect = Exception("Error getting spec")
        mock_column.type = mock_type

        result = converter.convert("test_type", mock_column, "test_name")

        # Should return None when get_col_spec fails
        assert result is None
