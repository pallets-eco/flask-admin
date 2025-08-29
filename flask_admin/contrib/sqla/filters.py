import enum
import typing as t

from sqlalchemy.sql import not_
from sqlalchemy.sql import or_
from sqlalchemy.sql.schema import Column

from flask_admin._types import T_OPTIONS
from flask_admin._types import T_SQLALCHEMY_QUERY
from flask_admin._types import T_TRANSLATABLE
from flask_admin._types import T_WIDGET_TYPE
from flask_admin.babel import lazy_gettext
from flask_admin.contrib.sqla import tools
from flask_admin.model import filters


class BaseSQLAFilter(filters.BaseFilter):
    """
    Base SQLAlchemy filter.
    """

    def __init__(
        self,
        column: Column,
        name: str,
        options: T_OPTIONS = None,
        data_type: T_WIDGET_TYPE = None,
    ) -> None:
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

    def get_column(self, alias: t.Any) -> Column:
        return self.column if alias is None else getattr(alias, self.column.key)

    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        return super().apply(query, value)


# Common filters
class FilterEqual(BaseSQLAFilter):
    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        return query.filter(self.get_column(alias) == value)

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("equals")


class FilterNotEqual(BaseSQLAFilter):
    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        return query.filter(self.get_column(alias) != value)

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("not equal")


class FilterLike(BaseSQLAFilter):
    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        stmt = tools.parse_like_term(value)
        return query.filter(self.get_column(alias).ilike(stmt))

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("contains")


class FilterNotLike(BaseSQLAFilter):
    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        stmt = tools.parse_like_term(value)
        return query.filter(~self.get_column(alias).ilike(stmt))

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("not contains")


class FilterGreater(BaseSQLAFilter):
    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        return query.filter(self.get_column(alias) > value)

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("greater than")


class FilterSmaller(BaseSQLAFilter):
    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        return query.filter(self.get_column(alias) < value)

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("smaller than")


class FilterEmpty(BaseSQLAFilter, filters.BaseBooleanFilter):
    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        if value == "1":
            return query.filter(self.get_column(alias) == None)  # noqa: E711
        else:
            return query.filter(self.get_column(alias) != None)  # noqa: E711

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("empty")


class FilterInList(BaseSQLAFilter):
    def __init__(
        self,
        column: Column,
        name: str,
        options: T_OPTIONS = None,
        data_type: T_WIDGET_TYPE = None,
    ) -> None:
        super().__init__(column, name, options, data_type="select2-tags")

    def clean(self, value: str) -> list[str]:
        return [v.strip() for v in value.split(",") if v.strip()]

    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        return query.filter(self.get_column(alias).in_(value))

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("in list")


class FilterNotInList(FilterInList):
    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        # NOT IN can exclude NULL values, so "or_ == None" needed to be added
        column = self.get_column(alias)
        return query.filter(or_(~column.in_(value), column == None))  # noqa: E711

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("not in list")


# Customized type filters
class BooleanEqualFilter(FilterEqual, filters.BaseBooleanFilter):
    pass


class BooleanNotEqualFilter(FilterNotEqual, filters.BaseBooleanFilter):
    pass


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


class DateBetweenFilter(BaseSQLAFilter, filters.BaseDateBetweenFilter):
    def __init__(
        self,
        column: Column,
        name: str,
        options: T_OPTIONS = None,
        data_type: T_WIDGET_TYPE = None,
    ):
        super().__init__(column, name, options, data_type="daterangepicker")

    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        start, end = value
        return query.filter(self.get_column(alias).between(start, end))


class DateNotBetweenFilter(DateBetweenFilter):
    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        start, end = value
        return query.filter(not_(self.get_column(alias).between(start, end)))

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


class DateTimeBetweenFilter(BaseSQLAFilter, filters.BaseDateTimeBetweenFilter):
    def __init__(
        self,
        column: Column,
        name: str,
        options: T_OPTIONS = None,
        data_type: T_WIDGET_TYPE = None,
    ) -> None:
        super().__init__(column, name, options, data_type="datetimerangepicker")

    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        start, end = value
        return query.filter(self.get_column(alias).between(start, end))


