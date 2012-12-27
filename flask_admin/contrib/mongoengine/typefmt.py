from mongoengine.base import BaseList
from flask.ext.admin.model.typefmt import DEFAULT_FORMATTERS


def list_formatter(values):
    """
        Return string with comma separated values

        :param values:
            Value to check
    """
    return u', '.join(unicode(v) for v in values)


DEFAULT_FORMATTERS = DEFAULT_FORMATTERS.copy()
DEFAULT_FORMATTERS.update({
    BaseList: list_formatter
})
