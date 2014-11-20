import warnings
import time
import datetime

from flask.ext.admin.babel import lazy_gettext
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
        return lazy_gettext('equals')


class FilterNotEqual(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column != value)

    def operation(self):
        return lazy_gettext('not equal')


class FilterLike(BaseSQLAFilter):
    def apply(self, query, value):
        stmt = tools.parse_like_term(value)
        return query.filter(self.column.ilike(stmt))

    def operation(self):
        return lazy_gettext('contains')


class FilterNotLike(BaseSQLAFilter):
    def apply(self, query, value):
        stmt = tools.parse_like_term(value)
        return query.filter(~self.column.ilike(stmt))

    def operation(self):
        return lazy_gettext('not contains')


class FilterGreater(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column > value)

    def operation(self):
        return lazy_gettext('greater than')


class FilterSmaller(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column < value)

    def operation(self):
        return lazy_gettext('smaller than')


# Customized type filters
class BooleanEqualFilter(FilterEqual, filters.BaseBooleanFilter):
    pass
    

class BooleanNotEqualFilter(FilterNotEqual, filters.BaseBooleanFilter):
    pass
    
   
class DateTimeEqualFilter(FilterEqual, filters.BaseDateTimeFilter):
    def clean(self, value):
        return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

        
class TimeEqualFilter(FilterEqual, filters.BaseTimeFilter):
    def clean(self, value):
        timetuple = time.strptime(value, '%H:%M:%S')
        return datetime.time(timetuple.tm_hour,
                             timetuple.tm_min,
                             timetuple.tm_sec)
                             

# Base SQLA filter field converter
class FilterConverter(filters.BaseFilterConverter):
    strings = (FilterEqual, FilterNotEqual, FilterLike, FilterNotLike)
    numeric = (FilterEqual, FilterNotEqual, FilterGreater, FilterSmaller)
    bool = (BooleanEqualFilter, BooleanNotEqualFilter)
    enum = (FilterEqual, FilterNotEqual)

    def convert(self, type_name, column, name, **kwargs):
        if type_name.lower() in self.converters:
            return self.converters[type_name.lower()](column, name, **kwargs)

        return None

    @filters.convert('string', 'unicode', 'text', 'unicodetext', 'varchar')
    def conv_string(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.strings]

    @filters.convert('boolean', 'tinyint')
    def conv_bool(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.bool]

    @filters.convert('integer', 'smallinteger', 'numeric', 'float', 'biginteger')
    def conv_int(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.numeric]

    @filters.convert('date')
    def conv_date(self, column, name, **kwargs):
        return [f(column, name, data_type='datepicker', **kwargs) for f in self.numeric]

    @filters.convert('datetime')
    def conv_datetime(self, column, name, **kwargs):
        return [DateTimeEqualFilter(column, name),
                FilterNotEqual(column, name, data_type='datetimepicker', **kwargs),
                FilterGreater(column, name, data_type='datetimepicker', **kwargs),
                FilterSmaller(column, name, data_type='datetimepicker', **kwargs)]
                
    @filters.convert('time')
    def conv_time(self, column, name, **kwargs):
        return [TimeEqualFilter(column, name),
                FilterNotEqual(column, name, data_type='timepicker', **kwargs),
                FilterGreater(column, name, data_type='timepicker', **kwargs),
                FilterSmaller(column, name, data_type='timepicker', **kwargs)]

    @filters.convert('enum')
    def conv_enum(self, column, name, options=None, **kwargs):
        if not options:
            options = [
                (v, v)
                for v in column.type.enums
            ]
        return [f(column, name, options, **kwargs) for f in self.enum]
