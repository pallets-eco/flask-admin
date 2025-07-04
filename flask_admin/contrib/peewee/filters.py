import typing as t

from flask_admin.babel import lazy_gettext
from flask_admin.model import filters

from ..._types import T_OPTIONS
from ..._types import T_TRANSLATABLE
from ..._types import T_WIDGET_TYPE
from .tools import parse_like_term


class BasePeeweeFilter(filters.BaseFilter):
    """
    Base Peewee filter.
    """

    def __init__(
        self,
        column: t.Any,
        name: str,
        options: T_OPTIONS = None,
        data_type: T_WIDGET_TYPE = None,
    ):
        """
        Constructor.

        :param column:
            Model field
        :param name:
            Display name
        :param options:
            Fixed set of options
        :param data_type:
            Client data type
        """
        super().__init__(name, options, data_type)

        self.column = column


# Common filters
class FilterEqual(BasePeeweeFilter):
    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        return query.filter(self.column == value)

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("equals")


class FilterNotEqual(BasePeeweeFilter):
    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        return query.filter(self.column != value)

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("not equal")


class FilterLike(BasePeeweeFilter):
    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        term = parse_like_term(value)
        return query.filter(self.column**term)

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("contains")


class FilterNotLike(BasePeeweeFilter):
    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        term = parse_like_term(value)
        return query.filter(~(self.column**term))

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("not contains")


class FilterGreater(BasePeeweeFilter):
    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        return query.filter(self.column > value)

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("greater than")


class FilterSmaller(BasePeeweeFilter):
    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        return query.filter(self.column < value)

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("smaller than")


class FilterEmpty(BasePeeweeFilter, filters.BaseBooleanFilter):
    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        if value == "1":
            return query.filter(self.column >> None)
        else:
            return query.filter(~(self.column >> None))

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("empty")


class FilterInList(BasePeeweeFilter):
    def __init__(
        self,
        column: t.Any,
        name: str,
        options: T_OPTIONS = None,
        data_type: T_WIDGET_TYPE = None,
    ) -> None:
        super().__init__(column, name, options, data_type="select2-tags")

    def clean(self, value: str) -> list[str]:
        return [v.strip() for v in value.split(",") if v.strip()]

    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        return query.filter(self.column << (value or [None]))

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("in list")


class FilterNotInList(FilterInList):
    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        # NOT IN can exclude NULL values, so "or_ == None" needed to be added
        return query.filter(~(self.column << (value or [None])) | (self.column >> None))

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("not in list")


# Customized type filters
class BooleanEqualFilter(FilterEqual, filters.BaseBooleanFilter):
    def clean(self, value: t.Any) -> int:
        return int(value)


class BooleanNotEqualFilter(FilterNotEqual, filters.BaseBooleanFilter):
    def clean(self, value: t.Any) -> int:
        return int(value)


class IntEqualFilter(FilterEqual, filters.BaseIntFilter):
    pass


class IntNotEqualFilter(FilterNotEqual, filters.BaseIntFilter):
    pass


class IntGreaterFilter(FilterGreater, filters.BaseIntFilter):
    pass


class IntSmallerFilter(FilterSmaller, filters.BaseIntFilter):
    pass


class IntInListFilter(filters.BaseIntListFilter, FilterInList):  # type: ignore[misc]
    pass


class IntNotInListFilter(filters.BaseIntListFilter, FilterNotInList):  # type: ignore[misc]
    pass


class FloatEqualFilter(FilterEqual, filters.BaseFloatFilter):
    pass


class FloatNotEqualFilter(FilterNotEqual, filters.BaseFloatFilter):
    pass


class FloatGreaterFilter(FilterGreater, filters.BaseFloatFilter):
    pass


class FloatSmallerFilter(FilterSmaller, filters.BaseFloatFilter):
    pass


class FloatInListFilter(filters.BaseFloatListFilter, FilterInList):  # type: ignore[misc]
    pass


class FloatNotInListFilter(filters.BaseFloatListFilter, FilterNotInList):  # type: ignore[misc]
    pass


class DateEqualFilter(FilterEqual, filters.BaseDateFilter):
    pass


class DateNotEqualFilter(FilterNotEqual, filters.BaseDateFilter):
    pass


class DateGreaterFilter(FilterGreater, filters.BaseDateFilter):
    pass


class DateSmallerFilter(FilterSmaller, filters.BaseDateFilter):
    pass


class DateBetweenFilter(BasePeeweeFilter, filters.BaseDateBetweenFilter):
    def __init__(
        self,
        column: t.Any,
        name: str,
        options: T_OPTIONS = None,
        data_type: T_WIDGET_TYPE = None,
    ) -> None:
        super().__init__(column, name, options, data_type="daterangepicker")

    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        start, end = value
        return query.filter(self.column.between(start, end))


class DateNotBetweenFilter(DateBetweenFilter):
    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        start, end = value
        return query.filter(~(self.column.between(start, end)))

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("not between")


class DateTimeEqualFilter(FilterEqual, filters.BaseDateTimeFilter):
    pass


