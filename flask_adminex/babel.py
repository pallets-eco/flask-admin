from __future__ import absolute_import

import os.path as op
from flask import _request_ctx_stack


try:
    from babel import support, Locale
    from speaklater import make_lazy_string

    class Namespace(object):
        def __init__(self, dirname=None, namespace='', default_locale='en'):
            self.dirname = dirname
            self.namespace = namespace
            self.default_locale = Locale.parse(default_locale)

        def _get_locale(self):
            ctx = _request_ctx_stack.top
            if ctx is None:
                return None

            locale = getattr(ctx, 'admin_locale', None)
            if locale is None:
                admin = ctx.app.extensions['admin']

                if admin.locale_selector_func:
                    locale_name = admin.locale_selector_func()

                    if locale_name:
                        locale = Locale.parse(locale_name)
                    else:
                        locale = self.default_locale
                else:
                    locale = self.default_locale

                ctx.admin_locale = locale

            return locale

        def _get_translations(self):
            ctx = _request_ctx_stack.top
            if ctx is None:
                return None

            attr = 'admin_trans_' + self.namespace

            translations = getattr(ctx, attr, None)
            if translations is None:
                dirname = self.dirname or op.join(ctx.app.root_path, 'translations')
                translations = support.Translations.load(dirname,
                                                         [self._get_locale()],
                                                         domain=self.namespace)
                setattr(ctx, attr, translations)

            return translations

        def gettext(self, string, **variables):
            translations = self._get_translations()
            return translations.ugettext(string, **variables)

        def ngettext(self, singular, plural, num, **variables):
            translations = self._get_translations()
            return translations.ungettext(singular, plural, num, **variables)

        def lazy_gettext(self, string, **variables):
            return make_lazy_string(self.gettext, string, **variables)

except ImportError, ex:
    class DummyNamespace(object):
        def __init__(self, dirname=None, namespace='admin'):
            self.dirname = dirname
            self.namespace = namespace

        def gettext(self, string, **variables):
            return string % variables

        def ngettext(self, singular, plural, num, **variables):
            return (singular if num == 1 else plural) % variables

        def lazy_gettext(self, string, **variables):
            return string % variables

    Namespace = DummyNamespace

# Create default namespace pointing to the flask-adminex localization directory
ns = Namespace(namespace='admin')

# Create shortcuts for default namespace
gettext = ns.gettext
ngettext = ns.ngettext
lazy_gettext = ns.lazy_gettext
