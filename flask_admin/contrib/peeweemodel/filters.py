from flask.ext.admin.babel import gettext

from flask.ext.admin.model import filters

from peewee import Q


def parse_like_term(term):
    if term.startswith('^'):
        stmt = '%s%%' % term[1:]
    elif term.startswith('='):
        stmt = term[1:]
    else:
        stmt = '%%%s%%' % term

    return stmt


class BasePeeweeFilter(filters.BaseFilter):
    """
        Base SQLAlchemy filter.
    """
    def __init__(self, column, name, options=None, data_type=None):
        """
            Constructor.

            `column`
                Model field
            `name`
                Display name
            `options`
                Fixed set of options
            `data_type`
                Client data type
        """
        super(BasePeeweeFilter, self).__init__(name, options, data_type)

        self.column = column


# Common filters
class FilterEqual(BasePeeweeFilter):
    def apply(self, query, value):
        stmt = '%s__eq' % self.column.name
        return query.where(**{stmt: value})

    def operation(self):
        return gettext('equals')


class FilterNotEqual(BasePeeweeFilter):
    def apply(self, query, value):
        stmt = '%s__neq' % self.column.name
        return query.where(**{stmt: value})

    def operation(self):
        return gettext('not equal')


class FilterLike(BasePeeweeFilter):
    def apply(self, query, value):
        stmt = '%s__icontains' % self.column.name
        val = parse_like_term(value)
        return query.where(**{stmt: val})

    def operation(self):
        return gettext('contains')


class FilterNotLike(BasePeeweeFilter):
    def apply(self, query, value):
        stmt = '%s__icontains' % self.column.name
        val = parse_like_term(value)
        node = ~Q(**{stmt: val})
        return query.where(node)

    def operation(self):
        return gettext('not contains')


class FilterGreater(BasePeeweeFilter):
    def apply(self, query, value):
        stmt = '%s__gt' % self.column.name
        return query.where(**{stmt: value})

    def operation(self):
        return gettext('greater than')


class FilterSmaller(BasePeeweeFilter):
    def apply(self, query, value):
        stmt = '%s__lt' % self.column.name
        return query.where(**{stmt: value})

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
        print type_name, column, name

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
