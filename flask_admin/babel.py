try:
    from .helpers import get_current_view

    from flask_babelex import Domain

    from flask_admin import translations

    class CustomDomain(Domain):
        def __init__(self):
            super(CustomDomain, self).__init__(translations.__path__[0], domain='admin')

        def get_translations_path(self, ctx):
            view = get_current_view()

            if view is not None:
                dirname = view.admin.translations_path
                if dirname is not None:
                    return dirname

            return super(CustomDomain, self).get_translations_path(ctx)

    domain = CustomDomain()

    gettext = domain.gettext
    ngettext = domain.ngettext
    lazy_gettext = domain.lazy_gettext
except ImportError:
    from flask_admin._compat import text_type

    def gettext(string, **variables):
        return text_type(string % variables)

    def ngettext(singular, plural, num, **variables):
        return text_type((singular if num == 1 else plural) % variables)

    def lazy_gettext(string, **variables):
        return text_type(gettext(string, **variables))
