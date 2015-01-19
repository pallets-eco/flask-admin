import wtforms

from nose.tools import eq_, ok_

from flask import Flask, session

from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.test import Client

from wtforms import fields

from flask.ext.admin import Admin, form
from flask.ext.admin._compat import iteritems, itervalues
from flask.ext.admin.model import base, filters


def wtforms2_and_up(func):
    """Decorator for skipping test if wtforms <2
    """
    if int(wtforms.__version__[0]) < 2:
        func.__test__ = False
    return func


class Model(object):
    def __init__(self, id=None, c1=1, c2=2, c3=3):
        self.id = id
        self.col1 = c1
        self.col2 = c2
        self.col3 = c3


class Form(form.BaseForm):
    col1 = fields.StringField()
    col2 = fields.StringField()
    col3 = fields.StringField()


class SimpleFilter(filters.BaseFilter):
    def apply(self, query):
        query._applied = True
        return query

    def operation(self):
        return 'test'


class MockModelView(base.BaseModelView):
    def __init__(self, model, name=None, category=None, endpoint=None, url=None,
                 **kwargs):
        # Allow to set any attributes from parameters
        for k, v in iteritems(kwargs):
            setattr(self, k, v)

        super(MockModelView, self).__init__(model, name, category, endpoint, url)

        self.created_models = []
        self.updated_models = []
        self.deleted_models = []

        self.search_arguments = []

        self.all_models = {1: Model(1),
                           2: Model(2)}
        self.last_id = 3

    # Scaffolding
    def get_pk_value(self, model):
        return model.id

    def scaffold_list_columns(self):
        columns = ['col1', 'col2', 'col3']

        if self.column_exclude_list:
            return filter(lambda x: x not in self.column_exclude_list, columns)

        return columns

    def init_search(self):
        return bool(self.column_searchable_list)

    def scaffold_filters(self, name):
        return [SimpleFilter(name)]

    def scaffold_sortable_columns(self):
        return ['col1', 'col2', 'col3']

    def scaffold_form(self):
        return Form

    # Data
    def get_list(self, page, sort_field, sort_desc, search, filters):
        self.search_arguments.append((page, sort_field, sort_desc, search, filters))
        return len(self.all_models), itervalues(self.all_models)

    def get_one(self, id):
        return self.all_models.get(int(id))

    def create_model(self, form):
        model = Model(self.last_id)
        self.last_id += 1

        form.populate_obj(model)
        self.created_models.append(model)
        self.all_models[model.id] = model

        return True

    def update_model(self, form, model):
        form.populate_obj(model)
        self.updated_models.append(model)
        return True

    def delete_model(self, model):
        self.deleted_models.append(model)
        return True


def setup():
    app = Flask(__name__)
    app.config['CSRF_ENABLED'] = False
    app.secret_key = '1'
    admin = Admin(app)

    return app, admin


def test_mockview():
    app, admin = setup()

    view = MockModelView(Model)
    admin.add_view(view)

    eq_(view.model, Model)

    eq_(view.name, 'Model')
    eq_(view.endpoint, 'model')

    # Verify scaffolding
    eq_(view._sortable_columns, ['col1', 'col2', 'col3'])
    eq_(view._create_form_class, Form)
    eq_(view._edit_form_class, Form)
    eq_(view._search_supported, False)
    eq_(view._filters, None)

    client = app.test_client()

    # Make model view requests
    rv = client.get('/admin/model/')
    eq_(rv.status_code, 200)

    # Test model creation view
    rv = client.get('/admin/model/new/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/model/new/',
                     data=dict(col1='test1', col2='test2', col3='test3'))
    eq_(rv.status_code, 302)
    eq_(len(view.created_models), 1)

    model = view.created_models.pop()
    eq_(model.id, 3)
    eq_(model.col1, 'test1')
    eq_(model.col2, 'test2')
    eq_(model.col3, 'test3')

    # Try model edit view
    rv = client.get('/admin/model/edit/?id=3')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test1' in data)

    rv = client.post('/admin/model/edit/?id=3',
                     data=dict(col1='test!', col2='test@', col3='test#'))
    eq_(rv.status_code, 302)
    eq_(len(view.updated_models), 1)

    model = view.updated_models.pop()
    eq_(model.col1, 'test!')
    eq_(model.col2, 'test@')
    eq_(model.col3, 'test#')

    rv = client.get('/admin/model/edit/?id=4')
    eq_(rv.status_code, 302)

    # Attempt to delete model
    rv = client.post('/admin/model/delete/?id=3')
    eq_(rv.status_code, 302)
    eq_(rv.headers['location'], 'http://localhost/admin/model/')

    # Create a dispatched application to test that edit view's "save and
    # continue" functionality works when app is not located at root
    dummy_app = Flask('dummy_app')
    dispatched_app = DispatcherMiddleware(dummy_app, {'/dispatched': app})
    dispatched_client = Client(dispatched_app)

    app_iter, status, headers = dispatched_client.post(
        '/dispatched/admin/model/edit/?id=3',
        data=dict(col1='another test!', col2='test@', col3='test#', _continue_editing='True'))

    eq_(status, '302 FOUND')
    eq_(headers['Location'], 'http://localhost/dispatched/admin/model/edit/?id=3')
    model = view.updated_models.pop()
    eq_(model.col1, 'another test!')


