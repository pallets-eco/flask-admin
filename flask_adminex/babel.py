from flask import _request_ctx_stack


def _gettext(string, **variables):
    return string % variables


def _ngettext(singular, plural, num, **variables):
    return (singular if num == 1 else plural) % variables


def _lazy_gettext(string, **variables):
    return string % variables

# Wrap flask-babel API
try:
    from flask.ext import babel

    def _is_babel_on():
        ctx = _request_ctx_stack.top
        if ctx is None:
            return False

        return hasattr(ctx, 'babel_locale')

    def gettext(string, **variables):
        if not _is_babel_on():
            return _gettext(string, **variables)

        return babel.gettext(string, **variables)

    def ngettext(singular, plural, num, **variables):
        if not _is_babel_on():
            return _ngettext(singular, plural, num, **variables)

        return babel.ngettext(singular, plural, num, **variables)

    def lazy_gettext(string, **variables):
        from speaklater import make_lazy_string
        return make_lazy_string(gettext, string, **variables)

except ImportError:
    gettext = _gettext
    ngettext = _ngettext
    lazy_gettext = _lazy_gettext
