import enum

from sqlalchemy.sql import not_
from sqlalchemy.sql import or_

from flask_admin.babel import lazy_gettext
from flask_admin.contrib.sqla import tools
from flask_admin.model import filters


class BaseSQLAFilter(filters.BaseFilter):
    """
    Base SQLAlchemy filter.
    """

    def __init__(self, column, name, options=None, data_type=None):
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

    def get_column(self, alias):
        return self.column if alias is None else getattr(alias, self.column.key)

    def apply(self, query, value, alias=None):
        return super().apply(query, value)


# Common filters
class FilterEqual(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.get_column(alias) == value)

    def operation(self):
        return lazy_gettext("equals")


class FilterNotEqual(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.get_column(alias) != value)

    def operation(self):
        return lazy_gettext("not equal")


class FilterLike(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        stmt = tools.parse_like_term(value)
        return query.filter(self.get_column(alias).ilike(stmt))

    def operation(self):
        return lazy_gettext("contains")


class FilterNotLike(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        stmt = tools.parse_like_term(value)
        return query.filter(~self.get_column(alias).ilike(stmt))

    def operation(self):
        return lazy_gettext("not contains")


class FilterGreater(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.get_column(alias) > value)

    def operation(self):
        return lazy_gettext("greater than")


class FilterSmaller(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.get_column(alias) < value)

    def operation(self):
        return lazy_gettext("smaller than")


class FilterEmpty(BaseSQLAFilter, filters.BaseBooleanFilter):
    def apply(self, query, value, alias=None):
        if value == "1":
            return query.filter(self.get_column(alias) == None)  # noqa: E711
        else:
            return query.filter(self.get_column(alias) != None)  # noqa: E711

    def operation(self):
        return lazy_gettext("empty")


class FilterInList(BaseSQLAFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super().__init__(column, name, options, data_type="select2-tags")

    def clean(self, value):
        return [v.strip() for v in value.split(",") if v.strip()]

    def apply(self, query, value, alias=None):
        return query.filter(self.get_column(alias).in_(value))

    def operation(self):
        return lazy_gettext("in list")


class FilterNotInList(FilterInList):
    def apply(self, query, value, alias=None):
        # NOT IN can exclude NULL values, so "or_ == None" needed to be added
        column = self.get_column(alias)
        return query.filter(or_(~column.in_(value), column == None))  # noqa: E711

    def operation(self):
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


class IntInListFilter(filters.BaseIntListFilter, FilterInList):
    pass


class IntNotInListFilter(filters.BaseIntListFilter, FilterNotInList):
    pass


class FloatEqualFilter(FilterEqual, filters.BaseFloatFilter):
    pass


class FloatNotEqualFilter(FilterNotEqual, filters.BaseFloatFilter):
    pass


class FloatGreaterFilter(FilterGreater, filters.BaseFloatFilter):
    pass


class FloatSmallerFilter(FilterSmaller, filters.BaseFloatFilter):
    pass


class FloatInListFilter(filters.BaseFloatListFilter, FilterInList):
    pass


class FloatNotInListFilter(filters.BaseFloatListFilter, FilterNotInList):
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
    def __init__(self, column, name, options=None, data_type=None):
        super().__init__(column, name, options, data_type="daterangepicker")

    def apply(self, query, value, alias=None):
        start, end = value
        return query.filter(self.get_column(alias).between(start, end))


class DateNotBetweenFilter(DateBetweenFilter):
    def apply(self, query, value, alias=None):
        start, end = value
        return query.filter(not_(self.get_column(alias).between(start, end)))

    def operation(self):
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
    def __init__(self, column, name, options=None, data_type=None):
        super().__init__(column, name, options, data_type="datetimerangepicker")

    def apply(self, query, value, alias=None):
        start, end = value
        return query.filter(self.get_column(alias).between(start, end))


class DateTimeNotBetweenFilter(DateTimeBetweenFilter):
    def apply(self, query, value, alias=None):
        start, end = value
        return query.filter(not_(self.get_column(alias).between(start, end)))

    def operation(self):
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
    def __init__(self, column, name, options=None, data_type=None):
        super().__init__(column, name, options, data_type="timerangepicker")

    def apply(self, query, value, alias=None):
        start, end = value
        return query.filter(self.get_column(alias).between(start, end))


class TimeNotBetweenFilter(TimeBetweenFilter):
    def apply(self, query, value, alias=None):
        start, end = value
        return query.filter(not_(self.get_column(alias).between(start, end)))

    def operation(self):
        return lazy_gettext("not between")


class EnumEqualFilter(FilterEqual):
    def __init__(self, column, name, options=None, **kwargs):
        self.enum_class = column.type.enum_class
        super().__init__(column, name, options, **kwargs)

    def clean(self, value):
        if self.enum_class is None:
            return super().clean(value)
        return self.enum_class[value]


class EnumFilterNotEqual(FilterNotEqual):
    def __init__(self, column, name, options=None, **kwargs):
        self.enum_class = column.type.enum_class
        super().__init__(column, name, options, **kwargs)

    def clean(self, value):
        if self.enum_class is None:
            return super().clean(value)
        return self.enum_class[value]


class EnumFilterEmpty(FilterEmpty):
    def __init__(self, column, name, options=None, **kwargs):
        self.enum_class = column.type.enum_class
        super().__init__(column, name, options, **kwargs)


class EnumFilterInList(FilterInList):
    def __init__(self, column, name, options=None, **kwargs):
        self.enum_class = column.type.enum_class
        super().__init__(column, name, options, **kwargs)

    def clean(self, value):
        values = super().clean(value)
        if self.enum_class is not None:
            values = [self.enum_class[val] for val in values]
        return values


class EnumFilterNotInList(FilterNotInList):
    def __init__(self, column, name, options=None, **kwargs):
        self.enum_class = column.type.enum_class
        super().__init__(column, name, options, **kwargs)

    def clean(self, value):
        values = super().clean(value)
        if self.enum_class is not None:
            values = [self.enum_class[val] for val in values]
        return values


class ChoiceTypeEqualFilter(FilterEqual):
    def __init__(self, column, name, options=None, **kwargs):
        super().__init__(column, name, options, **kwargs)

    def apply(self, query, user_query, alias=None):
        column = self.get_column(alias)
        choice_type = None
        # loop through choice 'values' to try and find an exact match
        if isinstance(column.type.choices, enum.EnumMeta):
            for choice in column.type.choices:
                if choice.name == user_query:
                    choice_type = choice.value
                    break
        else:
            for type, value in column.type.choices:
                if value == user_query:
                    choice_type = type
                    break
        if choice_type:
            return query.filter(column == choice_type)
        else:
            return query.filter(column.in_([]))


class ChoiceTypeNotEqualFilter(FilterNotEqual):
    def __init__(self, column, name, options=None, **kwargs):
        super().__init__(column, name, options, **kwargs)

    def apply(self, query, user_query, alias=None):
        column = self.get_column(alias)
        choice_type = None
        # loop through choice 'values' to try and find an exact match
        if isinstance(column.type.choices, enum.EnumMeta):
            for choice in column.type.choices:
                if choice.name == user_query:
                    choice_type = choice.value
                    break
        else:
            for type, value in column.type.choices:
                if value == user_query:
                    choice_type = type
                    break
        if choice_type:
            # != can exclude NULL values, so "or_ == None" needed to be added
            return query.filter(or_(column != choice_type, column == None))  # noqa: E711
        else:
            return query


class ChoiceTypeLikeFilter(FilterLike):
    def __init__(self, column, name, options=None, **kwargs):
        super().__init__(column, name, options, **kwargs)

    def apply(self, query, user_query, alias=None):
        column = self.get_column(alias)
        choice_types = []
        if user_query:
            # loop through choice 'values' looking for matches
            if isinstance(column.type.choices, enum.EnumMeta):
                for choice in column.type.choices:
                    if user_query.lower() in choice.name.lower():
                        choice_types.append(choice.value)
            else:
                for type, value in column.type.choices:
                    if user_query.lower() in value.lower():
                        choice_types.append(type)
        if choice_types:
            return query.filter(column.in_(choice_types))
        else:
            return query


class ChoiceTypeNotLikeFilter(FilterNotLike):
    def __init__(self, column, name, options=None, **kwargs):
        super().__init__(column, name, options, **kwargs)

    def apply(self, query, user_query, alias=None):
        column = self.get_column(alias)
        choice_types = []
        if user_query:
            # loop through choice 'values' looking for matches
            if isinstance(column.type.choices, enum.EnumMeta):
                for choice in column.type.choices:
                    if user_query.lower() in choice.name.lower():
                        choice_types.append(choice.value)
            else:
                for type, value in column.type.choices:
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

    def convert(self, type_name, column, name, **kwargs):
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
    def conv_string(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.strings]

    @filters.convert("UUIDType", "ColorType", "TimezoneType", "CurrencyType")
    def conv_string_keys(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.string_key_filters]

    @filters.convert("boolean", "tinyint")
    def conv_bool(self, column, name, **kwargs):
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
    def conv_int(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.int_filters]

    @filters.convert(
        "float", "real", "decimal", "numeric", "double_precision", "double"
    )
    def conv_float(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.float_filters]

    @filters.convert("date")
    def conv_date(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.date_filters]

    @filters.convert("datetime", "datetime2", "timestamp", "smalldatetime")
    def conv_datetime(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.datetime_filters]

    @filters.convert("time")
    def conv_time(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.time_filters]

    @filters.convert("ChoiceType")
    def conv_sqla_utils_choice(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.choice_type_filters]

    @filters.convert("ArrowType")
    def conv_sqla_utils_arrow(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.arrow_type_filters]

    @filters.convert("enum")
    def conv_enum(self, column, name, options=None, **kwargs):
        if not options:
            options = [(v, v) for v in column.type.enums]

        return [f(column, name, options, **kwargs) for f in self.enum]

    @filters.convert("uuid")
    def conv_uuid(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.uuid_filters]
