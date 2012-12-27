from jinja2 import Markup


def null_formatter(value):
    """
        Return `NULL` as the string for `None` value

        :param value:
            Value to check
    """
    return Markup('<i>NULL</i>')


def empty_formatter(value):
    """
        Return empty string for `None` value

        :param value:
            Value to check
    """
    return ''


def bool_formatter(value):
    """
        Return check icon if value is `True` or empty string otherwise.

        :param value:
            Value to check
    """
    return Markup('<i class="icon-ok"></i>' if value else '')


def list_formatter(values):
    """
        Return string with comma separated values

        :param values:
            Value to check
    """
    return u', '.join(unicode(v) for v in values)


BASE_FORMATTERS = {
    type(None): empty_formatter,
    bool: bool_formatter,
    list: list_formatter,
}
