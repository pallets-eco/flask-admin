from flask_admin.babel import lazy_gettext
from flask_admin.model import filters

from django.db.models import Q


def parse_like_term(term):
    """
        Parse search term into (operation, term) tuple. Recognizes operators
        in the beginning of the search term.
        * = case insensitive (can precede other operators)
        ^ = starts with
        = = exact

        :param term:
            Search term
    """
    case_insensitive = term.startswith('*')
    if case_insensitive:
        term = term[1:]
    # apply operators
    if term.startswith('^'):
        oper = 'startswith'
        term = term[1:]
    elif term.startswith('='):
        oper = 'exact'
        term = term[1:]
    else:
        oper = 'contains'
    # add case insensitive flag
    if case_insensitive:
        oper = 'i' + oper
    return oper, term


class DjangoDbModelsFilter(filters.BaseFilter):
    """
        Base Django filter.
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
        super(DjangoDbModelsFilter, self).__init__(name, options, data_type)

        self.column = column


# Common filters
class FilterEqual(DjangoDbModelsFilter):

    def apply(self, query, value):
        flt = {'%s' % self.column.name: value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('equals')


class FilterNotEqual(DjangoDbModelsFilter):

    def apply(self, query, value):
        flt = {'%s__ne' % self.column.name: value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('not equal')


class FilterLike(DjangoDbModelsFilter):

    def apply(self, query, value):
        term, data = parse_like_term(value)
        flt = {'%s__%s' % (self.column.name, term): data}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('contains')


class FilterNotLike(DjangoDbModelsFilter):

    def apply(self, query, value):
        term, data = parse_like_term(value)
        flt = {'%s__not__%s' % (self.column.name, term): data}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('not contains')


class FilterGreater(DjangoDbModelsFilter):

    def apply(self, query, value):
        flt = {'%s__gt' % self.column.name: value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('greater than')


class FilterSmaller(DjangoDbModelsFilter):

    def apply(self, query, value):
        flt = {'%s__lt' % self.column.name: value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('smaller than')


class FilterEmpty(DjangoDbModelsFilter, filters.BaseBooleanFilter):

    def apply(self, query, value):
        if value == '1':
            flt = {'%s' % self.column.name: None}
        else:
            flt = {'%s__ne' % self.column.name: None}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext('empty')

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

class FloatEqualFilter(FilterEqual, filters.BaseFloatFilter):
    pass


class FloatNotEqualFilter(FilterNotEqual, filters.BaseFloatFilter):
    pass


class FloatGreaterFilter(FilterGreater, filters.BaseFloatFilter):
    pass


class FloatSmallerFilter(FilterSmaller, filters.BaseFloatFilter):
    pass


class DateTimeEqualFilter(FilterEqual, filters.BaseDateTimeFilter):
    pass


class DateTimeNotEqualFilter(FilterNotEqual, filters.BaseDateTimeFilter):
    pass


class DateTimeGreaterFilter(FilterGreater, filters.BaseDateTimeFilter):
    pass


class DateTimeSmallerFilter(FilterSmaller, filters.BaseDateTimeFilter):
    pass


class DateTimeBetweenFilter(DjangoDbModelsFilter, filters.BaseDateTimeBetweenFilter):

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
               FilterEmpty)
    int_filters = (IntEqualFilter, IntNotEqualFilter, IntGreaterFilter,
                   IntSmallerFilter, FilterEmpty)
    float_filters = (FloatEqualFilter, FloatNotEqualFilter, FloatGreaterFilter,
                     FloatSmallerFilter, FilterEmpty)
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

    @filters.convert('CharField', 'EmailField', 'URLField')
    def conv_string(self, column, name):
        return [f(column, name) for f in self.strings]

    @filters.convert('BooleanField')
    def conv_bool(self, column, name):
        return [f(column, name) for f in self.bool_filters]

    @filters.convert('IntegerField', 'LongField')
    def conv_int(self, column, name):
        return [f(column, name) for f in self.int_filters]

    @filters.convert('DecimalField', 'FloatField')
    def conv_float(self, column, name):
        return [f(column, name) for f in self.float_filters]

    @filters.convert('DateTimeField', 'DateField')
    def conv_datetime(self, column, name):
        return [f(column, name) for f in self.datetime_filters]
