import os

import pytest

from flask import Flask, request, abort, url_for
from flask.views import MethodView

from flask_admin import base


class MockView(base.BaseView):
    # Various properties
    allow_call = True
    allow_access = True
    visible = True

    @base.expose('/')
    def index(self):
        return 'Success!'

    @base.expose('/test/')
    def test(self):
        return self.render('mock.html')

    def _handle_view(self, name, **kwargs):
        if self.allow_call:
            return super(MockView, self)._handle_view(name, **kwargs)
        else:
            return 'Failure!'

    def is_accessible(self):
        if self.allow_access:
            return super(MockView, self).is_accessible()

        return False

    def is_visible(self):
        if self.visible:
            return super(MockView, self).is_visible()

        return False


class MockMethodView(base.BaseView):
    @base.expose('/')
    def index(self):
        return 'Success!'

    @base.expose_plugview('/_api/1')
    class API1(MethodView):
        def get(self, cls):
            return cls.render('method.html', request=request, name='API1')

        def post(self, cls):
            return cls.render('method.html', request=request, name='API1')

        def put(self, cls):
            return cls.render('method.html', request=request, name='API1')

        def delete(self, cls):
            return cls.render('method.html', request=request, name='API1')

    @base.expose_plugview('/_api/2')
    class API2(MethodView):
        def get(self, cls):
            return cls.render('method.html', request=request, name='API2')

        def post(self, cls):
            return cls.render('method.html', request=request, name='API2')

    @base.expose_plugview('/_api/3')
    @base.expose_plugview('/_api/4')
    class DoubleExpose(MethodView):
        def get(self, cls):
            return cls.render('method.html', request=request, name='API3')


def test_baseview_defaults():
    view = MockView()
    assert view.name is None
    assert view.category is None
    assert view.endpoint == 'mockview'
    assert view.url is None
    assert view.static_folder is None
    assert view.admin is None
    assert view.blueprint is None


def test_base_defaults():
    admin = base.Admin()
    assert admin.name == 'Admin'
    assert admin.url == '/admin'
    assert admin.endpoint == 'admin'
    assert admin.app is None
    assert admin.index_view is not None
    assert admin.index_view._template == 'admin/index.html'

    # Check if default view was added
    assert len(admin._views) == 1
    assert admin._views[0] == admin.index_view


def test_custom_index_view():
    view = base.AdminIndexView(name='a', category='b', endpoint='c',
                               url='/d', template='e')
    admin = base.Admin(index_view=view)

    assert admin.endpoint == 'c'
    assert admin.url == '/d'
    assert admin.index_view is view
    assert view.name == 'a'
    assert view.category == 'b'
    assert view._template == 'e'

    # Check if view was added
    assert len(admin._views) == 1
    assert admin._views[0] == view


def test_custom_index_view_in_init_app():
    view = base.AdminIndexView(name='a', category='b', endpoint='c',
                               url='/d', template='e')
    app = Flask(__name__)
    admin = base.Admin()
    admin.init_app(app, index_view=view)

    assert admin.endpoint == 'c'
    assert admin.url == '/d'
    assert admin.index_view is view
    assert view.name == 'a'
    assert view.category == 'b'
    assert view._template == 'e'

    # Check if view was added
    assert len(admin._views) == 1
    assert admin._views[0] == view


def test_base_registration():
    app = Flask(__name__)
    admin = base.Admin(app)

    assert admin.app == app
    assert admin.index_view.blueprint is not None


def test_admin_customizations():
    app = Flask(__name__)
    admin = base.Admin(app, name='Test', url='/foobar', static_url_path='/static/my/admin')
    assert admin.name == 'Test'
    assert admin.url == '/foobar'
    assert admin.index_view.blueprint.static_url_path == '/static/my/admin'

    client = app.test_client()
    rv = client.get('/foobar/')
    assert rv.status_code == 200

    # test custom static_url_path
    with app.test_request_context('/'):
        rv = client.get(url_for('admin.static', filename='bootstrap/bootstrap2/css/bootstrap.css'))
    assert rv.status_code == 200


