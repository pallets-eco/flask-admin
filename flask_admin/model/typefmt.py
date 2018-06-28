import json

from jinja2 import Markup
from flask_admin._compat import text_type
try:
    from enum import Enum
except ImportError:
    Enum = None


def null_formatter(view, value):
    """
        Return `NULL` as the string for `None` value

        :param value:
            Value to check
    """
    return Markup('<i>NULL</i>')


def empty_formatter(view, value):
    """
        Return empty string for `None` value

        :param value:
            Value to check
    """
    return ''


def bool_formatter(view, value):
    """
        Return check icon if value is `True` or empty string otherwise.

        :param value:
            Value to check
    """
    glyph = 'ok-circle' if value else 'minus-sign'
    fa = 'check-circle' if value else 'minus-circle'
    return Markup('<span class="fa fa-%s glyphicon glyphicon-%s icon-%s"></span>' % (fa, glyph, glyph))


def list_formatter(view, values):
    """
        Return string with comma separated values

        :param values:
            Value to check
    """
    return u', '.join(text_type(v) for v in values)


def enum_formatter(view, value):
    """
        Return the name of the enumerated member.

        :param value:
            Value to check
    """
    return value.name


def dict_formatter(view, value):
    """
        Removes unicode entities when displaying dict as string. Also unescapes
        non-ASCII characters stored in the JSON.

        :param value:
            Dict to convert to string
    """
    return json.dumps(value, ensure_ascii=False)


BASE_FORMATTERS = {
    type(None): empty_formatter,
    bool: bool_formatter,
    list: list_formatter,
    dict: dict_formatter,
}

EXPORT_FORMATTERS = {
    type(None): empty_formatter,
    list: list_formatter,
    dict: dict_formatter,
}

DETAIL_FORMATTERS = {
    type(None): empty_formatter,
    list: list_formatter,
    dict: dict_formatter,
}

if Enum is not None:
    BASE_FORMATTERS[Enum] = enum_formatter
    EXPORT_FORMATTERS[Enum] = enum_formatter
    DETAIL_FORMATTERS[Enum] = enum_formatter
