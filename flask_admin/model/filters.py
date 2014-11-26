import time
import datetime

from flask.ext.admin._compat import text_type
from flask.ext.admin.babel import lazy_gettext


class BaseFilter(object):
    """
        Base filter class.
    """
    def __init__(self, name, options=None, data_type=None):
        """
            Constructor.

            :param name:
                Displayed name
            :param options:
                List of fixed options. If provided, will use drop down instead of textbox.
            :param data_type:
                Client-side widget type to use.
        """
        self.name = name
        self.options = options
        self.data_type = data_type

    def get_options(self, view):
        """
            Return list of predefined options.

            Override to customize behavior.

            :param view:
                Associated administrative view class.
        """
        options = self.options

        if options:
            if callable(options):
                options = options()

            return [(v, text_type(n)) for v, n in options]

        return None

    def validate(self, value):
        """
            Validate value.

            If value is valid, returns `True` and `False` otherwise.
            
            :param value:
                Value to validate
        """
        # useful for filters with date conversions, see if conversion in clean() raises ValueError
        try:
            self.clean(value)
            return True
        except ValueError:
            return False

    def clean(self, value):
        """
            Parse value into python format. Occurs before .apply()

            :param value:
                Value to parse
        """
        return value

    def apply(self, query):
        """
            Apply search criteria to the query and return new query.

            :param query:
                Query
        """
        raise NotImplementedError()

    def operation(self):
        """
            Return readable operation name.

            For example: u'equals'
        """
        raise NotImplementedError()

    def __unicode__(self):
        return self.name


# Customized filters
class BaseBooleanFilter(BaseFilter):
    """
        Base boolean filter, uses fixed list of options.
    """
    def __init__(self, name, options=None, data_type=None):
        super(BaseBooleanFilter, self).__init__(name,
                                                (('1', lazy_gettext(u'Yes')),
                                                 ('0', lazy_gettext(u'No'))),
                                                data_type)

    def validate(self, value):
        return value in ('0', '1')


class BaseDateFilter(BaseFilter):
    """
        Base Date filter. Uses client-side date picker control.
    """
    def __init__(self, name, options=None, data_type=None):
        super(BaseDateFilter, self).__init__(name,
                                             options,
                                             data_type='datepicker')
                                             
    def clean(self, value):
        return datetime.datetime.strptime(value, '%Y-%m-%d').date()


class BaseDateTimeFilter(BaseFilter):
    """
        Base DateTime filter. Uses client-side date time picker control.
    """
    def __init__(self, name, options=None, data_type=None):
        super(BaseDateTimeFilter, self).__init__(name,
                                                 options,
                                                 data_type='datetimepicker')
                                                 
    def clean(self, value):
        # datetime filters will not work in SQLite + SQLAlchemy if value not converted to datetime
        return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        
        
class BaseTimeFilter(BaseFilter):
    """
        Base Time filter. Uses client-side time picker control.
    """
    def __init__(self, name, options=None, data_type=None):
        super(BaseTimeFilter, self).__init__(name,
                                             options,
                                             data_type='timepicker')
                                             
    def clean(self, value):
        # time filters will not work in SQLite + SQLAlchemy if value not converted to time
        timetuple = time.strptime(value, '%H:%M:%S')
        return datetime.time(timetuple.tm_hour,
                             timetuple.tm_min,
                             timetuple.tm_sec)
                             

def convert(*args):
    """
        Decorator for field to filter conversion routine.

        See :mod:`flask.ext.admin.contrib.sqla.filters` for usage example.
    """
    def _inner(func):
        func._converter_for = args
        return func
    return _inner


class BaseFilterConverter(object):
    """
        Base filter converter.

        Derive from this class to implement custom field to filter conversion
        logic.
    """
    def __init__(self):
        self.converters = dict()

        for p in dir(self):
            attr = getattr(self, p)

            if hasattr(attr, '_converter_for'):
                for p in attr._converter_for:
                    self.converters[p] = attr