class DateTimeNotBetweenFilter(DateTimeBetweenFilter):
    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        start, end = value
        return query.filter(not_(self.get_column(alias).between(start, end)))

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


class TimeBetweenFilter(BaseSQLAFilter, filters.BaseTimeBetweenFilter):
    def __init__(
        self,
        column: Column,
        name: str,
        options: T_OPTIONS = None,
        data_type: T_WIDGET_TYPE = None,
    ) -> None:
        super().__init__(column, name, options, data_type="timerangepicker")

    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        start, end = value
        return query.filter(self.get_column(alias).between(start, end))


class TimeNotBetweenFilter(TimeBetweenFilter):
    def apply(
        self, query: T_SQLALCHEMY_QUERY, value: t.Any, alias: t.Any = None
    ) -> t.Any:
        start, end = value
        return query.filter(not_(self.get_column(alias).between(start, end)))

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("not between")


class EnumEqualFilter(FilterEqual):
    def __init__(
        self, column: Column, name: str, options: T_OPTIONS = None, **kwargs: t.Any
    ) -> None:
        self.enum_class = column.type.enum_class  # type: ignore[attr-defined]
        super().__init__(column, name, options, **kwargs)

    def clean(self, value: t.Any) -> t.Any:
        if self.enum_class is None:
            return super().clean(value)
        return self.enum_class[value]


class EnumFilterNotEqual(FilterNotEqual):
    def __init__(
        self, column: Column, name: str, options: T_OPTIONS = None, **kwargs: t.Any
    ) -> None:
        self.enum_class = column.type.enum_class  # type: ignore[attr-defined]
        super().__init__(column, name, options, **kwargs)

    def clean(self, value: t.Any) -> t.Any:
        if self.enum_class is None:
            return super().clean(value)
        return self.enum_class[value]


class EnumFilterEmpty(FilterEmpty):
    def __init__(
        self, column: Column, name: str, options: T_OPTIONS = None, **kwargs: t.Any
    ) -> None:
        self.enum_class = column.type.enum_class  # type: ignore[attr-defined]
        super().__init__(column, name, options, **kwargs)


class EnumFilterInList(FilterInList):
    def __init__(
        self, column: Column, name: str, options: T_OPTIONS = None, **kwargs: t.Any
    ) -> None:
        self.enum_class = column.type.enum_class  # type: ignore[attr-defined]
        super().__init__(column, name, options, **kwargs)

    def clean(self, value: t.Any) -> t.Any:
        values = super().clean(value)
        if self.enum_class is not None:
            values = [
                v if isinstance(v, self.enum_class) else self.enum_class[v]
                for v in values
            ]
        return values


class EnumFilterNotInList(FilterNotInList):
    def __init__(
        self, column: Column, name: str, options: T_OPTIONS = None, **kwargs: t.Any
    ) -> None:
        self.enum_class = column.type.enum_class  # type: ignore[attr-defined]
        super().__init__(column, name, options, **kwargs)

    def clean(self, value: t.Any) -> t.Any:
        values = super().clean(value)
        if self.enum_class is not None:
            values = [
                v if isinstance(v, self.enum_class) else self.enum_class[v]
                for v in values
            ]
        return values


class ChoiceTypeEqualFilter(FilterEqual):
    def __init__(
        self, column: Column, name: str, options: T_OPTIONS = None, **kwargs: t.Any
    ) -> None:
        super().__init__(column, name, options, **kwargs)

    def apply(
        self, query: T_SQLALCHEMY_QUERY, user_query: str, alias: t.Any = None
    ) -> T_SQLALCHEMY_QUERY:
        column = self.get_column(alias)
        choice_type = None
        # loop through choice 'values' to try and find an exact match
        if isinstance(column.type.choices, enum.EnumMeta):  # type: ignore[attr-defined]
            for choice in column.type.choices:  # type: enum.Enum  # type: ignore[attr-defined]
                if choice.name == user_query:
                    choice_type = choice.value
                    break
        else:
            for type, value in column.type.choices:  # type: ignore[attr-defined]
                if value == user_query:
                    choice_type = type
                    break
        if choice_type:
            return query.filter(column == choice_type)
        else:
            return query.filter(column.in_([]))


