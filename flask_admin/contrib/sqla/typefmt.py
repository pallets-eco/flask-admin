import sqlalchemy_utils
from sqlalchemy.ext.associationproxy import _AssociationList
from sqlalchemy.orm.collections import InstrumentedList

from flask_admin._types import T_ARROW
from flask_admin._types import T_MODEL_VIEW
from flask_admin.model.typefmt import BASE_FORMATTERS
from flask_admin.model.typefmt import EXPORT_FORMATTERS
from flask_admin.model.typefmt import list_formatter


def choice_formatter(
    view: T_MODEL_VIEW, choice: sqlalchemy_utils.Choice, name: str
) -> str:
    """
    Return label of selected choice
    see https://sqlalchemy-utils.readthedocs.io/

    :param choice:
        sqlalchemy_utils Choice, which has a `code` and a `value`
    """
    return choice.value


def arrow_formatter(view: T_MODEL_VIEW, arrow_time: T_ARROW, name: str) -> str:
    """
    Return human-friendly string of the time relative to now.
    see https://arrow.readthedocs.io/

    :param arrow_time:
        Arrow object for handling datetimes
    """
    return arrow_time.humanize()


def arrow_export_formatter(view: T_MODEL_VIEW, arrow_time: T_ARROW, name: str) -> str:
    """
    Return string representation of Arrow object
    see https://arrow.readthedocs.io/

    :param arrow_time:
        Arrow object for handling datetimes
    """
    return arrow_time.format()


DEFAULT_FORMATTERS = BASE_FORMATTERS.copy()
EXPORT_FORMATTERS = EXPORT_FORMATTERS.copy()

DEFAULT_FORMATTERS.update(
    {
        InstrumentedList: list_formatter,
        _AssociationList: list_formatter,
    }
)
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
