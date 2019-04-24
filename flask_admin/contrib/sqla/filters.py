from flask_admin.babel import lazy_gettext
from flask_admin.model import filters
from flask_admin.contrib.sqla import tools
from sqlalchemy.sql import not_, or_


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
        super(BaseSQLAFilter, self).__init__(name, options, data_type)

        self.column = column

    def get_column(self, alias):
        return self.column if alias is None else getattr(alias, self.column.key)

    def apply(self, query, value, alias=None):
        return super(BaseSQLAFilter, self).apply(query, value)


# Common filters
class FilterEqual(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.get_column(alias) == value)

    def operation(self):
        return lazy_gettext('equals')


class FilterNotEqual(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.get_column(alias) != value)

    def operation(self):
        return lazy_gettext('not equal')


class FilterLike(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        stmt = tools.parse_like_term(value)
        return query.filter(self.get_column(alias).ilike(stmt))

    def operation(self):
        return lazy_gettext('contains')


class FilterNotLike(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        stmt = tools.parse_like_term(value)
        return query.filter(~self.get_column(alias).ilike(stmt))

    def operation(self):
        return lazy_gettext('not contains')


class FilterGreater(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.get_column(alias) > value)

    def operation(self):
        return lazy_gettext('greater than')


class FilterSmaller(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.get_column(alias) < value)

    def operation(self):
        return lazy_gettext('smaller than')


class FilterEmpty(BaseSQLAFilter, filters.BaseBooleanFilter):
    def apply(self, query, value, alias=None):
        if value == '1':
            return query.filter(self.get_column(alias) == None)  # noqa: E711
        else:
            return query.filter(self.get_column(alias) != None)  # noqa: E711

    def operation(self):
        return lazy_gettext('empty')


class FilterInList(BaseSQLAFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(FilterInList, self).__init__(column, name, options, data_type='select2-tags')

    def clean(self, value):
        return [v.strip() for v in value.split(',') if v.strip()]

    def apply(self, query, value, alias=None):
        return query.filter(self.get_column(alias).in_(value))

    def operation(self):
        return lazy_gettext('in list')


class FilterNotInList(FilterInList):
    def apply(self, query, value, alias=None):
        # NOT IN can exclude NULL values, so "or_ == None" needed to be added
        column = self.get_column(alias)
        return query.filter(or_(~column.in_(value), column == None))  # noqa: E711

    def operation(self):
        return lazy_gettext('not in list')


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
        super(DateBetweenFilter, self).__init__(column,
                                                name,
                                                options,
                                                data_type='daterangepicker')

    def apply(self, query, value, alias=None):
        start, end = value
        return query.filter(self.get_column(alias).between(start, end))


class DateNotBetweenFilter(DateBetweenFilter):
    def apply(self, query, value, alias=None):
        start, end = value
        # ~between() isn't possible until sqlalchemy 1.0.0
        return query.filter(not_(self.get_column(alias).between(start, end)))

    def operation(self):
        return lazy_gettext('not between')


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
        super(DateTimeBetweenFilter, self).__init__(column,
                                                    name,
                                                    options,
                                                    data_type='datetimerangepicker')

    def apply(self, query, value, alias=None):
        start, end = value
        return query.filter(self.get_column(alias).between(start, end))


class DateTimeNotBetweenFilter(DateTimeBetweenFilter):
    def apply(self, query, value, alias=None):
        start, end = value
        return query.filter(not_(self.get_column(alias).between(start, end)))

    def operation(self):
        return lazy_gettext('not between')


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
        super(TimeBetweenFilter, self).__init__(column,
                                                name,
                                                options,
                                                data_type='timerangepicker')

    def apply(self, query, value, alias=None):
        start, end = value
        return query.filter(self.get_column(alias).between(start, end))


class TimeNotBetweenFilter(TimeBetweenFilter):
    def apply(self, query, value, alias=None):
        start, end = value
        return query.filter(not_(self.get_column(alias).between(start, end)))

    def operation(self):
        return lazy_gettext('not between')


class EnumEqualFilter(FilterEqual):
    def __init__(self, column, name, options=None, enum_class=None, **kwargs):
        self.enum_class = enum_class
        super(EnumEqualFilter, self).__init__(column, name, options, **kwargs)

    def clean(self, value):
        if self.enum_class is None:
            return super(EnumEqualFilter, self).clean(value)
        return self.enum_class(value)


class EnumFilterNotEqual(FilterNotEqual):
    def __init__(self, column, name, options=None, enum_class=None, **kwargs):
        self.enum_class = enum_class
        super(EnumFilterNotEqual, self).__init__(column, name, options, **kwargs)

    def clean(self, value):
        if self.enum_class is None:
            return super(EnumFilterNotEqual, self).clean(value)
        return self.enum_class(value)


class EnumFilterEmpty(FilterEmpty):
    def __init__(self, column, name, options=None, enum_class=None, **kwargs):
        self.enum_class = enum_class
        super(EnumFilterEmpty, self).__init__(column, name, options, **kwargs)


class EnumFilterInList(FilterInList):
    def __init__(self, column, name, options=None, enum_class=None, **kwargs):
        self.enum_class = enum_class
        super(EnumFilterInList, self).__init__(column, name, options, **kwargs)

    def clean(self, value):
        values = super(EnumFilterInList, self).clean(value)
        if self.enum_class is not None:
            values = [self.enum_class(val) for val in values]
        return values


class EnumFilterNotInList(FilterNotInList):
    def __init__(self, column, name, options=None, enum_class=None, **kwargs):
        self.enum_class = enum_class
        super(EnumFilterNotInList, self).__init__(column, name, options, **kwargs)

    def clean(self, value):
        values = super(EnumFilterNotInList, self).clean(value)
        if self.enum_class is not None:
            values = [self.enum_class(val) for val in values]
        return values


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
    strings = (FilterLike, FilterNotLike, FilterEqual, FilterNotEqual,
               FilterEmpty, FilterInList, FilterNotInList)
    int_filters = (IntEqualFilter, IntNotEqualFilter, IntGreaterFilter,
                   IntSmallerFilter, FilterEmpty, IntInListFilter,
                   IntNotInListFilter)
    float_filters = (FloatEqualFilter, FloatNotEqualFilter, FloatGreaterFilter,
                     FloatSmallerFilter, FilterEmpty, FloatInListFilter,
                     FloatNotInListFilter)
    bool_filters = (BooleanEqualFilter, BooleanNotEqualFilter)
    enum = (EnumEqualFilter, EnumFilterNotEqual, EnumFilterEmpty, EnumFilterInList,
            EnumFilterNotInList)
    date_filters = (DateEqualFilter, DateNotEqualFilter, DateGreaterFilter,
                    DateSmallerFilter, DateBetweenFilter, DateNotBetweenFilter,
                    FilterEmpty)
    datetime_filters = (DateTimeEqualFilter, DateTimeNotEqualFilter,
                        DateTimeGreaterFilter, DateTimeSmallerFilter,
                        DateTimeBetweenFilter, DateTimeNotBetweenFilter,
                        FilterEmpty)
    time_filters = (TimeEqualFilter, TimeNotEqualFilter, TimeGreaterFilter,
                    TimeSmallerFilter, TimeBetweenFilter, TimeNotBetweenFilter,
                    FilterEmpty)
    uuid_filters = (UuidFilterEqual, UuidFilterNotEqual, FilterEmpty,
                    UuidFilterInList, UuidFilterNotInList)

    def convert(self, type_name, column, name, **kwargs):
        filter_name = type_name.lower()

        if filter_name in self.converters:
            return self.converters[filter_name](column, name, **kwargs)

        return None

    @filters.convert('string', 'char', 'unicode', 'varchar', 'tinytext',
                     'text', 'mediumtext', 'longtext', 'unicodetext',
                     'nchar', 'nvarchar', 'ntext', 'citext')
    def conv_string(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.strings]

    @filters.convert('boolean', 'tinyint')
    def conv_bool(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.bool_filters]

    @filters.convert('int', 'integer', 'smallinteger', 'smallint',
                     'biginteger', 'bigint', 'mediumint')
    def conv_int(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.int_filters]

    @filters.convert('float', 'real', 'decimal', 'numeric', 'double_precision', 'double')
    def conv_float(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.float_filters]

    @filters.convert('date')
    def conv_date(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.date_filters]

    @filters.convert('datetime', 'datetime2', 'timestamp', 'smalldatetime')
    def conv_datetime(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.datetime_filters]

    @filters.convert('time')
    def conv_time(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.time_filters]

    @filters.convert('enum')
    def conv_enum(self, column, name, options=None, **kwargs):
        if not options:
            options = [
                (v, v)
                for v in column.type.enums
            ]
        try:
            from sqlalchemy_enum34 import EnumType
        except ImportError:
            pass
        else:
            if isinstance(column.type, EnumType):
                kwargs['enum_class'] = column.type._enum_class

        return [f(column, name, options, **kwargs) for f in self.enum]

    @filters.convert('uuid')
    def conv_uuid(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.uuid_filters]
