from flask_admin.model import filters
from flask_admin.babel import lazy_gettext
from google.cloud.ndb.query import AND


class BaseAppEngineFilter(filters.BaseFilter):
    """
        Base AppEngine filter.
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
        super(BaseAppEngineFilter, self).__init__(name, options, data_type)

        self.column = column

    def get_column(self, alias):
        return self.column if alias is None else getattr(alias, self.column)


# Common filters
class FilterEqual(BaseAppEngineFilter):
    def apply(self, model, value):
        return getattr(model, self.column) == value

    def operation(self):
        return lazy_gettext('equals')


class FilterNotEqual(BaseAppEngineFilter):
    def apply(self, model, value):
        return getattr(model, self.column) != value

    def operation(self):
        return lazy_gettext('not equal')


class FilterInList(BaseAppEngineFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(FilterInList, self).__init__(column, name, options, data_type='select2-tags')

    def clean(self, value):
        if isinstance(value, str):
            value = [v.strip() for v in value.split(',') if v.strip()] or ['']
        return value

    def apply(self, model, value):
        return getattr(model, self.column).IN(value)

    def operation(self):
        return lazy_gettext('in list')


class FilterGreater(BaseAppEngineFilter):
    def apply(self, model, value):
        return getattr(model, self.column) > value

    def operation(self):
        return lazy_gettext('greater than')


class FilterSmaller(BaseAppEngineFilter):
    def apply(self, model, value):
        return getattr(model, self.column) < value

    def operation(self):
        return lazy_gettext('smaller than')


class FilterEmpty(BaseAppEngineFilter, filters.BaseBooleanFilter):
    def apply(self, model, value):
        column = getattr(model, self.column)
        if value == '1':
            flt = column == None
        else:
            flt = column != None
        return flt

    def operation(self):
        return lazy_gettext('empty')


# Customized type filters
class BooleanEqualFilter(FilterEqual, filters.BaseBooleanFilter):
    def apply(self, model, value):
        if value == '1':
            flt = getattr(model, self.column) == True
        else:
            flt = getattr(model, self.column) == False
        return flt


class BooleanNotEqualFilter(FilterNotEqual, filters.BaseBooleanFilter):
    def apply(self, query, value):
        if value == '1':
            flt = getattr(model, self.column) == False
        else:
            flt = getattr(model, self.column) == True
        return flt


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


class DateTimeEqualFilter(FilterEqual, filters.BaseDateTimeFilter):
    pass


class DateTimeNotEqualFilter(FilterNotEqual, filters.BaseDateTimeFilter):
    pass


class DateTimeGreaterFilter(FilterGreater, filters.BaseDateTimeFilter):
    pass


class DateTimeSmallerFilter(FilterSmaller, filters.BaseDateTimeFilter):
    pass


class DateTimeBetweenFilter(BaseAppEngineFilter, filters.BaseDateTimeBetweenFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(DateTimeBetweenFilter, self).__init__(
            column, name, options, data_type='datetimerangepicker'
        )

    def apply(self, model, value):
        start, end = value
        column = getattr(model, self.column)
        return AND(column >= start, column <= end)


# Base AppEngine filter field converter
class FilterConverter(filters.BaseFilterConverter):
    strings = (FilterEqual, FilterInList, FilterEmpty)
    int_filters = (IntEqualFilter, IntNotEqualFilter, IntGreaterFilter,
                   IntSmallerFilter, FilterEmpty, IntInListFilter)
    float_filters = (FloatEqualFilter, FloatNotEqualFilter, FloatGreaterFilter,
                     FloatSmallerFilter, FilterEmpty, FloatInListFilter)
    bool_filters = (BooleanEqualFilter, BooleanNotEqualFilter)
    datetime_filters = (DateTimeEqualFilter, DateTimeNotEqualFilter,
                        DateTimeGreaterFilter, DateTimeSmallerFilter,
                        DateTimeBetweenFilter, FilterEmpty)

    def convert(self, type_name, column, name):
        filter_name = type_name.lower()

        if filter_name in self.converters:
            return self.converters[filter_name](column, name)

        return None

    @filters.convert('StringField', 'EmailField', 'URLField')
    def conv_string(self, column, name):
        return [f(column, name) for f in self.strings]
