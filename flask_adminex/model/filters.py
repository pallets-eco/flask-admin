class BaseFilter(object):
    def __init__(self, name, options=None, data_type=None):
        self.name = name
        self.options = options
        self.data_type = data_type

    def get_options(self, view):
        return self.options

    def validate(self, value):
        return True

    def apply(self, query):
        raise NotImplemented()

    def __unicode__(self):
        return self.name


# Customized filters
class BaseBooleanFilter(BaseFilter):
    def __init__(self, name, data_type=None):
        super(BaseBooleanFilter, self).__init__(name,
                                                (('1', 'Yes'), ('0', 'No')),
                                                data_type)

    def validate(self, value):
        return value == '0' or value == '1'


class BaseDateFilter(BaseFilter):
    def __init__(self, name, options=None):
        super(BaseDateFilter, self).__init__(name,
                                             options,
                                             data_type='datepicker')

    def validate(self, value):
        # TODO: Validation
        return True


class BaseDateTimeFilter(BaseFilter):
    def __init__(self, name, options=None):
        super(BaseDateTimeFilter, self).__init__(name,
                                                 options,
                                                 data_type='datetimepicker')

    def validate(self, value):
        # TODO: Validation
        return True


def convert(*args):
    def _inner(func):
        print args
        func._converter_for = args
        return func
    return _inner


class BaseFilterConverter(object):
    def __init__(self):
        self.converters = dict()

        for p in dir(self):
            attr = getattr(self, p)

            if hasattr(attr, '_converter_for'):
                for p in attr._converter_for:
                    self.converters[p] = attr
