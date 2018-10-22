from sqlalchemy.ext.associationproxy import _AssociationList

from flask_admin.model.typefmt import BASE_FORMATTERS, EXPORT_FORMATTERS, \
DETAIL_FORMATTERS, list_formatter
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy_utils.types import Choice


def choice_formatter(view, choice):
    """
        Return label of selected choice

        :param choice:
            sqlalchemy_utils Choice, which has a `code` and a `value`
    """
    return choice.value

DEFAULT_FORMATTERS = BASE_FORMATTERS.copy()
EXPORT_FORMATTERS = EXPORT_FORMATTERS.copy()
DETAIL_FORMATTERS = DETAIL_FORMATTERS.copy()

DEFAULT_FORMATTERS.update({
    InstrumentedList: list_formatter,
    _AssociationList: list_formatter,
    Choice: choice_formatter,
})

EXPORT_FORMATTERS.update({
    Choice: choice_formatter,
})

DETAIL_FORMATTERS.update({
    Choice: choice_formatter,
})