class DateTimeNotEqualFilter(FilterNotEqual, filters.BaseDateTimeFilter):
    pass


class DateTimeGreaterFilter(FilterGreater, filters.BaseDateTimeFilter):
    pass


class DateTimeSmallerFilter(FilterSmaller, filters.BaseDateTimeFilter):
    pass


class DateTimeBetweenFilter(BasePeeweeFilter, filters.BaseDateTimeBetweenFilter):
    def __init__(
        self,
        column: t.Any,
        name: str,
        options: T_OPTIONS = None,
        data_type: T_WIDGET_TYPE = None,
    ):
        super().__init__(column, name, options, data_type="datetimerangepicker")

    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        start, end = value
        return query.filter(self.column.between(start, end))


class DateTimeNotBetweenFilter(DateTimeBetweenFilter):
    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        start, end = value
        return query.filter(~(self.column.between(start, end)))

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("not between")


class TimeEqualFilter(FilterEqual, filters.BaseTimeFilter):
    pass


class TimeNotEqualFilter(FilterNotEqual, filters.BaseTimeFilter):
    pass


class TimeGreaterFilter(FilterGreater, filters.BaseTimeFilter):
    pass


class TimeSmallerFilter(FilterSmaller, filters.BaseTimeFilter):
    pass


class TimeBetweenFilter(BasePeeweeFilter, filters.BaseTimeBetweenFilter):
    def __init__(
        self,
        column: t.Any,
        name: str,
        options: T_OPTIONS = None,
        data_type: T_WIDGET_TYPE = None,
    ):
        super().__init__(column, name, options, data_type="timerangepicker")

    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        start, end = value
        return query.filter(self.column.between(start, end))


class TimeNotBetweenFilter(TimeBetweenFilter):
    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        start, end = value
        return query.filter(~(self.column.between(start, end)))

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("not between")


# Base peewee filter field converter
class FilterConverter(filters.BaseFilterConverter):
    strings = (
        FilterLike,
        FilterNotLike,
        FilterEqual,
        FilterNotEqual,
        FilterEmpty,
        FilterInList,
        FilterNotInList,
    )
    int_filters = (
        IntEqualFilter,
        IntNotEqualFilter,
        IntGreaterFilter,
        IntSmallerFilter,
        FilterEmpty,
        IntInListFilter,
        IntNotInListFilter,
    )
    float_filters = (
        FloatEqualFilter,
        FloatNotEqualFilter,
        FloatGreaterFilter,
        FloatSmallerFilter,
        FilterEmpty,
        FloatInListFilter,
        FloatNotInListFilter,
    )
    bool_filters = (BooleanEqualFilter, BooleanNotEqualFilter)
    date_filters = (
        DateEqualFilter,
        DateNotEqualFilter,
        DateGreaterFilter,
        DateSmallerFilter,
        DateBetweenFilter,
        DateNotBetweenFilter,
        FilterEmpty,
    )
    datetime_filters = (
        DateTimeEqualFilter,
        DateTimeNotEqualFilter,
        DateTimeGreaterFilter,
        DateTimeSmallerFilter,
        DateTimeBetweenFilter,
        DateTimeNotBetweenFilter,
        FilterEmpty,
    )
    time_filters = (
        TimeEqualFilter,
        TimeNotEqualFilter,
        TimeGreaterFilter,
        TimeSmallerFilter,
        TimeBetweenFilter,
        TimeNotBetweenFilter,
        FilterEmpty,
    )

    def convert(self, type_name: str, column: str, name: str) -> t.Any:
        filter_name = type_name.lower()

        if filter_name in self.converters:
            return self.converters[filter_name](column, name)

        return None

    @filters.convert("CharField", "TextField")
    def conv_string(self, column: t.Any, name: str) -> list[BasePeeweeFilter]:
        return [f(column, name) for f in self.strings]

    @filters.convert("BooleanField")
    def conv_bool(self, column: t.Any, name: str) -> list[BasePeeweeFilter]:
        return [f(column, name) for f in self.bool_filters]

    @filters.convert("IntegerField", "BigIntegerField", "PrimaryKeyField")
    def conv_int(self, column: t.Any, name: str) -> list[BasePeeweeFilter]:
        return [f(column, name) for f in self.int_filters]

    @filters.convert("DecimalField", "FloatField", "DoubleField")
    def conv_float(self, column: t.Any, name: str) -> list[BasePeeweeFilter]:
        return [f(column, name) for f in self.float_filters]

    @filters.convert("DateField")
    def conv_date(self, column: t.Any, name: str) -> list[BasePeeweeFilter]:
        return [f(column, name) for f in self.date_filters]

    @filters.convert("DateTimeField")
    def conv_datetime(self, column: t.Any, name: str) -> list[BasePeeweeFilter]:
        return [f(column, name) for f in self.datetime_filters]

    @filters.convert("TimeField")
    def conv_time(self, column: t.Any, name: str) -> list[BasePeeweeFilter]:
        return [f(column, name) for f in self.time_filters]
