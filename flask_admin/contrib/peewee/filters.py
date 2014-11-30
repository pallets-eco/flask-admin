import time
import datetime

from flask.ext.admin.babel import lazy_gettext

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
        return lazy_gettext('equals')


class FilterNotEqual(BasePeeweeFilter):
    def apply(self, query, value):
        return query.filter(self.column != value)

    def operation(self):
        return lazy_gettext('not equal')


class FilterLike(BasePeeweeFilter):
    def apply(self, query, value):
        term = parse_like_term(value)
        return query.filter(self.column ** term)

    def operation(self):
        return lazy_gettext('contains')


class FilterNotLike(BasePeeweeFilter):
    def apply(self, query, value):
        term = parse_like_term(value)
        return query.filter(~(self.column ** term))

    def operation(self):
        return lazy_gettext('not contains')


class FilterGreater(BasePeeweeFilter):
    def apply(self, query, value):
        return query.filter(self.column > value)

    def operation(self):
        return lazy_gettext('greater than')


class FilterSmaller(BasePeeweeFilter):
    def apply(self, query, value):
        return query.filter(self.column < value)

    def operation(self):
        return lazy_gettext('smaller than')


class FilterEmpty(BasePeeweeFilter, filters.BaseBooleanFilter):
    def apply(self, query, value):
        if value == '1':
            return query.filter(self.column >> None)
        else:
            return query.filter(~(self.column >> None))

    def operation(self):
        return lazy_gettext('empty')
        

class FilterInList(BasePeeweeFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(FilterInList, self).__init__(column, name, options, data_type='select2-tags')

    def clean(self, value):
        return [v.strip() for v in value.split(',') if v.strip()]
        
    def apply(self, query, value):
        return query.filter(self.column << value)
    
    def operation(self):
        return lazy_gettext('in list')
        

class FilterNotInList(FilterInList):
    def apply(self, query, value):
        # NOT IN can exclude NULL values, so "or_ == None" needed to be added
        return query.filter(~(self.column << value) | (self.column >> None))
    
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
    

class DateBetweenFilter(BasePeeweeFilter):
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
            # if end date is before start date, fail validation
            if (len(value) == 2) and (value[0] <= value[1]):
                return True
            else:
                return False
        except ValueError:
            return False        
        

class DateNotBetweenFilter(DateBetweenFilter):
    def apply(self, query, value):
        start, end = value
        return query.filter(~(self.column.between(start, end)))
        
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
        

class DateTimeBetweenFilter(BasePeeweeFilter):
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
        return query.filter(~(self.column.between(start, end)))

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
    

class TimeBetweenFilter(BasePeeweeFilter):
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
        return query.filter(~(self.column.between(start, end)))
        
    def operation(self):
        return lazy_gettext('not between')
        
        
# Base peewee filter field converter
class FilterConverter(filters.BaseFilterConverter):
    strings = (FilterEqual, FilterNotEqual, FilterLike, FilterNotLike, FilterEmpty, FilterInList, FilterNotInList)
    numeric = (FilterEqual, FilterNotEqual, FilterGreater, FilterSmaller, FilterEmpty, FilterInList, FilterNotInList)
    bool = (BooleanEqualFilter, BooleanNotEqualFilter)
    date_filters = (DateEqualFilter, DateNotEqualFilter, DateGreaterFilter, DateSmallerFilter, 
            DateBetweenFilter, DateNotBetweenFilter, FilterEmpty)
    datetime_filters = (DateTimeEqualFilter, DateTimeNotEqualFilter, DateTimeGreaterFilter, 
                DateTimeSmallerFilter, DateTimeBetweenFilter, DateTimeNotBetweenFilter, 
                FilterEmpty)
    time_filters = (TimeEqualFilter, TimeNotEqualFilter, TimeGreaterFilter, TimeSmallerFilter, 
            TimeBetweenFilter, TimeNotBetweenFilter, FilterEmpty)

    def convert(self, type_name, column, name):
        if type_name in self.converters:
            return self.converters[type_name](column, name)

        return None

    @filters.convert('CharField', 'TextField')
    def conv_string(self, column, name):
        return [f(column, name) for f in self.strings]

    @filters.convert('BooleanField')
    def conv_bool(self, column, name):
        return [f(column, name) for f in self.bool]

    @filters.convert('IntegerField', 'DecimalField', 'FloatField',
                     'DoubleField', 'BigIntegerField')
    def conv_int(self, column, name):
        return [f(column, name) for f in self.numeric]

    @filters.convert('DateField')
    def conv_date(self, column, name):
        return [f(column, name) for f in self.date_filters]

    @filters.convert('DateTimeField')
    def conv_datetime(self, column, name):
        return [f(column, name) for f in self.datetime_filters]
    
    @filters.convert('TimeField')
    def conv_time(self, column, name):
        return [f(column, name) for f in self.time_filters]