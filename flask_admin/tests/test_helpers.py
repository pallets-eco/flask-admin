import flask

from flask_admin import helpers


def test_is_safe_url():
    app = flask.Flask(__name__)

    with app.test_request_context('http://127.0.0.1/admin/car/edit/'):
        assert helpers.is_safe_url('http://127.0.0.1/admin/car/')
        assert helpers.is_safe_url('https://127.0.0.1/admin/car/')
        assert helpers.is_safe_url('/admin/car/')
        assert helpers.is_safe_url('admin/car/')
        assert helpers.is_safe_url('http////www.google.com')

        assert not helpers.is_safe_url('http://127.0.0.2/admin/car/')
        assert not helpers.is_safe_url(' javascript:alert(document.domain)')
        assert not helpers.is_safe_url('javascript:alert(document.domain)')
        assert not helpers.is_safe_url('javascrip\nt:alert(document.domain)')
        assert not helpers.is_safe_url(r'\\www.google.com')
        assert not helpers.is_safe_url(r'\\/www.google.com')
        assert not helpers.is_safe_url('/////www.google.com')
        assert not helpers.is_safe_url('http:///www.google.com')
        assert not helpers.is_safe_url('https:////www.google.com')