def test_baseview_registration():
    admin = base.Admin()

    view = MockView()
    bp = view.create_blueprint(admin)

    # Base properties
    assert view.admin == admin
    assert view.blueprint is not None

    # Calculated properties
    assert view.endpoint == 'mockview'
    assert view.url == '/admin/mockview'
    assert view.name == 'Mock View'

    # Verify generated blueprint properties
    assert bp.name == view.endpoint
    assert bp.url_prefix == view.url
    assert bp.template_folder == os.path.join('templates', 'bootstrap2')
    assert bp.static_folder == view.static_folder

    # Verify customizations
    view = MockView(name='Test', endpoint='foobar')
    view.create_blueprint(base.Admin())

    assert view.name == 'Test'
    assert view.endpoint == 'foobar'
    assert view.url == '/admin/foobar'

    view = MockView(url='test')
    view.create_blueprint(base.Admin())
    assert view.url == '/admin/test'

    view = MockView(url='/test/test')
    view.create_blueprint(base.Admin())
    assert view.url == '/test/test'

    view = MockView(endpoint='test')
    view.create_blueprint(base.Admin(url='/'))
    assert view.url == '/test'

    view = MockView(static_url_path='/static/my/test')
    view.create_blueprint(base.Admin())
    assert view.blueprint.static_url_path == '/static/my/test'


def test_baseview_urls():
    app = Flask(__name__)
    admin = base.Admin(app)

    view = MockView()
    admin.add_view(view)

    assert len(view._urls) == 2


def test_add_views():
    app = Flask(__name__)
    admin = base.Admin(app)

    admin.add_views(MockView(endpoint='test1'), MockView(endpoint='test2'))

    assert len(admin.menu()) == 3


def test_add_category():
    app = Flask(__name__)
    admin = base.Admin(app)

    admin.add_category('Category1', 'class-name', 'icon-type', 'icon-value')
    admin.add_view(MockView(name='Test 1', endpoint='test1', category='Category1'))
    admin.add_view(MockView(name='Test 2', endpoint='test2', category='Category2'))

    assert len(admin.menu()) == 3

    # Test 1 should be underneath Category1
    assert admin.menu()[1].name == 'Category1'
    assert admin.menu()[1].get_class_name() == 'class-name'
    assert admin.menu()[1].get_icon_type() == 'icon-type'
    assert admin.menu()[1].get_icon_value() == 'icon-value'
    assert len(admin.menu()[1].get_children()) == 1
    assert admin.menu()[1].get_children()[0].name == 'Test 1'

    # Test 2 should be underneath Category2
    assert admin.menu()[2].name == 'Category2'
    assert admin.menu()[2].get_class_name() is None
    assert admin.menu()[2].get_icon_type() is None
    assert admin.menu()[2].get_icon_value() is None
    assert len(admin.menu()[2].get_children()) == 1
    assert admin.menu()[2].get_children()[0].name == 'Test 2'


@pytest.mark.xfail(raises=Exception)
def test_no_default():
    app = Flask(__name__)
    admin = base.Admin(app)
    admin.add_view(base.BaseView())


def test_call():
    app = Flask(__name__)
    admin = base.Admin(app)
    view = MockView()
    admin.add_view(view)
    client = app.test_client()

    rv = client.get('/admin/')
    assert rv.status_code == 200

    rv = client.get('/admin/mockview/')
    assert rv.data == b'Success!'

    rv = client.get('/admin/mockview/test/')
    assert rv.data == b'Success!'

    # Check authentication failure
    view.allow_call = False
    rv = client.get('/admin/mockview/')
    assert rv.data == b'Failure!'


def test_permissions():
    app = Flask(__name__)
    admin = base.Admin(app)
    view = MockView()
    admin.add_view(view)
    client = app.test_client()

    view.allow_access = False

    rv = client.get('/admin/mockview/')
    assert rv.status_code == 403


def test_inaccessible_callback():
    app = Flask(__name__)
    admin = base.Admin(app)
    view = MockView()
    admin.add_view(view)
    client = app.test_client()

    view.allow_access = False
    view.inaccessible_callback = lambda *args, **kwargs: abort(418)

    rv = client.get('/admin/mockview/')
    assert rv.status_code == 418


def get_visibility():
    app = Flask(__name__)
    admin = base.Admin(app)

    view = MockView(name='TestMenuItem')
    view.visible = False

    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/mockview/')
    assert 'TestMenuItem' not in rv.data.decode('utf-8')


