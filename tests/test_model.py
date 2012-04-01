from flask import Flask

from flask.ext.adminex import Admin
from flask.ext.adminex.model import base, filters

from flask.ext import wtf


class Model(object):
    def __init__(self, id=None, c1=None, c2=None, c3=None):
        self.id = id
        self.col1 = c1
        self.col2 = c2
        self.col3 = c3


class Form(wtf.Form):
    col1 = wtf.TextField()
    col2 = wtf.TextField()
    col3 = wtf.TextField()


class MockModelView(base.BaseModelView):
    def __init__(self, model, name=None, category=None, endpoint=None, url=None):
        super(MockModelView, self).__init__(model, name, category, endpoint, url)

        self.created_models = []
        self.updated_models = []
        self.deleted_models = []

    # Scaffolding
    def scaffold_pk(self):
        return 'id'

    def scaffold_list_columns(self):
        return ['col1', 'col2', 'col3']

    def init_search(self):
        return True

    def scaffold_filters(self):
        return None

    def scaffold_form(self):
        return Form

    # Data
    def get_list(self, page, sort_field, sort_desc, search, filters):
        return [Model(1,2,3,4), Model(2,3,4,5)]

    def get_one(self, id):
        return Model(1,2,3,4)

    def create_model(self, form):
        model = Model()
        form.populate_obj(model)
        return True

    def update_model(self, form, model):
        form.populate_obj(model)
        return True

    def delete_model(self, model):
        return True


def test_mockview():
    app = Flask(__name__)
    admin = Admin()

    view = MockView(Model)
    admin.add_view(view)

    eq_(view.model, Model)

    eq_(view.name, 'Model')
    eq_(view.endpoint, 'modelview')

    # Verify scaffolding
    eq_(view._primary_key, 'id')
    eq_(view._sortable_columns, ['col1', 'col2', 'col3'])
    eq_(view._create_form_class, Form)
    eq_(view._edit_form_class, Form)
    eq_(view._search_supported, True)
    eq_(view._filters, None)

    # Make some test requests
    client = app.test_client()

    rv = client.get('/admin/modelview/')
    eq_(rv.status_code, 200)

    rv = client.get('/admin/modelview/new/')
    eq_(rv.status_code, 200)

    rv = client.get('/admin/modelview/edit/0/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/modelview/delete/0/')
    eq_(rv.status_code, 200)
