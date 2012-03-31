from nose.tools import ok_, eq_

from flask import Flask
from flask.ext.adminex import base

from .mock import MockView


def test_baseview_defaults():
    view = MockView()
    eq_(view.name, None)
    eq_(view.category, None)
    eq_(view.endpoint, None)
    eq_(view.url, None)
    eq_(view.static_folder, None)
    eq_(view.admin, None)
    eq_(view.blueprint, None)


def test_base_defaults():
    admin = base.Admin()
    eq_(admin.name, 'Admin')
    eq_(admin.url, '/admin')
    eq_(admin.app, None)
    ok_(admin.index_view is not None)

    # Check if default view was added
    eq_(len(admin._views), 1)
    eq_(admin._views[0], admin.index_view)


def test_base_registration():
    app = Flask(__name__)
    admin = base.Admin(app)

    eq_(admin.app, app)
    ok_(admin.index_view.blueprint is not None)


def test_baseview_registration():
    admin = base.Admin()

    view = MockView()
    bp = view.create_blueprint(admin)

    # Base properties
    eq_(view.admin, admin)
    ok_(view.blueprint is not None)

    # Calculated properties
    eq_(view.endpoint, 'mockview')
    eq_(view.url, '/admin/mockview')
    eq_(view.name, 'Mock View')
    eq_(view._urls, [('/', 'index', ('GET',))])

    # Verify generated blueprint properties
    eq_(bp.name, view.endpoint)
    eq_(bp.url_prefix, view.url)
    eq_(bp.template_folder, 'templates')
    eq_(bp.static_folder, view.static_folder)

    # Verify customizations
    view = MockView(name='Test', endpoint='foobar')
    view.create_blueprint(base.Admin())

    eq_(view.name, 'Test')
    eq_(view.endpoint, 'foobar')
    eq_(view.url, '/admin/foobar')

    view = MockView(url='test')
    view.create_blueprint(base.Admin())
    eq_(view.url, '/admin/test')

    view = MockView(url='/test/test')
    view.create_blueprint(base.Admin())
    eq_(view.url, '/test/test')


def verify_baseview_urls():
    app = Flask(__name__)
    admin = base.Admin(app)

    view = Dummy()
    admin.add_view(view)

    eq_(len(view._urls, 1))
