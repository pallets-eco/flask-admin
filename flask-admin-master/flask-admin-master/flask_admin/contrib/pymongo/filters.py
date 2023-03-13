import re

from flask_admin.babel import lazy_gettext
from flask_admin.model import filters

from .tools import parse_like_term


class BasePyMongoFilter(filters.BaseFilter):
    """
        Base pymongo filter.
    """
    def __init__(self, column, name, options=None, data_type=None):
        """
            Constructor.

            :param column:
                Document field name
            :param name:
                Display name
            :param options:
                Fixed set of options
            :param data_type:
                Client data type
        """
        super(BasePyMongoFilter, self).__init__(name, options, data_type)

        self.column = column


# Common filters
class FilterEqual(BasePyMongoFilter):
    def apply(self, query, value):
        query.append({self.column: value})
        return query

    def operation(self):
        return lazy_gettext('equals')


class FilterNotEqual(BasePyMongoFilter):
    def apply(self, query, value):
        query.append({self.column: {'$ne': value}})
        return query

    def operation(self):
        return lazy_gettext('not equal')


class FilterLike(BasePyMongoFilter):
    def apply(self, query, value):
        regex = parse_like_term(value)
        query.append({self.column: {'$regex': regex}})
        return query

    def operation(self):
        return lazy_gettext('contains')


class FilterNotLike(BasePyMongoFilter):
    def apply(self, query, value):
        regex = parse_like_term(value)
        query.append({self.column: {'$not': re.compile(regex)}})
        return query

    def operation(self):
        return lazy_gettext('not contains')


class FilterGreater(BasePyMongoFilter):
    def apply(self, query, value):
        try:
            value = float(value)
        except ValueError:
            value = 0
        query.append({self.column: {'$gt': value}})
        return query

    def operation(self):
        return lazy_gettext('greater than')


class FilterSmaller(BasePyMongoFilter):
    def apply(self, query, value):
        try:
            value = float(value)
        except ValueError:
            value = 0
        query.append({self.column: {'$lt': value}})
        return query

    def operation(self):
        return lazy_gettext('smaller than')


# Customized type filters
class BooleanEqualFilter(FilterEqual, filters.BaseBooleanFilter):
    def apply(self, query, value):
        query.append({self.column: value == '1'})
        return query


class BooleanNotEqualFilter(FilterNotEqual, filters.BaseBooleanFilter):
    def apply(self, query, value):
        query.append({self.column: value != '1'})
        return query
