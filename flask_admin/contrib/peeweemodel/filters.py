from flask.ext.admin.babel import gettext

from flask.ext.admin.model import filters
from .tools import parse_like_term


class BasePeeweeFilter(filters.BaseFilter):
    """
        Base Peewee filter.
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
        super(BasePeeweeFilter, self).__init__(name, options, data_type)

        self.column = column


# Common filters
class FilterEqual(BasePeeweeFilter):
    def apply(self, query, value):
        return query.filter(self.column == value)

    def operation(self):
        return gettext('equals')


class FilterNotEqual(BasePeeweeFilter):
    def apply(self, query, value):
        return query.filter(self.column != value)

    def operation(self):
        return gettext('not equal')


class FilterLike(BasePeeweeFilter):
    def apply(self, query, value):
        term = parse_like_term(value)
        return query.filter(self.column ** term)

    def operation(self):
        return gettext('contains')


class FilterNotLike(BasePeeweeFilter):
    def apply(self, query, value):
        term = parse_like_term(value)
        return query.filter(~(self.column ** term))

    def operation(self):
        return gettext('not contains')


class FilterGreater(BasePeeweeFilter):
    def apply(self, query, value):
        return query.filter(self.column > value)

    def operation(self):
        return gettext('greater than')


class FilterSmaller(BasePeeweeFilter):
    def apply(self, query, value):
        return query.filter(self.column < value)

    def operation(self):
        return gettext('smaller than')


# Customized type filters
class BooleanEqualFilter(FilterEqual, filters.BaseBooleanFilter):
    pass


class BooleanNotEqualFilter(FilterNotEqual, filters.BaseBooleanFilter):
    pass


# Base peewee filter field converter
class FilterConverter(filters.BaseFilterConverter):
    strings = (FilterEqual, FilterNotEqual, FilterLike, FilterNotLike)
    numeric = (FilterEqual, FilterNotEqual, FilterGreater, FilterSmaller)

    def convert(self, type_name, column, name):
        if type_name in self.converters:
            return self.converters[type_name](column, name)

        return None

    @filters.convert('CharField', 'TextField')
    def conv_string(self, column, name):
        return [f(column, name) for f in self.strings]

    @filters.convert('BooleanField')
    def conv_bool(self, column, name):
        return [BooleanEqualFilter(column, name),
                BooleanNotEqualFilter(column, name)]

    @filters.convert('IntegerField', 'DecimalField', 'FloatField')
    def conv_int(self, column, name):
        return [f(column, name) for f in self.numeric]

    @filters.convert('DateField')
    def conv_date(self, column, name):
        return [f(column, name, data_type='datepicker') for f in self.numeric]

    @filters.convert('DateTimeField')
    def conv_datetime(self, column, name):
        return [f(column, name, data_type='datetimepicker')
                for f in self.numeric]
