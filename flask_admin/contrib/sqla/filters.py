import warnings

from flask.ext.admin.babel import gettext
from flask.ext.admin.model import filters
from flask.ext.admin.contrib.sqla import tools


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


# Common filters
class FilterEqual(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column == value)

    def operation(self):
        return gettext('equals')


class FilterNotEqual(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column != value)

    def operation(self):
        return gettext('not equal')


class FilterLike(BaseSQLAFilter):
    def apply(self, query, value):
        stmt = tools.parse_like_term(value)
        return query.filter(self.column.ilike(stmt))

    def operation(self):
        return gettext('contains')


class FilterNotLike(BaseSQLAFilter):
    def apply(self, query, value):
        stmt = tools.parse_like_term(value)
        return query.filter(~self.column.ilike(stmt))

    def operation(self):
        return gettext('not contains')


class FilterGreater(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column > value)

    def operation(self):
        return gettext('greater than')


class FilterSmaller(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column < value)

    def operation(self):
        return gettext('smaller than')


# Customized type filters
class BooleanEqualFilter(FilterEqual, filters.BaseBooleanFilter):
    pass


class BooleanNotEqualFilter(FilterNotEqual, filters.BaseBooleanFilter):
    pass


# Base SQLA filter field converter
class FilterConverter(filters.BaseFilterConverter):
    strings = (FilterEqual, FilterNotEqual, FilterLike, FilterNotLike)
    numeric = (FilterEqual, FilterNotEqual, FilterGreater, FilterSmaller)
    bool = (BooleanEqualFilter, BooleanNotEqualFilter)
    enum = (FilterEqual, FilterNotEqual)

    def convert(self, type_name, column, name, **kwargs):
        if type_name in self.converters:
            return self.converters[type_name](column, name, **kwargs)

        return None

    @filters.convert('String', 'Unicode', 'Text', 'UnicodeText')
    def conv_string(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.strings]

    @filters.convert('Boolean')
    def conv_bool(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.bool]

    @filters.convert('Integer', 'SmallInteger', 'Numeric', 'Float', 'BigInteger')
    def conv_int(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.numeric]

    @filters.convert('Date')
    def conv_date(self, column, name, **kwargs):
        return [f(column, name, data_type='datepicker', **kwargs) for f in self.numeric]

    @filters.convert('DateTime')
    def conv_datetime(self, column, name, **kwargs):
        return [f(column, name, data_type='datetimepicker', **kwargs) for f in self.numeric]

    @filters.convert('Enum', 'ENUM')
    def conv_enum(self, column, name, options=None, **kwargs):
        if not options:
            options = [
                (v, v)
                for v in column.type.enums
            ]
        return [f(column, name, options, **kwargs) for f in self.enum]
