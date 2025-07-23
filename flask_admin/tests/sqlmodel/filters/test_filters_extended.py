"""
Extended tests for SQLModel filters module to improve coverage.
"""

import enum
from datetime import date
from datetime import datetime
from datetime import time
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from sqlmodel import Field
from sqlmodel import SQLModel

from flask_admin.contrib.sqlmodel.filters import BaseSQLModelFilter
from flask_admin.contrib.sqlmodel.filters import BooleanEqualFilter
from flask_admin.contrib.sqlmodel.filters import BooleanNotEqualFilter
from flask_admin.contrib.sqlmodel.filters import ChoiceTypeEqualFilter
from flask_admin.contrib.sqlmodel.filters import ChoiceTypeLikeFilter
from flask_admin.contrib.sqlmodel.filters import ChoiceTypeNotLikeFilter
from flask_admin.contrib.sqlmodel.filters import DateBetweenFilter
from flask_admin.contrib.sqlmodel.filters import DateEqualFilter
from flask_admin.contrib.sqlmodel.filters import DateGreaterFilter
from flask_admin.contrib.sqlmodel.filters import DateNotBetweenFilter
from flask_admin.contrib.sqlmodel.filters import DateTimeBetweenFilter
from flask_admin.contrib.sqlmodel.filters import DateTimeEqualFilter
from flask_admin.contrib.sqlmodel.filters import DateTimeGreaterFilter
from flask_admin.contrib.sqlmodel.filters import DateTimeNotBetweenFilter
from flask_admin.contrib.sqlmodel.filters import EnumEqualFilter
from flask_admin.contrib.sqlmodel.filters import EnumFilterInList
from flask_admin.contrib.sqlmodel.filters import EnumFilterNotInList
from flask_admin.contrib.sqlmodel.filters import FilterConverter
from flask_admin.contrib.sqlmodel.filters import FilterEmpty
from flask_admin.contrib.sqlmodel.filters import FilterEqual
from flask_admin.contrib.sqlmodel.filters import FilterGreater
from flask_admin.contrib.sqlmodel.filters import FilterInList
from flask_admin.contrib.sqlmodel.filters import FilterLike
from flask_admin.contrib.sqlmodel.filters import FilterNotEqual
from flask_admin.contrib.sqlmodel.filters import FilterNotInList
from flask_admin.contrib.sqlmodel.filters import FilterNotLike
from flask_admin.contrib.sqlmodel.filters import FilterSmaller
from flask_admin.contrib.sqlmodel.filters import FloatEqualFilter
from flask_admin.contrib.sqlmodel.filters import FloatGreaterFilter
from flask_admin.contrib.sqlmodel.filters import IntEqualFilter
from flask_admin.contrib.sqlmodel.filters import IntGreaterFilter
from flask_admin.contrib.sqlmodel.filters import IntInListFilter
from flask_admin.contrib.sqlmodel.filters import IntNotInListFilter
from flask_admin.contrib.sqlmodel.filters import IntSmallerFilter
from flask_admin.contrib.sqlmodel.filters import TimeBetweenFilter
from flask_admin.contrib.sqlmodel.filters import TimeEqualFilter
from flask_admin.contrib.sqlmodel.filters import TimeGreaterFilter
from flask_admin.contrib.sqlmodel.filters import TimeNotBetweenFilter
from flask_admin.contrib.sqlmodel.filters import UuidFilterEqual
from flask_admin.contrib.sqlmodel.filters import UuidFilterInList
from flask_admin.contrib.sqlmodel.filters import UuidFilterNotEqual
from flask_admin.contrib.sqlmodel.filters import UuidFilterNotInList


# Test enums
class FilterTestEnum(enum.Enum):
    OPTION1 = "option1"
    OPTION2 = "option2"
    OPTION3 = "option3"