class ChoiceTypeNotEqualFilter(FilterNotEqual):
    def __init__(
        self, column: Column, name: str, options: T_OPTIONS = None, **kwargs: t.Any
    ) -> None:
        super().__init__(column, name, options, **kwargs)

    def apply(
        self, query: T_SQLALCHEMY_QUERY, user_query: str, alias: t.Any = None
    ) -> T_SQLALCHEMY_QUERY:
        column = self.get_column(alias)
        choice_type = None
        # loop through choice 'values' to try and find an exact match
        if isinstance(column.type.choices, enum.EnumMeta):  # type: ignore[attr-defined]
            for choice in column.type.choices:  # type: enum.Enum # type: ignore[attr-defined]
                if choice.name == user_query:
                    choice_type = choice.value
                    break
        else:
            for type, value in column.type.choices:  # type: ignore[attr-defined]
                if value == user_query:
                    choice_type = type
                    break
        if choice_type:
            # != can exclude NULL values, so "or_ == None" needed to be added
            return query.filter(or_(column != choice_type, column == None))  # noqa: E711
        else:
            return query


class ChoiceTypeLikeFilter(FilterLike):
    def __init__(
        self, column: Column, name: str, options: T_OPTIONS = None, **kwargs: t.Any
    ) -> None:
        super().__init__(column, name, options, **kwargs)

    def apply(
        self, query: T_SQLALCHEMY_QUERY, user_query: str, alias: t.Any = None
    ) -> T_SQLALCHEMY_QUERY:
        column = self.get_column(alias)
        choice_types = []
        if user_query:
            # loop through choice 'values' looking for matches
            if isinstance(column.type.choices, enum.EnumMeta):  # type: ignore[attr-defined]
                for choice in column.type.choices:  # type: enum.Enum  # type: ignore[attr-defined]
                    if user_query.lower() in choice.name.lower():
                        choice_types.append(choice.value)
            else:
                for type, value in column.type.choices:  # type: ignore[attr-defined]
                    if user_query.lower() in value.lower():
                        choice_types.append(type)
        if choice_types:
            return query.filter(column.in_(choice_types))
        else:
            return query


class ChoiceTypeNotLikeFilter(FilterNotLike):
    def __init__(
        self, column: Column, name: str, options: T_OPTIONS = None, **kwargs: t.Any
    ) -> None:
        super().__init__(column, name, options, **kwargs)

    def apply(
        self, query: T_SQLALCHEMY_QUERY, user_query: str, alias: t.Any = None
    ) -> T_SQLALCHEMY_QUERY:
        column = self.get_column(alias)
        choice_types = []
        if user_query:
            # loop through choice 'values' looking for matches
            if isinstance(column.type.choices, enum.EnumMeta):  # type: ignore[attr-defined]
                for choice in column.type.choices:  # type: enum.Enum  # type: ignore[attr-defined]
                    if user_query.lower() in choice.name.lower():
                        choice_types.append(choice.value)
            else:
                for type, value in column.type.choices:  # type: ignore[attr-defined]
                    if user_query.lower() in value.lower():
                        choice_types.append(type)
        if choice_types:
            # != can exclude NULL values, so "or_ == None" needed to be added
            return query.filter(or_(column.notin_(choice_types), column == None))  # noqa: E711
        else:
            return query


class UuidFilterEqual(FilterEqual, filters.BaseUuidFilter):
    pass


class UuidFilterNotEqual(FilterNotEqual, filters.BaseUuidFilter):
    pass


class UuidFilterInList(filters.BaseUuidListFilter, FilterInList):
    pass


class UuidFilterNotInList(filters.BaseUuidListFilter, FilterNotInList):
    pass


