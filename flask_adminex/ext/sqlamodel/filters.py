from flask.ext.adminex.model import filters
from flask.ext.adminex.ext.sqlamodel import tools


class BaseSQLAFilter(filters.BaseFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(BaseSQLAFilter, self).__init__(name, options, data_type)

        self.column = column


# Common filters
class FilterEqual(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column == value)

    def __unicode__(self):
        return '%s equals' % self.name


class FilterNotEqual(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column != value)

    def __unicode__(self):
        return '%s not equal' % self.name


class FilterLike(BaseSQLAFilter):
    def apply(self, query, value):
        stmt = tools.parse_like_term(value)
        return query.filter(self.column.ilike(stmt))

    def __unicode__(self):
        return '%s like' % self.name


class FilterNotLike(BaseSQLAFilter):
    def apply(self, query, value):
        stmt = tools.parse_like_term(value)
        return query.filter(~self.column.ilike(stmt))

    def __unicode__(self):
        return '%s not like' % self.name


class FilterGreater(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column > value)

    def __unicode__(self):
        return '%s greater than' % self.name


class FilterSmaller(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column < value)

    def __unicode__(self):
        return '%s smaller than' % self.name


# Customized type filters
class BooleanEqualFilter(FilterEqual, filters.BaseBooleanFilter):
    pass


class BooleanNotEqualFilter(FilterNotEqual, filters.BaseBooleanFilter):
    pass


# Base SQLA filter field converter
class FilterConverter(filters.BaseFilterConverter):
    strings = (FilterEqual, FilterNotEqual, FilterLike, FilterNotLike)
    numeric = (FilterEqual, FilterNotEqual, FilterGreater, FilterSmaller)

    def convert(self, type_name, column, name):
        if type_name in self.converters:
            return self.converters[type_name](column, name)

        return None

    @filters.convert('String', 'Unicode', 'Text', 'UnicodeText')
    def conv_string(self, column, name):
        return [f(column, name) for f in self.strings]

    @filters.convert('Boolean')
    def conv_bool(self, column, name):
        return [BooleanEqualFilter(column, name),
                BooleanNotEqualFilter(column, name)]

    @filters.convert('Integer', 'SmallInteger', 'Numeric', 'Float')
    def conv_int(self, column, name):
        return [f(column, name) for f in self.numeric]

    @filters.convert('Date')
    def conv_date(self, column, name):
        return [f(column, name, data_type='datepicker') for f in self.numeric]

    @filters.convert('DateTime')
    def conv_datetime(self, column, name):
        return [f(column, name, data_type='datetimepicker') for f in self.numeric]
