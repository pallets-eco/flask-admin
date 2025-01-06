try:
    from flask_babel import Domain

except ImportError:

    def gettext(string, **variables):
        return string if not variables else string % variables

    def ngettext(singular, plural, num, **variables):
        variables.setdefault("num", num)
        return gettext((singular if num == 1 else plural), **variables)

    def lazy_gettext(string, **variables):
        return gettext(string, **variables)

    class Translations:
        """dummy Translations class for WTForms, no translation support"""

        def gettext(self, string):
            return string

        def ngettext(self, singular, plural, n):
            return singular if n == 1 else plural
else:
    from flask_admin import translations

    class CustomDomain(Domain):
        def __init__(self):
            super().__init__(translations.__path__[0], domain="admin")

        @property
        def translation_directories(self):
            view = get_current_view()

            if view is not None:
                dirname = view.admin.translations_path
                if dirname is not None:
                    return [dirname] + super().translation_directories

            return super().translation_directories

    domain = CustomDomain()

    gettext = domain.gettext
    ngettext = domain.ngettext
    lazy_gettext = domain.lazy_gettext

    from wtforms.i18n import messages_path

    wtforms_domain = Domain(messages_path(), domain="wtforms")

    class Translations:  # type: ignore[no-redef]
        """Fixes WTForms translation support and uses wtforms translations"""

        def gettext(self, string):
            t = wtforms_domain.get_translations()
            return t.ugettext(string)

        def ngettext(self, singular, plural, n):
            t = wtforms_domain.get_translations()
            return t.ungettext(singular, plural, n)


# lazy imports
from .helpers import get_current_view