# Base SQLA filter field converter
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
    string_key_filters = (
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
    enum = (
        EnumEqualFilter,
        EnumFilterNotEqual,
        EnumFilterEmpty,
        EnumFilterInList,
        EnumFilterNotInList,
    )
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
    choice_type_filters = (
        ChoiceTypeEqualFilter,
        ChoiceTypeNotEqualFilter,
        ChoiceTypeLikeFilter,
        ChoiceTypeNotLikeFilter,
        FilterEmpty,
    )
    uuid_filters = (
        UuidFilterEqual,
        UuidFilterNotEqual,
        FilterEmpty,
        UuidFilterInList,
        UuidFilterNotInList,
    )
    arrow_type_filters = (DateTimeGreaterFilter, DateTimeSmallerFilter, FilterEmpty)

    def convert(
        self, type_name: str, column: Column, name: str, **kwargs: t.Any
    ) -> t.Optional[list[BaseSQLAFilter]]:
        filter_name = type_name.lower()

        if filter_name in self.converters:
            return self.converters[filter_name](column, name, **kwargs)

        return None

    @filters.convert(
        "string",
        "char",
        "unicode",
        "varchar",
        "tinytext",
        "text",
        "mediumtext",
        "longtext",
        "unicodetext",
        "nchar",
        "nvarchar",
        "ntext",
        "citext",
        "emailtype",
        "URLType",
        "IPAddressType",
    )
    def conv_string(
        self, column: Column, name: str, **kwargs: t.Any
    ) -> list[BaseSQLAFilter]:
        return [f(column, name, **kwargs) for f in self.strings]

    @filters.convert("UUIDType", "ColorType", "TimezoneType", "CurrencyType")
    def conv_string_keys(
        self, column: Column, name: str, **kwargs: t.Any
    ) -> list[BaseSQLAFilter]:
        return [f(column, name, **kwargs) for f in self.string_key_filters]

    @filters.convert("boolean", "tinyint")
    def conv_bool(
        self, column: Column, name: str, **kwargs: t.Any
    ) -> list[BaseSQLAFilter]:
        return [f(column, name, **kwargs) for f in self.bool_filters]

    @filters.convert(
        "int",
        "integer",
        "smallinteger",
        "smallint",
        "biginteger",
        "bigint",
        "mediumint",
    )
    def conv_int(
        self, column: Column, name: str, **kwargs: t.Any
    ) -> list[BaseSQLAFilter]:
        return [f(column, name, **kwargs) for f in self.int_filters]

    @filters.convert(
        "float", "real", "decimal", "numeric", "double_precision", "double"
    )
    def conv_float(
        self, column: Column, name: str, **kwargs: t.Any
    ) -> list[BaseSQLAFilter]:
        return [f(column, name, **kwargs) for f in self.float_filters]

    @filters.convert("date")
    def conv_date(
        self, column: Column, name: str, **kwargs: t.Any
    ) -> list[BaseSQLAFilter]:
        return [f(column, name, **kwargs) for f in self.date_filters]

    @filters.convert("datetime", "datetime2", "timestamp", "smalldatetime")
    def conv_datetime(
        self, column: Column, name: str, **kwargs: t.Any
    ) -> list[BaseSQLAFilter]:
        return [f(column, name, **kwargs) for f in self.datetime_filters]

    @filters.convert("time")
    def conv_time(
        self, column: Column, name: str, **kwargs: t.Any
    ) -> list[BaseSQLAFilter]:
        return [f(column, name, **kwargs) for f in self.time_filters]

    @filters.convert("ChoiceType")
    def conv_sqla_utils_choice(
        self, column: Column, name: str, **kwargs: t.Any
    ) -> list[BaseSQLAFilter]:
        return [f(column, name, **kwargs) for f in self.choice_type_filters]

    @filters.convert("ArrowType")
    def conv_sqla_utils_arrow(
        self, column: Column, name: str, **kwargs: t.Any
    ) -> list[BaseSQLAFilter]:
        return [f(column, name, **kwargs) for f in self.arrow_type_filters]

    @filters.convert("enum")
    def conv_enum(
        self, column: Column, name: str, options: T_OPTIONS = None, **kwargs: t.Any
    ) -> list[BaseSQLAFilter]:
        if not options:
            options = [(v, v) for v in column.type.enums]  # type: ignore[attr-defined]

        return [f(column, name, options, **kwargs) for f in self.enum]

    @filters.convert("uuid")
    def conv_uuid(
        self, column: Column, name: str, **kwargs: t.Any
    ) -> list[BaseSQLAFilter]:
        return [f(column, name, **kwargs) for f in self.uuid_filters]