def test_permissions():
    app, admin = setup()

    view = MockModelView(Model)
    admin.add_view(view)

    client = app.test_client()

    view.can_create = False
    rv = client.get('/admin/model/new/')
    eq_(rv.status_code, 302)

    view.can_edit = False
    rv = client.get('/admin/model/edit/?id=1')
    eq_(rv.status_code, 302)

    view.can_delete = False
    rv = client.post('/admin/model/delete/?id=1')
    eq_(rv.status_code, 302)


def test_templates():
    app, admin = setup()

    view = MockModelView(Model)
    admin.add_view(view)

    client = app.test_client()

    view.list_template = 'mock.html'
    view.create_template = 'mock.html'
    view.edit_template = 'mock.html'

    rv = client.get('/admin/model/')
    eq_(rv.data, b'Success!')

    rv = client.get('/admin/model/new/')
    eq_(rv.data, b'Success!')

    rv = client.get('/admin/model/edit/?id=1')
    eq_(rv.data, b'Success!')


def test_list_columns():
    app, admin = setup()

    view = MockModelView(Model,
                         column_list=['col1', 'col3'],
                         column_labels=dict(col1='Column1'))
    admin.add_view(view)

    eq_(len(view._list_columns), 2)
    eq_(view._list_columns, [('col1', 'Column1'), ('col3', 'Col3')])

    client = app.test_client()

    rv = client.get('/admin/model/')
    data = rv.data.decode('utf-8')
    ok_('Column1' in data)
    ok_('Col2' not in data)


def test_exclude_columns():
    app, admin = setup()

    view = MockModelView(Model, column_exclude_list=['col2'])
    admin.add_view(view)

    eq_(view._list_columns, [('col1', 'Col1'), ('col3', 'Col3')])

    client = app.test_client()

    rv = client.get('/admin/model/')
    data = rv.data.decode('utf-8')
    ok_('Col1' in data)
    ok_('Col2' not in data)


def test_sortable_columns():
    app, admin = setup()

    view = MockModelView(Model, column_sortable_list=['col1', ('col2', 'test1')])
    admin.add_view(view)

    eq_(view._sortable_columns, dict(col1='col1', col2='test1'))


def test_column_searchable_list():
    app, admin = setup()

    view = MockModelView(Model, column_searchable_list=['col1', 'col2'])
    admin.add_view(view)

    eq_(view._search_supported, True)

    # TODO: Make calls with search


def test_column_filters():
    app, admin = setup()

    view = MockModelView(Model, column_filters=['col1', 'col2'])
    admin.add_view(view)

    eq_(len(view._filters), 2)
    eq_(view._filters[0].name, 'col1')
    eq_(view._filters[1].name, 'col2')

    eq_([(f['index'], f['operation']) for f in view._filter_groups[u'col1']], [(0, 'test')])
    eq_([(f['index'], f['operation']) for f in view._filter_groups[u'col2']], [(1, 'test')])

    # TODO: Make calls with filters


