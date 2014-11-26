import warnings
import time
import datetime

from flask.ext.admin.babel import lazy_gettext
from flask.ext.admin.model import filters
from flask.ext.admin.contrib.sqla import tools
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


class FilterEmpty(BaseSQLAFilter, filters.BaseBooleanFilter):
    def apply(self, query, value):
        if value == '1':
            return query.filter(self.column == None)
        else:
            return query.filter(self.column != None)

    def operation(self):
        return lazy_gettext('empty')
        

class FilterInList(BaseSQLAFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(FilterInList, self).__init__(column, name, options, data_type='select2-tags')

    def clean(self, value):
        return [v.strip() for v in value.split(',') if v.strip()]
        
    def apply(self, query, value):
        return query.filter(self.column.in_(value))
    
    def operation(self):
        return lazy_gettext('in list')
        

class FilterNotInList(FilterInList):
    def apply(self, query, value):
        # NOT IN can exclude NULL values, so "or_ == None" needed to be added
        return query.filter(or_(~self.column.in_(value), self.column == None))
    
    def operation(self):
        return lazy_gettext('not in list')
        

# Customized type filters
class BooleanEqualFilter(FilterEqual, filters.BaseBooleanFilter):
    pass
    

class BooleanNotEqualFilter(FilterNotEqual, filters.BaseBooleanFilter):
    pass
    

class DateEqualFilter(FilterEqual, filters.BaseDateFilter):
    pass

    
class DateNotEqualFilter(FilterNotEqual, filters.BaseDateFilter):
    pass
        

class DateGreaterFilter(FilterGreater, filters.BaseDateFilter):
    pass
        

class DateSmallerFilter(FilterSmaller, filters.BaseDateFilter):
    pass
        

class DateBetweenFilter(BaseSQLAFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(DateBetweenFilter, self).__init__(column, name, options, data_type='daterangepicker')
        
    def clean(self, value):
        return [datetime.datetime.strptime(range, '%Y-%m-%d') for range in value.split(' to ')]

    def apply(self, query, value):
        start, end = value
        return query.filter(self.column.between(start, end))

    def operation(self):
        return lazy_gettext('between')

    def validate(self, value):
        try:
            value = [datetime.datetime.strptime(range, '%Y-%m-%d') for range in value.split(' to ')]
            # if " to " is missing, fail validation
            # sqlalchemy's .between() will not work if end date is before start date
            if (len(value) == 2) and (value[0] <= value[1]):
                return True
            else:
                return False        
        except ValueError:
            return False        
        

class DateNotBetweenFilter(DateBetweenFilter):
    def apply(self, query, value):
        start, end = value
        # ~between() isn't possible until sqlalchemy 1.0.0
        return query.filter(not_(self.column.between(start, end)))
        
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
        

class DateTimeBetweenFilter(BaseSQLAFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(DateTimeBetweenFilter, self).__init__(column, name, options, data_type='datetimerangepicker')
        
    def clean(self, value):
        return [datetime.datetime.strptime(range, '%Y-%m-%d %H:%M:%S') for range in value.split(' to ')]
        
    def apply(self, query, value):
        start, end = value
        return query.filter(self.column.between(start, end))
    
    def operation(self):
        return lazy_gettext('between')
        
    def validate(self, value):
        try:
            value = [datetime.datetime.strptime(range, '%Y-%m-%d %H:%M:%S') for range in value.split(' to ')]
            if (len(value) == 2) and (value[0] <= value[1]):
                return True
            else:
                return False
        except ValueError:
            return False
            

class DateTimeNotBetweenFilter(DateTimeBetweenFilter):
    def apply(self, query, value):
        start, end = value
        return query.filter(not_(self.column.between(start, end)))

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
    

class TimeBetweenFilter(BaseSQLAFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(TimeBetweenFilter, self).__init__(column, name, options, data_type='timerangepicker')
        
    def clean(self, value):
        timetuples = [time.strptime(range, '%H:%M:%S') 
                      for range in value.split(' to ')]
        return [datetime.time(timetuple.tm_hour,
                              timetuple.tm_min,
                              timetuple.tm_sec)
                              for timetuple in timetuples]
                              
    def apply(self, query, value):
        start, end = value
        return query.filter(self.column.between(start, end))

    def operation(self):
        return lazy_gettext('between')

    def validate(self, value):
        try:
            timetuples = [time.strptime(range, '%H:%M:%S') 
                          for range in value.split(' to ')]
            if (len(timetuples) == 2) and (timetuples[0] <= timetuples[1]):
                return True
            else:
                return False
        except ValueError:
            raise
            return False
        

class TimeNotBetweenFilter(TimeBetweenFilter):
    def apply(self, query, value):
        start, end = value
        return query.filter(not_(self.column.between(start, end)))
        
    def operation(self):
        return lazy_gettext('not between')
        
            
# Base SQLA filter field converter
class FilterConverter(filters.BaseFilterConverter):
    strings = (FilterEqual, FilterNotEqual, FilterLike, FilterNotLike, FilterEmpty, FilterInList, FilterNotInList)
    numeric = (FilterEqual, FilterNotEqual, FilterGreater, FilterSmaller, FilterEmpty, FilterInList, FilterNotInList)
    bool = (BooleanEqualFilter, BooleanNotEqualFilter)
    enum = (FilterEqual, FilterNotEqual, FilterEmpty, FilterInList, FilterNotInList)
    date_filters = (DateEqualFilter, DateNotEqualFilter, DateGreaterFilter, DateSmallerFilter, 
            DateBetweenFilter, DateNotBetweenFilter, FilterEmpty)
    datetime_filters = (DateTimeEqualFilter, DateTimeNotEqualFilter, DateTimeGreaterFilter, 
                DateTimeSmallerFilter, DateTimeBetweenFilter, DateTimeNotBetweenFilter, 
                FilterEmpty)
    time_filters = (TimeEqualFilter, TimeNotEqualFilter, TimeGreaterFilter, TimeSmallerFilter, 
            TimeBetweenFilter, TimeNotBetweenFilter, FilterEmpty)
            
    def convert(self, type_name, column, name, **kwargs):
        if type_name.lower() in self.converters:
            return self.converters[type_name.lower()](column, name, **kwargs)
        return None
        
    @filters.convert('string', 'char', 'unicode', 'varchar', 'tinytext',
                     'text', 'mediumtext', 'longtext', 'unicodetext',
                     'nchar', 'nvarchar', 'ntext')
    def conv_string(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.strings]
        
    @filters.convert('boolean', 'tinyint')
    def conv_bool(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.bool]
        
    @filters.convert('int', 'integer', 'smallinteger', 'smallint', 'numeric',
                     'float', 'real', 'biginteger', 'bigint', 'decimal',
                     'double_precision', 'double', 'mediumint')
    def conv_int(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.numeric]
        
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
        # set all operations to select2
        kwargs['data_type'] = "select2"
        if not options:
            options = [
                (v, v)
                for v in column.type.enums
            ]
        return [f(column, name, options, **kwargs) for f in self.enum]
