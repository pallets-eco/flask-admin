import datetime

from flask_admin.babel import lazy_gettext
from flask_admin.model import filters

from .tools import parse_like_term
from mongoengine.queryset import Q

class BaseMongoEngineFilter(filters.BaseFilter):
    """
        Base MongoEngine filter.
    """
    def __init__(self, column, name, options=None, data_type=None):
        """
            Constructor.

            :param column:
                Model field
            :param name:
                Display name
            :param options:
                Fixed set of options. If provided, will use drop down instead of textbox.
            :param data_type:
                Client data type
        """
        super(BaseMongoEngineFilter, self).__init__(name, options, data_type)

        self.column = column


# Common filters
class FilterEqual(BaseMongoEngineFilter):
    def apply(self, query, value):
        flt = {'%s' % self.column.name: value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('equals')


class FilterNotEqual(BaseMongoEngineFilter):
    def apply(self, query, value):
        flt = {'%s__ne' % self.column.name: value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('not equal')


class FilterLike(BaseMongoEngineFilter):
    def apply(self, query, value):
        term, data = parse_like_term(value)
        flt = {'%s__%s' % (self.column.name, term): data}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('contains')


class FilterNotLike(BaseMongoEngineFilter):
    def apply(self, query, value):
        term, data = parse_like_term(value)
        flt = {'%s__not__%s' % (self.column.name, term): data}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('not contains')


class FilterGreater(BaseMongoEngineFilter):
    def apply(self, query, value):
        flt = {'%s__gt' % self.column.name: value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('greater than')


class FilterSmaller(BaseMongoEngineFilter):
    def apply(self, query, value):
        flt = {'%s__lt' % self.column.name: value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('smaller than')


class FilterEmpty(BaseMongoEngineFilter, filters.BaseBooleanFilter):
    def apply(self, query, value):
        if value == '1':
            flt = {'%s' % self.column.name: None}
        else:
            flt = {'%s__ne' % self.column.name: None}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('empty')


class FilterInList(BaseMongoEngineFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(FilterInList, self).__init__(column, name, options, data_type='select2-tags')

    def clean(self, value):
        return [v.strip() for v in value.split(',') if v.strip()]

    def apply(self, query, value):
        flt = {'%s__in' % self.column.name: value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('in list')


class FilterNotInList(FilterInList):
    def apply(self, query, value):
        flt = {'%s__nin' % self.column.name: value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('not in list')


# Customized type filters
class BooleanEqualFilter(FilterEqual, filters.BaseBooleanFilter):
    def apply(self, query, value):
        flt = {'%s' % self.column.name: value == '1'}
        return query.filter(**flt)


class BooleanNotEqualFilter(FilterNotEqual, filters.BaseBooleanFilter):
    def apply(self, query, value):
        flt = {'%s' % self.column.name: value != '1'}
        return query.filter(**flt)


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


class DateTimeEqualFilter(FilterEqual, filters.BaseDateTimeFilter):
    pass


class DateTimeNotEqualFilter(FilterNotEqual, filters.BaseDateTimeFilter):
    pass


class DateTimeGreaterFilter(FilterGreater, filters.BaseDateTimeFilter):
    pass


class DateTimeSmallerFilter(FilterSmaller, filters.BaseDateTimeFilter):
    pass


class DateTimeBetweenFilter(BaseMongoEngineFilter, filters.BaseDateTimeBetweenFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(DateTimeBetweenFilter, self).__init__(column,
                                                    name,
                                                    options,
                                                    data_type='datetimerangepicker')

    def apply(self, query, value):
        start, end = value
        flt = {'%s__gte' % self.column.name: start, '%s__lte' % self.column.name: end}
        return query.filter(**flt)


class DateTimeNotBetweenFilter(DateTimeBetweenFilter):
    def apply(self, query, value):
        start, end = value
        return query.filter(Q(**{'%s__not__gte' % self.column.name: start}) |
                            Q(**{'%s__not__lte' % self.column.name: end}))

    def operation(self):
        return lazy_gettext('not between')


# Base MongoEngine filter field converter
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
    datetime_filters = (DateTimeEqualFilter, DateTimeNotEqualFilter,
                        DateTimeGreaterFilter, DateTimeSmallerFilter,
                        DateTimeBetweenFilter, DateTimeNotBetweenFilter,
                        FilterEmpty)

    def convert(self, type_name, column, name):
        filter_name = type_name.lower()

        if filter_name in self.converters:
            return self.converters[filter_name](column, name)

        return None

    @filters.convert('StringField', 'EmailField', 'URLField')
    def conv_string(self, column, name):
        return [f(column, name) for f in self.strings]

    @filters.convert('BooleanField')
    def conv_bool(self, column, name):
        return [f(column, name) for f in self.bool_filters]

    @filters.convert('IntField', 'LongField')
    def conv_int(self, column, name):
        return [f(column, name) for f in self.int_filters]

    @filters.convert('DecimalField', 'FloatField')
    def conv_float(self, column, name):
        return [f(column, name) for f in self.float_filters]

    @filters.convert('DateTimeField', 'ComplexDateTimeField')
    def conv_datetime(self, column, name):
        return [f(column, name) for f in self.datetime_filters]