def test_filter_list_callable():
    app, admin = setup()

    flt = SimpleFilter('test', options=lambda: (('1', 'Test 1'), ('2', 'Test 2')))

    view = MockModelView(Model, column_filters=[flt])
    admin.add_view(view)

    opts = flt.get_options(view)
    eq_(len(opts), 2)
    eq_(opts, [('1', u'Test 1'), ('2', u'Test 2')])


def test_form():
    # TODO: form_columns
    # TODO: form_excluded_columns
    # TODO: form_args
    # TODO: form_widget_args
    pass


@wtforms2_and_up
def test_csrf():
    from datetime import timedelta

    from wtforms.csrf.session import SessionCSRF
    from wtforms.meta import DefaultMeta

    # BaseForm w/ CSRF
    class SecureForm(form.BaseForm):
        class Meta(DefaultMeta):
            csrf = True
            csrf_class = SessionCSRF
            csrf_secret = b'EPj00jpfj8Gx1SjnyLxwBBSQfnQ9DJYe0Ym'
            csrf_time_limit = timedelta(minutes=20)

            @property
            def csrf_context(self):
                return session

    class SecureModelView(MockModelView):
        form_base_class = SecureForm

        def scaffold_form(self):
            return SecureForm

    def get_csrf_token(data):
        data = data.split('name="csrf_token" type="hidden" value="')[1]
        token = data.split('"')[0]
        return token

    app, admin = setup()

    view = SecureModelView(Model, endpoint='secure')
    admin.add_view(view)

    client = app.test_client()

    ################
    # create_view
    ################
    rv = client.get('/admin/secure/new/')
    eq_(rv.status_code, 200)
    ok_(u'name="csrf_token"' in rv.data.decode('utf-8'))

    csrf_token = get_csrf_token(rv.data.decode('utf-8'))

    # Create without CSRF token
    rv = client.post('/admin/secure/new/', data=dict(name='test1'))
    eq_(rv.status_code, 200)

    # Create with CSRF token
    rv = client.post('/admin/secure/new/', data=dict(name='test1',
                                                   csrf_token=csrf_token))
    eq_(rv.status_code, 302)

    ###############
    # edit_view
    ###############
    rv = client.get('/admin/secure/edit/?url=%2Fadmin%2Fsecure%2F&id=1')
    eq_(rv.status_code, 200)
    ok_(u'name="csrf_token"' in rv.data.decode('utf-8'))

    csrf_token = get_csrf_token(rv.data.decode('utf-8'))

    # Edit without CSRF token
    rv = client.post('/admin/secure/edit/?url=%2Fadmin%2Fsecure%2F&id=1', 
                     data=dict(name='test1'))
    eq_(rv.status_code, 200)

    # Edit with CSRF token
    rv = client.post('/admin/secure/edit/?url=%2Fadmin%2Fsecure%2F&id=1',
                     data=dict(name='test1', csrf_token=csrf_token))
    eq_(rv.status_code, 302)

    ################
    # delete_view
    ################
    rv = client.get('/admin/secure/')
    eq_(rv.status_code, 200)
    ok_(u'name="csrf_token"' in rv.data.decode('utf-8'))

    csrf_token = get_csrf_token(rv.data.decode('utf-8'))

    # Delete without CSRF token, test validation errors
    rv = client.post('/admin/secure/delete/', 
                     data=dict(id="1", url="/admin/secure/"), follow_redirects=True)
    eq_(rv.status_code, 200)
    ok_(u'Record was successfully deleted.' not in rv.data.decode('utf-8'))
    ok_(u'Failed to delete record.' in rv.data.decode('utf-8'))

    # Delete with CSRF token
    rv = client.post('/admin/secure/delete/',
                     data=dict(id="1", url="/admin/secure/", csrf_token=csrf_token),
                     follow_redirects=True)
    eq_(rv.status_code, 200)
    ok_(u'Record was successfully deleted.' in rv.data.decode('utf-8'))


def test_custom_form():
    app, admin = setup()

    class TestForm(form.BaseForm):
        pass

    view = MockModelView(Model, form=TestForm)
    admin.add_view(view)

    eq_(view._create_form_class, TestForm)
    eq_(view._edit_form_class, TestForm)

    ok_(not hasattr(view._create_form_class, 'col1'))


def check_class_name():
    class DummyView(MockModelView):
        pass

    view = DummyView(Model)
    eq_(view.name, 'Dummy View')