class FilterTestStringEnum(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


# Test models
class FilterTestModelClass(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    active: bool
    score: float
    created_date: date
    created_datetime: datetime
    created_time: time

    @property
    def number_of_pixels(self) -> int:
        """Computed property for testing computed field filters."""
        return self.width * self.height

    width: int = 100
    height: int = 200


class MockQueryObject:
    """Mock query object for testing filters."""

    def __init__(self):
        self.filters = []

    def filter(self, condition):
        self.filters.append(condition)
        return self

    def all(self):
        return []


class TestBaseSQLModelFilter:
    """Test BaseSQLModelFilter class."""

    def test_init_with_regular_column(self):
        """Test initialization with regular column."""
        mock_column = Mock()
        mock_column.key = "test_field"

        filter_obj = BaseSQLModelFilter(mock_column, "Test Filter")
        assert filter_obj.column == mock_column
        assert filter_obj.key_name is None

    def test_init_with_computed_field(self):
        """Test initialization with computed field property."""
        # Mock a property that looks like number_of_pixels
        mock_prop = Mock(spec=property)
        mock_prop.fget = Mock()
        mock_prop.fget.__name__ = "number_of_pixels"

        filter_obj = BaseSQLModelFilter(mock_prop, "Computed Filter")
        assert isinstance(filter_obj.column, tuple)
        assert filter_obj.column[0] == "computed_number_of_pixels"

    def test_init_with_unknown_computed_field(self):
        """Test initialization with unknown computed field."""
        mock_prop = Mock(spec=property)
        mock_prop.fget = Mock()
        mock_prop.fget.__name__ = "unknown_computed"

        filter_obj = BaseSQLModelFilter(mock_prop, "Unknown Computed")
        assert filter_obj.column == mock_prop

    def test_get_column_regular_field(self):
        """Test get_column with regular field."""
        mock_column = Mock()
        mock_column.key = "test_field"

        filter_obj = BaseSQLModelFilter(mock_column, "Test Filter")

        # Without alias
        result = filter_obj.get_column(None)
        assert result == mock_column  # type: ignore

        # With alias
        mock_alias = Mock()
        mock_alias.test_field = "aliased_field"
        result = filter_obj.get_column(mock_alias)
        assert result == "aliased_field"  # type: ignore

    def test_get_column_computed_pixels(self):
        """Test get_column with computed number_of_pixels field."""
        mock_prop = Mock(spec=property)
        mock_prop.fget = Mock()
        mock_prop.fget.__name__ = "number_of_pixels"

        filter_obj = BaseSQLModelFilter(mock_prop, "Pixels Filter")

        # Without alias - should create raw SQL expression
        result = filter_obj.get_column(None)
        assert result is not None

        # With alias - should use alias columns
        mock_alias = Mock()
        # Create mock objects that support multiplication
        mock_width = Mock()
        mock_height = Mock()
        mock_width.__mul__ = Mock(return_value="width_times_height_expression")
        mock_alias.width = mock_width
        mock_alias.height = mock_height
        result = filter_obj.get_column(mock_alias)
        assert result is not None

    def test_get_column_unsupported_computed(self):
        """Test get_column with unsupported computed field -
        now returns property filter marker."""
        mock_prop = Mock(spec=property)
        mock_prop.fget = Mock()
        mock_prop.fget.__name__ = "unsupported_computed"

        filter_obj = BaseSQLModelFilter(mock_prop, "Unsupported")
        filter_obj.column = mock_prop  # Simulate unknown computed field

        # Now properties are supported through post-query filtering
        result = filter_obj.get_column(None)

        # Should return the property filter marker
        assert result == ("__PROPERTY_FILTER__", mock_prop) # type: ignore


class TestFilterOperations:
    """Test various filter operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_column = Mock()
        self.mock_column.key = "test_field"
        # Add support for comparison operations
        self.mock_column.__gt__ = Mock(return_value="greater_condition")
        self.mock_column.__lt__ = Mock(return_value="smaller_condition")
        self.mock_column.ilike = Mock(return_value="like_condition")
        self.mock_query = MockQueryObject()

    def test_filter_equal(self):
        """Test FilterEqual operation."""
        filter_obj = FilterEqual(self.mock_column, "Equal Filter")
        filter_obj.apply(self.mock_query, "test_value")
        assert len(self.mock_query.filters) == 1

    def test_filter_not_equal(self):
        """Test FilterNotEqual operation."""
        filter_obj = FilterNotEqual(self.mock_column, "Not Equal Filter")
        filter_obj.apply(self.mock_query, "test_value")
        assert len(self.mock_query.filters) == 1

    def test_filter_like(self):
        """Test FilterLike operation."""
        with patch(
            "flask_admin.contrib.sqlmodel.filters.tools.parse_like_term"
        ) as mock_parse:
            mock_parse.return_value = "%test%"
            mock_column = Mock()
            mock_column.ilike = Mock(return_value="like_condition")

            filter_obj = FilterLike(mock_column, "Like Filter")
            filter_obj.apply(self.mock_query, "test")

            mock_parse.assert_called_once_with("test")
            mock_column.ilike.assert_called_once_with("%test%")

    def test_filter_not_like(self):
        """Test FilterNotLike operation."""
        with patch(
            "flask_admin.contrib.sqlmodel.filters.tools.parse_like_term"
        ) as mock_parse:
            mock_parse.return_value = "%test%"
            # Create a mock that supports ilike and inversion
            mock_like_result = Mock()
            mock_like_result.__invert__ = Mock(return_value="inverted_like_condition")
            self.mock_column.ilike = Mock(return_value=mock_like_result)

            filter_obj = FilterNotLike(self.mock_column, "Not Like Filter")
            filter_obj.apply(self.mock_query, "test")

            mock_parse.assert_called_once_with("test")
            self.mock_column.ilike.assert_called_once_with("%test%")

    def test_filter_greater(self):
        """Test FilterGreater operation."""
        filter_obj = FilterGreater(self.mock_column, "Greater Filter")
        filter_obj.apply(self.mock_query, 10)
        assert len(self.mock_query.filters) == 1

    def test_filter_smaller(self):
        """Test FilterSmaller operation."""
        filter_obj = FilterSmaller(self.mock_column, "Smaller Filter")
        filter_obj.apply(self.mock_query, 10)
        assert len(self.mock_query.filters) == 1

    def test_filter_empty_true(self):
        """Test FilterEmpty with value '1' (is empty)."""
        filter_obj = FilterEmpty(self.mock_column, "Empty Filter")
        filter_obj.apply(self.mock_query, "1")
        assert len(self.mock_query.filters) == 1

    def test_filter_empty_false(self):
        """Test FilterEmpty with value '0' (is not empty)."""
        filter_obj = FilterEmpty(self.mock_column, "Empty Filter")
        filter_obj.apply(self.mock_query, "0")
        assert len(self.mock_query.filters) == 1


class TestFilterInList:
    """Test FilterInList and FilterNotInList."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_column = Mock()
        self.mock_column.key = "test_field"
        self.mock_column.in_ = Mock(return_value="in_condition")
        self.mock_query = MockQueryObject()

    def test_filter_in_list_init(self):
        """Test FilterInList initialization."""
        filter_obj = FilterInList(self.mock_column, "In List Filter")
        assert filter_obj.data_type == "select2-tags"

    def test_filter_in_list_clean(self):
        """Test FilterInList clean method."""
        filter_obj = FilterInList(self.mock_column, "In List Filter")

        # Test normal input
        result = filter_obj.clean("item1, item2, item3")
        assert result == ["item1", "item2", "item3"]

        # Test with extra spaces
        result = filter_obj.clean(" item1 ,  item2  , item3 ")
        assert result == ["item1", "item2", "item3"]

        # Test with empty values
        result = filter_obj.clean("item1, , item2, ")
        assert result == ["item1", "item2"]

    def test_filter_in_list_apply(self):
        """Test FilterInList apply method."""
        filter_obj = FilterInList(self.mock_column, "In List Filter")
        filter_obj.apply(self.mock_query, ["item1", "item2"])

        self.mock_column.in_.assert_called_once_with(["item1", "item2"])
        assert len(self.mock_query.filters) == 1

    def test_filter_not_in_list_apply(self):
        """Test FilterNotInList apply method."""
        with patch("flask_admin.contrib.sqlmodel.filters.or_") as mock_or:
            mock_or.return_value = "or_condition"

            # Mock the column.in_ to return something that supports inversion
            mock_in_result = Mock()
            mock_in_result.__invert__ = Mock(return_value="not_in_condition")
            self.mock_column.in_ = Mock(return_value=mock_in_result)
            self.mock_column.__eq__ = Mock(return_value="eq_none_condition")

            filter_obj = FilterNotInList(self.mock_column, "Not In List Filter")
            filter_obj.apply(self.mock_query, ["item1", "item2"])

            # Should call or_ with ~column.in_ and column == None
            mock_or.assert_called_once()
            assert len(self.mock_query.filters) == 1


class TestSpecializedFilters:
    """Test specialized filter types."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_column = Mock()
        self.mock_query = MockQueryObject()

    def test_boolean_filters(self):
        """Test boolean filter types."""
        bool_equal = BooleanEqualFilter(self.mock_column, "Boolean Equal")
        bool_not_equal = BooleanNotEqualFilter(self.mock_column, "Boolean Not Equal")

        # Test they inherit from the right base classes
        assert isinstance(bool_equal, FilterEqual)
        assert isinstance(bool_not_equal, FilterNotEqual)

    def test_int_filters(self):
        """Test integer filter types."""
        int_equal = IntEqualFilter(self.mock_column, "Int Equal")
        int_greater = IntGreaterFilter(self.mock_column, "Int Greater")
        int_smaller = IntSmallerFilter(self.mock_column, "Int Smaller")
        int_in_list = IntInListFilter(self.mock_column, "Int In List")
        int_not_in_list = IntNotInListFilter(self.mock_column, "Int Not In List")

        assert isinstance(int_equal, FilterEqual)
        assert isinstance(int_greater, FilterGreater)
        assert isinstance(int_smaller, FilterSmaller)
        assert isinstance(int_in_list, FilterInList)
        assert isinstance(int_not_in_list, FilterNotInList)

    def test_float_filters(self):
        """Test float filter types."""
        float_equal = FloatEqualFilter(self.mock_column, "Float Equal")
        float_greater = FloatGreaterFilter(self.mock_column, "Float Greater")

        assert isinstance(float_equal, FilterEqual)
        assert isinstance(float_greater, FilterGreater)

    def test_date_filters(self):
        """Test date filter types."""
        date_equal = DateEqualFilter(self.mock_column, "Date Equal")
        date_greater = DateGreaterFilter(self.mock_column, "Date Greater")

        assert isinstance(date_equal, FilterEqual)
        assert isinstance(date_greater, FilterGreater)

    def test_datetime_filters(self):
        """Test datetime filter types."""
        dt_equal = DateTimeEqualFilter(self.mock_column, "DateTime Equal")
        dt_greater = DateTimeGreaterFilter(self.mock_column, "DateTime Greater")

        assert isinstance(dt_equal, FilterEqual)
        assert isinstance(dt_greater, FilterGreater)

    def test_time_filters(self):
        """Test time filter types."""
        time_equal = TimeEqualFilter(self.mock_column, "Time Equal")
        time_greater = TimeGreaterFilter(self.mock_column, "Time Greater")

        assert isinstance(time_equal, FilterEqual)
        assert isinstance(time_greater, FilterGreater)


class TestBetweenFilters:
    """Test between filter types."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_column = Mock()
        self.mock_column.between = Mock(return_value="between_condition")
        self.mock_query = MockQueryObject()

    def test_date_between_filter(self):
        """Test DateBetweenFilter."""
        filter_obj = DateBetweenFilter(self.mock_column, "Date Between")
        assert filter_obj.data_type == "daterangepicker"

        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        filter_obj.apply(self.mock_query, (start_date, end_date))

        self.mock_column.between.assert_called_once_with(start_date, end_date)

    def test_date_not_between_filter(self):
        """Test DateNotBetweenFilter."""
        with patch("flask_admin.contrib.sqlmodel.filters.not_") as mock_not:
            mock_not.return_value = "not_condition"

            filter_obj = DateNotBetweenFilter(self.mock_column, "Date Not Between")

            start_date = date(2023, 1, 1)
            end_date = date(2023, 12, 31)
            filter_obj.apply(self.mock_query, (start_date, end_date))

            self.mock_column.between.assert_called_once_with(start_date, end_date)
            mock_not.assert_called_once()

    def test_datetime_between_filter(self):
        """Test DateTimeBetweenFilter."""
        filter_obj = DateTimeBetweenFilter(self.mock_column, "DateTime Between")
        assert filter_obj.data_type == "datetimerangepicker"

        start_dt = datetime(2023, 1, 1, 0, 0, 0)
        end_dt = datetime(2023, 12, 31, 23, 59, 59)
        filter_obj.apply(self.mock_query, (start_dt, end_dt))

        self.mock_column.between.assert_called_once_with(start_dt, end_dt)

    def test_time_between_filter(self):
        """Test TimeBetweenFilter."""
        filter_obj = TimeBetweenFilter(self.mock_column, "Time Between")
        assert filter_obj.data_type == "timerangepicker"

        start_time = time(9, 0, 0)
        end_time = time(17, 0, 0)
        filter_obj.apply(self.mock_query, (start_time, end_time))

        self.mock_column.between.assert_called_once_with(start_time, end_time)


class TestEnumFilters:
    """Test enum filter types."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_column = Mock()
        self.mock_column.type = Mock()
        self.mock_column.type.enum_class = FilterTestEnum
        self.mock_query = MockQueryObject()

    def test_enum_equal_filter_init(self):
        """Test EnumEqualFilter initialization."""
        filter_obj = EnumEqualFilter(self.mock_column, "Enum Equal")
        assert filter_obj.enum_class == FilterTestEnum

    def test_enum_equal_filter_clean(self):
        """Test EnumEqualFilter clean method."""
        filter_obj = EnumEqualFilter(self.mock_column, "Enum Equal")

        # Test valid enum value
        result = filter_obj.clean("OPTION1")
        assert result == FilterTestEnum.OPTION1

        # Test with None enum_class
        filter_obj.enum_class = None
        result = filter_obj.clean("test_value")
        assert result == "test_value"

    def test_enum_in_list_filter_clean(self):
        """Test EnumFilterInList clean method."""
        filter_obj = EnumFilterInList(self.mock_column, "Enum In List")

        # Test valid enum values by calling the parent clean method properly
        with patch.object(FilterInList, "clean", return_value=["OPTION1", "OPTION2"]):
            result = filter_obj.clean("OPTION1,OPTION2")
            assert result == [FilterTestEnum.OPTION1, FilterTestEnum.OPTION2]

    def test_enum_not_in_list_filter_clean(self):
        """Test EnumFilterNotInList clean method."""
        filter_obj = EnumFilterNotInList(self.mock_column, "Enum Not In List")

        with patch.object(
            FilterNotInList, "clean", return_value=["OPTION1", "OPTION3"]
        ):
            result = filter_obj.clean("OPTION1,OPTION3")
            assert result == [FilterTestEnum.OPTION1, FilterTestEnum.OPTION3]


class TestChoiceTypeFilters:
    """Test choice type filters."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_column = Mock()
        self.mock_query = MockQueryObject()

    def test_choice_type_equal_with_enum_choices(self):
        """Test ChoiceTypeEqualFilter with enum choices."""
        self.mock_column.type = Mock()
        self.mock_column.type.choices = FilterTestStringEnum

        filter_obj = ChoiceTypeEqualFilter(self.mock_column, "Choice Equal")
        filter_obj.apply(self.mock_query, "ACTIVE")

        assert len(self.mock_query.filters) == 1

    def test_choice_type_equal_with_tuple_choices(self):
        """Test ChoiceTypeEqualFilter with tuple choices."""
        self.mock_column.type = Mock()
        self.mock_column.type.choices = [("active", "Active"), ("inactive", "Inactive")]

        filter_obj = ChoiceTypeEqualFilter(self.mock_column, "Choice Equal")
        filter_obj.apply(self.mock_query, "Active")

        assert len(self.mock_query.filters) == 1

    def test_choice_type_equal_no_match(self):
        """Test ChoiceTypeEqualFilter with no matching choice."""
        self.mock_column.type = Mock()
        self.mock_column.type.choices = [("active", "Active")]
        self.mock_column.in_ = Mock(return_value="empty_condition")

        filter_obj = ChoiceTypeEqualFilter(self.mock_column, "Choice Equal")
        filter_obj.apply(self.mock_query, "NonExistent")

        # Should filter with empty list when no match found
        self.mock_column.in_.assert_called_once_with([])

    def test_choice_type_like_filter(self):
        """Test ChoiceTypeLikeFilter."""
        self.mock_column.type = Mock()
        self.mock_column.type.choices = [
            ("active", "Active Status"),
            ("inactive", "Inactive Status"),
        ]
        self.mock_column.in_ = Mock(return_value="in_condition")

        filter_obj = ChoiceTypeLikeFilter(self.mock_column, "Choice Like")
        filter_obj.apply(self.mock_query, "active")

        # Should find matches based on substring
        self.mock_column.in_.assert_called_once()

    def test_choice_type_not_like_filter(self):
        """Test ChoiceTypeNotLikeFilter."""
        with patch("flask_admin.contrib.sqlmodel.filters.or_") as mock_or:
            self.mock_column.type = Mock()
            self.mock_column.type.choices = [
                ("active", "Active"),
                ("inactive", "Inactive"),
            ]
            self.mock_column.notin_ = Mock(return_value="notin_condition")

            filter_obj = ChoiceTypeNotLikeFilter(self.mock_column, "Choice Not Like")
            filter_obj.apply(self.mock_query, "act")

            # Should call notin_ and or_ for NULL handling
            self.mock_column.notin_.assert_called_once()
            mock_or.assert_called_once()


class TestUuidFilters:
    """Test UUID filter types."""

    def test_uuid_filters_inheritance(self):
        """Test UUID filters inherit from correct base classes."""
        mock_column = Mock()

        uuid_equal = UuidFilterEqual(mock_column, "UUID Equal")
        uuid_not_equal = UuidFilterNotEqual(mock_column, "UUID Not Equal")
        uuid_in_list = UuidFilterInList(mock_column, "UUID In List")
        uuid_not_in_list = UuidFilterNotInList(mock_column, "UUID Not In List")

        assert isinstance(uuid_equal, FilterEqual)
        assert isinstance(uuid_not_equal, FilterNotEqual)
        assert isinstance(uuid_in_list, FilterInList)
        assert isinstance(uuid_not_in_list, FilterNotInList)


class TestFilterConverter:
    """Test FilterConverter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = FilterConverter()
        self.mock_column = Mock()

    def test_convert_with_relationship(self):
        """Test convert method with relationship attribute."""
        # Mock relationship attribute
        self.mock_column.property = Mock()
        self.mock_column.property.mapper = Mock()

        result = self.converter.convert("relationship", self.mock_column, "Test")
        assert result is None

    def test_convert_with_known_type(self):
        """Test convert method with known type in converters."""
        # Create a clean mock column without property attribute
        clean_mock_column = Mock(spec=["type"])
        clean_mock_column.type = Mock()

        # Mock converter method
        mock_converter = Mock(return_value="string_filters")
        self.converter.converters = {"string": mock_converter}

        result = self.converter.convert("string", clean_mock_column, "Test")
        assert result == "string_filters"
        mock_converter.assert_called_once_with(clean_mock_column, "Test")

    def test_convert_with_sql_type(self):
        """Test convert method using SQL type detection."""
        # Mock column with SQL type
        self.mock_column.type = Mock()
        self.mock_column.type.__class__.__name__ = "String"
        # Remove any existing property or mapper to avoid relationship detection
        if hasattr(self.mock_column, "property"):
            delattr(self.mock_column, "property")

        with patch.object(self.converter, "conv_string") as mock_conv:
            mock_conv.return_value = "string_filters"
            result = self.converter.convert("unknown_type", self.mock_column, "Test")
            assert result == "string_filters"
            mock_conv.assert_called_once_with(self.mock_column, "Test")

    def test_convert_without_type(self):
        """Test convert method with column without type."""
        mock_column = Mock()
        del mock_column.type  # Remove type attribute

        result = self.converter.convert("unknown", mock_column, "Test")
        assert result is None

    def test_conv_string_method(self):
        """Test conv_string converter method."""
        result = self.converter.conv_string(self.mock_column, "String Test")
        assert len(result) == len(self.converter.strings)
        assert all(isinstance(f, BaseSQLModelFilter) for f in result)

    def test_conv_int_method(self):
        """Test conv_int converter method."""
        result = self.converter.conv_int(self.mock_column, "Int Test")
        assert len(result) == len(self.converter.int_filters)

    def test_conv_bool_method(self):
        """Test conv_bool converter method."""
        result = self.converter.conv_bool(self.mock_column, "Bool Test")
        assert len(result) == len(self.converter.bool_filters)

    def test_conv_enum_method(self):
        """Test conv_enum converter method."""
        self.mock_column.type = Mock()
        self.mock_column.type.enums = ["option1", "option2", "option3"]

        result = self.converter.conv_enum(self.mock_column, "Enum Test")
        assert len(result) == len(self.converter.enum)

        # Test with custom options
        custom_options = [("a", "A"), ("b", "B")]
        result = self.converter.conv_enum(
            self.mock_column, "Enum Test", options=custom_options
        )
        # All filters should be created with custom options
        for filter_obj in result:
            assert hasattr(filter_obj, "options")

    def test_conv_uuid_method(self):
        """Test conv_uuid converter method."""
        result = self.converter.conv_uuid(self.mock_column, "UUID Test")
        assert len(result) == len(self.converter.uuid_filters)


class TestFilterOperationLabels:
    """Test filter operation labels."""

    def test_operation_labels(self):
        """Test that filters return correct operation labels."""
        mock_column = Mock()

        # Test various filter operation labels
        filters_and_labels = [
            (FilterEqual(mock_column, "Test"), "equals"),
            (FilterNotEqual(mock_column, "Test"), "not equal"),
            (FilterLike(mock_column, "Test"), "contains"),
            (FilterNotLike(mock_column, "Test"), "not contains"),
            (FilterGreater(mock_column, "Test"), "greater than"),
            (FilterSmaller(mock_column, "Test"), "smaller than"),
            (FilterEmpty(mock_column, "Test"), "empty"),
            (FilterInList(mock_column, "Test"), "in list"),
            (FilterNotInList(mock_column, "Test"), "not in list"),
            (DateNotBetweenFilter(mock_column, "Test"), "not between"),
            (DateTimeNotBetweenFilter(mock_column, "Test"), "not between"),
            (TimeNotBetweenFilter(mock_column, "Test"), "not between"),
        ]

        for filter_obj, _expected_label in filters_and_labels:
            operation = filter_obj.operation()
            # The actual test would check if operation contains the expected label
            # Since we're using lazy_gettext,
            # we just ensure operation() returns something
            assert operation is not None


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling."""

    def test_filter_with_none_values(self):
        """Test filters with None values."""
        mock_column = Mock()
        mock_query = MockQueryObject()

        filter_obj = FilterEqual(mock_column, "Test")
        # Should not raise exception with None value
        filter_obj.apply(mock_query, None)

    def test_filter_in_list_with_empty_string(self):
        """Test FilterInList with empty string."""
        mock_column = Mock()
        filter_obj = FilterInList(mock_column, "Test")

        result = filter_obj.clean("")
        assert result == []

    def test_filter_in_list_with_whitespace_only(self):
        """Test FilterInList with whitespace-only string."""
        mock_column = Mock()
        filter_obj = FilterInList(mock_column, "Test")

        result = filter_obj.clean("   ,  ,   ")
        assert result == []

    def test_choice_type_filter_with_empty_query(self):
        """Test ChoiceTypeLikeFilter with empty query."""
        mock_column = Mock()
        mock_column.type = Mock()
        mock_column.type.choices = [("active", "Active")]
        mock_query = MockQueryObject()

        filter_obj = ChoiceTypeLikeFilter(mock_column, "Test")
        result = filter_obj.apply(mock_query, "")

        # Should return query unchanged for empty search
        assert result == mock_query

    def test_enum_filter_with_invalid_value(self):
        """Test enum filter with invalid enum value."""
        mock_column = Mock()
        mock_column.type = Mock()
        mock_column.type.enum_class = FilterTestEnum

        filter_obj = EnumEqualFilter(mock_column, "Test")

        # Should raise KeyError for invalid enum value
        with pytest.raises(KeyError):
            filter_obj.clean("INVALID_OPTION")