def test_submenu():
    app = Flask(__name__)
    admin = base.Admin(app)
    admin.add_view(MockView(name='Test 1', category='Test', endpoint='test1'))

    # Second view is not normally accessible
    view = MockView(name='Test 2', category='Test', endpoint='test2')
    view.allow_access = False
    admin.add_view(view)

    assert 'Test' in admin._menu_categories
    assert len(admin._menu) == 2
    assert admin._menu[1].name == 'Test'
    assert len(admin._menu[1]._children) == 2

    # Categories don't have URLs
    assert admin._menu[1].get_url() is None

    # Categories are only accessible if there is at least one accessible child
    assert admin._menu[1].is_accessible()

    children = admin._menu[1].get_children()
    assert len(children) == 1

    assert children[0].is_accessible()


def test_delayed_init():
    app = Flask(__name__)
    admin = base.Admin()
    admin.add_view(MockView())
    admin.init_app(app)

    client = app.test_client()

    rv = client.get('/admin/mockview/')
    assert rv.data == b'Success!'


def test_multi_instances_init():
    app = Flask(__name__)
    _ = base.Admin(app)

    class ManageIndex(base.AdminIndexView):
        pass

    _ = base.Admin(app, index_view=ManageIndex(url='/manage', endpoint='manage'))  # noqa: F841


@pytest.mark.xfail(raises=Exception)
def test_double_init():
    app = Flask(__name__)
    admin = base.Admin(app)
    admin.init_app(app)


def test_nested_flask_views():
    app = Flask(__name__)
    admin = base.Admin(app)

    view = MockMethodView()
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/mockmethodview/_api/1')
    print('"', rv.data, '"')
    assert rv.data == b'GET - API1'
    rv = client.put('/admin/mockmethodview/_api/1')
    assert rv.data == b'PUT - API1'
    rv = client.post('/admin/mockmethodview/_api/1')
    assert rv.data == b'POST - API1'
    rv = client.delete('/admin/mockmethodview/_api/1')
    assert rv.data == b'DELETE - API1'

    rv = client.get('/admin/mockmethodview/_api/2')
    assert rv.data == b'GET - API2'
    rv = client.post('/admin/mockmethodview/_api/2')
    assert rv.data == b'POST - API2'
    rv = client.delete('/admin/mockmethodview/_api/2')
    assert rv.status_code == 405
    rv = client.put('/admin/mockmethodview/_api/2')
    assert rv.status_code == 405

    rv = client.get('/admin/mockmethodview/_api/3')
    assert rv.data == b'GET - API3'
    rv = client.get('/admin/mockmethodview/_api/4')
    assert rv.data == b'GET - API3'


def test_root_mount():
    app = Flask(__name__)
    admin = base.Admin(app, url='/')
    admin.add_view(MockView())

    client = app.test_client()
    rv = client.get('/mockview/')
    assert rv.data == b'Success!'

    # test static files when url='/'
    with app.test_request_context('/'):
        rv = client.get(url_for('admin.static', filename='bootstrap/bootstrap2/css/bootstrap.css'))
    assert rv.status_code == 200


def test_menu_links():
    app = Flask(__name__)
    admin = base.Admin(app)
    admin.add_link(base.MenuLink('TestMenuLink1', endpoint='.index'))
    admin.add_link(base.MenuLink('TestMenuLink2', url='http://python.org/'))

    client = app.test_client()
    rv = client.get('/admin/')

    data = rv.data.decode('utf-8')
    assert 'TestMenuLink1' in data
    assert 'TestMenuLink2' in data


def test_add_links():
    app = Flask(__name__)
    admin = base.Admin(app)
    admin.add_links(base.MenuLink('TestMenuLink1', endpoint='.index'),
                    base.MenuLink('TestMenuLink2', url='http://python.org/'))

    client = app.test_client()
    rv = client.get('/admin/')

    data = rv.data.decode('utf-8')
    assert 'TestMenuLink1' in data
    assert 'TestMenuLink2' in data


def check_class_name():
    view = MockView()
    assert view.name == 'Mock View'


def check_endpoint():
    class CustomView(MockView):
        def _get_endpoint(self, endpoint):
            return 'admin.' + super(CustomView, self)._get_endpoint(endpoint)

    view = CustomView()
    assert view.endpoint == 'admin.customview'
