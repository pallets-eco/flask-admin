try:
    from flask.ext.babel import Domain

    from flask.ext.adminex import translations
    domain = Domain(translations.__path__[0], domain='admin')

    gettext = domain.gettext
    ngettext = domain.ngettext
    lazy_gettext = domain.lazy_gettext
except ImportError:
    def gettext(string, **variables):
        return string % variables

    def ngettext(singular, plural, num, **variables):
        return (singular if num == 1 else plural) % variables

    def lazy_gettext(string, **variables):
        return gettext(string, **variables)
