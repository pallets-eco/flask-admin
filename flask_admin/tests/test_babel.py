from unittest import mock

import pytest

from flask_admin import babel
from flask_admin import translations

from . import flask_babel_test_decorator


@flask_babel_test_decorator
@pytest.mark.parametrize("dirname", [None, "foo/bar"])
@mock.patch("flask_admin.babel.get_current_view")
@mock.patch("flask_babel.Domain.get_translations_cache")
@mock.patch("flask_babel._get_current_context")
@mock.patch("flask_babel.get_locale", return_value="qux")
@mock.patch("babel.support.Translations")
def test_translations_path(
    _Translations,
    _get_locale,
    _get_current_context,
    _get_translations_cache,
    _get_current_view,
    dirname,
):
    _get_current_view.return_value.admin.translations_path = dirname
    _get_translations_cache.return_value = {}
    _dirname = dirname or translations.__path__[0]
    domain = babel.CustomDomain()
    assert domain.get_translations() == _Translations.return_value
    calls = [mock.call.load(translations.__path__[0], ["qux"], "admin")]
    if dirname:
        calls = [mock.call.load(dirname, ["qux"], "admin")] + calls
    assert _Translations.method_calls == calls
