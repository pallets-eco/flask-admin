from sqlalchemy.ext.associationproxy import _AssociationList

from flask_admin.model.typefmt import BASE_FORMATTERS, EXPORT_FORMATTERS, \
    list_formatter
from sqlalchemy.orm.collections import InstrumentedList


def choice_formatter(view, choice):
    """
        Return label of selected choice
        see https://sqlalchemy-utils.readthedocs.io/

        :param choice:
            sqlalchemy_utils Choice, which has a `code` and a `value`
    """
    return choice.value


def arrow_formatter(view, arrow_time):
    """
        Return human-friendly string of the time relative to now.
        see https://arrow.readthedocs.io/

        :param arrow_time:
            Arrow object for handling datetimes
    """
    return arrow_time.humanize()


def arrow_export_formatter(view, arrow_time):
    """
        Return string representation of Arrow object
        see https://arrow.readthedocs.io/

        :param arrow_time:
            Arrow object for handling datetimes
    """
    return arrow_time.format()


DEFAULT_FORMATTERS = BASE_FORMATTERS.copy()
EXPORT_FORMATTERS = EXPORT_FORMATTERS.copy()

DEFAULT_FORMATTERS.update({
    InstrumentedList: list_formatter,
    _AssociationList: list_formatter,
})
try:
    from sqlalchemy_utils import Choice
    DEFAULT_FORMATTERS[Choice] = choice_formatter
except ImportError:
    pass

try:
    from arrow import Arrow
    DEFAULT_FORMATTERS[Arrow] = arrow_formatter
    EXPORT_FORMATTERS[Arrow] = arrow_export_formatter
except ImportError:
    pass
