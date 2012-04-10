from flask.ext.adminex.babel import lazy_gettext


class BaseFilter(object):
    """
        Base filter class.
    """
    def __init__(self, name, options=None, data_type=None):
        """
            Constructor.

            `name`
                Displayed name
            `options`
                List of fixed options. If provided, will use drop down instead of textbox.
            `data_type`
                Client-side widget type to use.
        """
        self.name = name
        self.options = options
        self.data_type = data_type

    def get_options(self, view):
        """
            Return list of predefined options.

            Override to customize behavior.

            `view`
                Associated administrative view class.
        """
        return self.options

    def validate(self, value):
        """
            Validate value.

            If value is valid, returns `True` and `False` otherwise.

            `value`
                Value to validate
        """
        return True

    def clean(self, value):
        """
            Parse value into python format.

            `value`
                Value to parse
        """
        return value

    def apply(self, query):
        """
            Apply search criteria to the query and return new query.

            `query`
                Query
        """
        raise NotImplemented()

    def operation(self):
        """
            Return readable operation name.

            For example: u'equals'
        """
        raise NotImplemented()

    def __unicode__(self):
        return self.name


# Customized filters
class BaseBooleanFilter(BaseFilter):
    """
        Base boolean filter, uses fixed list of options.
    """
    def __init__(self, name, data_type=None):
        super(BaseBooleanFilter, self).__init__(name,
                                                (('1', lazy_gettext('Yes')),
                                                 ('0', lazy_gettext('No'))),
                                                data_type)

    def validate(self, value):
        return value == '0' or value == '1'


class BaseDateFilter(BaseFilter):
    """
        Base Date filter. Uses client-side date picker control.
    """
    def __init__(self, name, options=None):
        super(BaseDateFilter, self).__init__(name,
                                             options,
                                             data_type='datepicker')

    def validate(self, value):
        # TODO: Validation
        return True


class BaseDateTimeFilter(BaseFilter):
    """
        Base DateTime filter. Uses client-side date picker control.
    """
    def __init__(self, name, options=None):
        super(BaseDateTimeFilter, self).__init__(name,
                                                 options,
                                                 data_type='datetimepicker')

    def validate(self, value):
        # TODO: Validation
        return True


def convert(*args):
    """
        Decorator for field to filter conversion routine.

        See :mod:`flask.ext.adminex.ext.sqlamodel.filters` for usage example.
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
