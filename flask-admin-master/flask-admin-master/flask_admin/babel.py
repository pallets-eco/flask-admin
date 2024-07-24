try:
    try:
        from flask_babelex import Domain
    except ImportError:
        from flask_babel import Domain

except ImportError:
    def gettext(string, **variables):
        return string % variables

    def ngettext(singular, plural, num, **variables):
        variables.setdefault('num', num)
        return (singular if num == 1 else plural) % variables

    def lazy_gettext(string, **variables):
        return gettext(string, **variables)

    class Translations(object):
        ''' dummy Translations class for WTForms, no translation support '''
        def gettext(self, string):
            return string

        def ngettext(self, singular, plural, n):
            return singular if n == 1 else plural
else:
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

    try:
        from wtforms.i18n import messages_path
    except ImportError:
        from wtforms.ext.i18n.utils import messages_path

    wtforms_domain = Domain(messages_path(), domain='wtforms')

    class Translations(object):
        ''' Fixes WTForms translation support and uses wtforms translations '''
        def gettext(self, string):
            t = wtforms_domain.get_translations()
            return t.ugettext(string)

        def ngettext(self, singular, plural, n):
            t = wtforms_domain.get_translations()
            return t.ungettext(singular, plural, n)


# lazy imports
from .helpers import get_current_view
