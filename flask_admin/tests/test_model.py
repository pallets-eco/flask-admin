from nose.tools import eq_, ok_, raises

from flask import Flask
from flask.helpers import get_flashed_messages

from flask.ext.admin import Admin
from flask.ext.admin.model import base, filters

from flask.ext import wtf


class Model(object):
    def __init__(self, id=None, c1=1, c2=2, c3=3):
        self.id = id
        self.col1 = c1
        self.col2 = c2
        self.col3 = c3


class Form(wtf.Form):
    col1 = wtf.TextField()
    col2 = wtf.TextField()
    col3 = wtf.TextField()


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
        for k, v in kwargs.iteritems():
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
        return len(self.all_models), self.all_models.itervalues()

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
    eq_(view.endpoint, 'modelview')

    # Verify scaffolding
    eq_(view._sortable_columns, ['col1', 'col2', 'col3'])
    eq_(view._create_form_class, Form)
    eq_(view._edit_form_class, Form)
    eq_(view._search_supported, False)
    eq_(view._filters, None)

    client = app.test_client()

    # Make model view requests
    rv = client.get('/admin/modelview/')
    eq_(rv.status_code, 200)

    # Test model creation view
    rv = client.get('/admin/modelview/new/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/modelview/new/',
                     data=dict(col1='test1', col2='test2', col3='test3'))
    eq_(rv.status_code, 302)
    eq_(len(view.created_models), 1)

    model = view.created_models.pop()
    eq_(model.id, 3)
    eq_(model.col1, 'test1')
    eq_(model.col2, 'test2')
    eq_(model.col3, 'test3')

    # Try model edit view
    rv = client.get('/admin/modelview/edit/?id=3')
    eq_(rv.status_code, 200)
    ok_('test1' in rv.data)

    rv = client.post('/admin/modelview/edit/?id=3',
                     data=dict(col1='test!', col2='test@', col3='test#'))
    eq_(rv.status_code, 302)
    eq_(len(view.updated_models), 1)

    model = view.updated_models.pop()
    eq_(model.col1, 'test!')
    eq_(model.col2, 'test@')
    eq_(model.col3, 'test#')

    rv = client.get('/admin/modelview/edit/?id=4')
    eq_(rv.status_code, 302)

    # Attempt to delete model
    rv = client.post('/admin/modelview/delete/?id=3')
    eq_(rv.status_code, 302)
    eq_(rv.headers['location'], 'http://localhost/admin/modelview/')


def test_permissions():
    app, admin = setup()

    view = MockModelView(Model)
    admin.add_view(view)

    client = app.test_client()

    view.can_create = False
    rv = client.get('/admin/modelview/new/')
    eq_(rv.status_code, 302)

    view.can_edit = False
    rv = client.get('/admin/modelview/edit/?id=1')
    eq_(rv.status_code, 302)

    view.can_delete = False
    rv = client.post('/admin/modelview/delete/?id=1')
    eq_(rv.status_code, 302)


def test_templates():
    app, admin = setup()

    view = MockModelView(Model)
    admin.add_view(view)

    client = app.test_client()

    view.list_template = 'mock.html'
    view.create_template = 'mock.html'
    view.edit_template = 'mock.html'

    rv = client.get('/admin/modelview/')
    eq_(rv.data, 'Success!')

    rv = client.get('/admin/modelview/new/')
    eq_(rv.data, 'Success!')

    rv = client.get('/admin/modelview/edit/?id=1')
    eq_(rv.data, 'Success!')


def test_list_columns():
    app, admin = setup()

    view = MockModelView(Model,
                         column_list=['col1', 'col3'],
                         column_labels=dict(col1='Column1'))
    admin.add_view(view)

    eq_(len(view._list_columns), 2)
    eq_(view._list_columns, [('col1', 'Column1'), ('col3', 'Col3')])

    client = app.test_client()

    rv = client.get('/admin/modelview/')
    ok_('Column1' in rv.data)
    ok_('Col2' not in rv.data)


def test_exclude_columns():
    app, admin = setup()

    view = MockModelView(Model, column_exclude_list=['col2'])
    admin.add_view(view)

    eq_(view._list_columns, [('col1', 'Col1'), ('col3', 'Col3')])

    client = app.test_client()

    rv = client.get('/admin/modelview/')
    ok_('Col1' in rv.data)
    ok_('Col2' not in rv.data)


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

    eq_(view._filter_dict, {'col1': [(0, 'test')],
                            'col2': [(1, 'test')]})

    # TODO: Make calls with filters


def test_form():
    # TODO: form_columns
    # TODO: form_excluded_columns
    # TODO: form_args
    pass


def test_custom_form():
    app, admin = setup()

    class TestForm(wtf.Form):
        pass

    view = MockModelView(Model, form=TestForm)
    admin.add_view(view)

    eq_(view._create_form_class, TestForm)
    eq_(view._edit_form_class, TestForm)
