from mongoengine.base import BaseList

from flask.ext.admin.model.typefmt import DEFAULT_FORMATTERS


def mongoengine_list_formatter(values):
    """
        Return string with comma separated values

        :param values:
            Value to check
    """
    return u', '.join(unicode(v) for v in values)


MONGOENGINE_FORMATTERS = dict(DEFAULT_FORMATTERS)
MONGOENGINE_FORMATTERS.update({
        BaseList: mongoengine_list_formatter
    })
