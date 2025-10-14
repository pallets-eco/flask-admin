from bson.errors import InvalidId
from bson.objectid import ObjectId
from mongoengine.queryset import Q

from flask_admin.babel import lazy_gettext
from flask_admin.model import filters

from .tools import parse_like_term


class BaseMongoEngineFilter(filters.BaseFilter):
    """
    Base MongoEngine filter.
    """

    def __init__(self, column: str, name, options=None, data_type=None):
        """
        Constructor.

        :param column:
            Model field name
        :param name:
            Display name
        :param options:
            Fixed set of options. If provided, will use drop down instead of textbox.
        :param data_type:
            Client data type
        """
        super().__init__(name, options, data_type)

        self.column = column


# Common filters
class FilterEqual(BaseMongoEngineFilter):
    def apply(self, query, value):
        flt = {str(self.column): value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext("equals")


class FilterNotEqual(BaseMongoEngineFilter):
    def apply(self, query, value):
        flt = {f"{self.column}__ne": value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext("not equal")


class FilterLike(BaseMongoEngineFilter):
    def apply(self, query, value):
        term, data = parse_like_term(value)
        flt = {f"{self.column}__{term}": data}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext("contains")


class FilterNotLike(BaseMongoEngineFilter):
    def apply(self, query, value):
        term, data = parse_like_term(value)
        flt = {f"{self.column}__not__{term}": data}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext("not contains")


class FilterGreater(BaseMongoEngineFilter):
    def apply(self, query, value):
        flt = {f"{self.column}__gt": value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext("greater than")


class FilterSmaller(BaseMongoEngineFilter):
    def apply(self, query, value):
        flt = {f"{self.column}__lt": value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext("smaller than")


class FilterEmpty(BaseMongoEngineFilter, filters.BaseBooleanFilter):
    def apply(self, query, value):
        if value == "1":
            flt = {str(self.column): None}
        else:
            flt = {f"{self.column}__ne": None}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext("empty")


class FilterInList(BaseMongoEngineFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super().__init__(column, name, options, data_type="select2-tags")

    def clean(self, value):
        return [v.strip() for v in value.split(",") if v.strip()]

    def apply(self, query, value):
        flt = {f"{self.column}__in": value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext("in list")


class FilterNotInList(FilterInList):
    def apply(self, query, value):
        flt = {f"{self.column}__nin": value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext("not in list")


# Customized type filters
class BooleanEqualFilter(FilterEqual, filters.BaseBooleanFilter):
    def apply(self, query, value):
        flt = {str(self.column): value == "1"}
        return query.filter(**flt)


class BooleanNotEqualFilter(FilterNotEqual, filters.BaseBooleanFilter):
    def apply(self, query, value):
        flt = {str(self.column): value != "1"}
        return query.filter(**flt)


class IntEqualFilter(FilterEqual, filters.BaseIntFilter):
    pass


class IntNotEqualFilter(FilterNotEqual, filters.BaseIntFilter):
    pass


class IntGreaterFilter(FilterGreater, filters.BaseIntFilter):
    pass


class IntSmallerFilter(FilterSmaller, filters.BaseIntFilter):
    pass


class IntInListFilter(filters.BaseIntListFilter, FilterInList):
    pass


class IntNotInListFilter(filters.BaseIntListFilter, FilterNotInList):
    pass


class FloatEqualFilter(FilterEqual, filters.BaseFloatFilter):
    pass


class FloatNotEqualFilter(FilterNotEqual, filters.BaseFloatFilter):
    pass


class FloatGreaterFilter(FilterGreater, filters.BaseFloatFilter):
    pass


class FloatSmallerFilter(FilterSmaller, filters.BaseFloatFilter):
    pass


class FloatInListFilter(filters.BaseFloatListFilter, FilterInList):
    pass


class FloatNotInListFilter(filters.BaseFloatListFilter, FilterNotInList):
    pass


class DateTimeEqualFilter(FilterEqual, filters.BaseDateTimeFilter):
    pass


class DateTimeNotEqualFilter(FilterNotEqual, filters.BaseDateTimeFilter):
    pass


class DateTimeGreaterFilter(FilterGreater, filters.BaseDateTimeFilter):
    pass


class DateTimeSmallerFilter(FilterSmaller, filters.BaseDateTimeFilter):
    pass


class DateTimeBetweenFilter(BaseMongoEngineFilter, filters.BaseDateTimeBetweenFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super().__init__(column, name, options, data_type="datetimerangepicker")

    def apply(self, query, value):
        start, end = value
        flt = {f"{self.column}__gte": start, f"{self.column}__lte": end}
        return query.filter(**flt)


class DateTimeNotBetweenFilter(DateTimeBetweenFilter):
    def apply(self, query, value):
        start, end = value
        return query.filter(
            Q(**{f"{self.column}__not__gte": start})
            | Q(**{f"{self.column}__not__lte": end})
        )

    def operation(self):
        return lazy_gettext("not between")


class ReferenceObjectIdFilter(BaseMongoEngineFilter):
    def validate(self, value):
        """
        Validate value.
        If value is valid, returns `True` and `False` otherwise.
        :param value:
            Value to validate
        """
        try:
            self.clean(value)
            return True
        except InvalidId:
            return False

    def clean(self, value):
        return ObjectId(value.strip())

    def apply(self, query, value):
        flt = {str(self.column): value}
        return query.filter(**flt)

    def operation(self):
        return lazy_gettext("ObjectId equals")


# Base MongoEngine filter field converter
class FilterConverter(filters.BaseFilterConverter):
    strings = (
        FilterLike,
        FilterNotLike,
        FilterEqual,
        FilterNotEqual,
        FilterEmpty,
        FilterInList,
        FilterNotInList,
    )
    int_filters = (
        IntEqualFilter,
        IntNotEqualFilter,
        IntGreaterFilter,
        IntSmallerFilter,
        FilterEmpty,
        IntInListFilter,
        IntNotInListFilter,
    )
    float_filters = (
        FloatEqualFilter,
        FloatNotEqualFilter,
        FloatGreaterFilter,
        FloatSmallerFilter,
        FilterEmpty,
        FloatInListFilter,
        FloatNotInListFilter,
    )
    bool_filters = (BooleanEqualFilter, BooleanNotEqualFilter)
    datetime_filters = (
        DateTimeEqualFilter,
        DateTimeNotEqualFilter,
        DateTimeGreaterFilter,
        DateTimeSmallerFilter,
        DateTimeBetweenFilter,
        DateTimeNotBetweenFilter,
        FilterEmpty,
    )
    reference_filters = (ReferenceObjectIdFilter,)

    def convert(self, type_name, column, name):
        filter_name = type_name.lower()

        if filter_name in self.converters:
            return self.converters[filter_name](column, name)

        return None

    @filters.convert("StringField", "EmailField", "URLField")
    def conv_string(self, column, name):
        return [f(column, name) for f in self.strings]

    @filters.convert("BooleanField")
    def conv_bool(self, column, name):
        return [f(column, name) for f in self.bool_filters]

    @filters.convert("IntField", "LongField")
    def conv_int(self, column, name):
        return [f(column, name) for f in self.int_filters]

    @filters.convert("DecimalField", "FloatField")
    def conv_float(self, column, name):
        return [f(column, name) for f in self.float_filters]

    @filters.convert("DateTimeField", "ComplexDateTimeField")
    def conv_datetime(self, column, name):
        return [f(column, name) for f in self.datetime_filters]

    @filters.convert("ReferenceField")
    def conv_reference(self, column, name):
        return [f(column, name) for f in self.reference_filters]
