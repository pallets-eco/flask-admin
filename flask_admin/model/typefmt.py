import json
from enum import Enum

from markupsafe import Markup

from flask_admin._compat import text_type
from flask_admin._types import T_FORMATTERS


def null_formatter(view, value, name):
    """
    Return `NULL` as the string for `None` value

    :param value:
        Value to check
    """
    return Markup("<i>NULL</i>")


def empty_formatter(view, value, name):
    """
    Return empty string for `None` value

    :param value:
        Value to check
    """
    return ""


def bool_formatter(view, value, name):
    """
    Return check icon if value is `True` or empty string otherwise.

    :param value:
        Value to check
    """
    glyph = "ok-circle" if value else "minus-sign"
    fa = "fa-check-circle" if value else "fa-minus-circle"
    label = f'{name}: {"true" if value else "false"}'
    return Markup(
        f'<span class="fa {fa} glyphicon glyphicon-{glyph} '
        f'icon-{glyph}" title="{label}"></span>'
    )


def list_formatter(view, values, name) -> str:
    """
    Return string with comma separated values

    :param values:
        Value to check
    """
    return ", ".join(text_type(v) for v in values)


def enum_formatter(view, value, name) -> str:
    """
    Return the name of the enumerated member.

    :param value:
        Value to check
    """
    return value.name


def dict_formatter(view, value, name) -> str:
    """
    Removes unicode entities when displaying dict as string. Also unescapes
    non-ASCII characters stored in the JSON.

    :param value:
        Dict to convert to string
    """
    return json.dumps(value, ensure_ascii=False)


BASE_FORMATTERS: T_FORMATTERS = {
    type(None): empty_formatter,
    bool: bool_formatter,
    list: list_formatter,
    dict: dict_formatter,
}

EXPORT_FORMATTERS: T_FORMATTERS = {
    type(None): empty_formatter,
    list: list_formatter,
    dict: dict_formatter,
}

DETAIL_FORMATTERS: T_FORMATTERS = {
    type(None): empty_formatter,
    list: list_formatter,
    dict: dict_formatter,
}

BASE_FORMATTERS[Enum] = enum_formatter
EXPORT_FORMATTERS[Enum] = enum_formatter
DETAIL_FORMATTERS[Enum] = enum_formatter
