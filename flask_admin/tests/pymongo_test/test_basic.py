
import pytest
pymongo = pytest.importorskip('pymongo')

from flask import Flask

from flask_admin import Admin
from flask_admin.contrib.pymongo import ModelView

from pymongo import MongoClient
from wtforms import form, fields

from . import setup


class TestForm(form.Form):
    test1 = fields.StringField('Test1')
    test2 = fields.StringField('Test2')


class TestView(ModelView):
    column_list = ('test1', 'test2', 'test3', 'test4')
    column_sortable_list = ('test1', 'test2')

    form = TestForm

def setup():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '1'
    app.config['CSRF_ENABLED'] = False

    conn = MongoClient()
    db = conn.tests

    admin = Admin(app)

    return app, db, admin

def test_model():
    app, db, admin = setup()

    view = TestView(db.test, 'Test')
    admin.add_view(view)

    # Drop existing data (if any)
    db.test.remove()

    assert view.name == 'Test'
    assert view.endpoint == 'testview'

    assert 'test1' in view._sortable_columns
    assert 'test2' in view._sortable_columns

    assert view._create_form_class is not None
    assert view._edit_form_class is not None
    assert view._search_supported == False
    assert view._filters == None

    # Make some test clients
    client = app.test_client()

    rv = client.get('/admin/testview/')
    assert rv.status_code == 200

    rv = client.get('/admin/testview/new/')
    assert rv.status_code == 200

    rv = client.post('/admin/testview/new/',
                     data=dict(test1='test1large', test2='test2'))
    assert rv.status_code == 302

    model = db.test.find()[0]
    print(model)
    assert model['test1'] == 'test1large'
    assert model['test2'] == 'test2'

    rv = client.get('/admin/testview/')
    assert rv.status_code == 200
    assert 'test1large' in rv.data.decode('utf-8')

    url = '/admin/testview/edit/?id=%s' % model['_id']
    rv = client.get(url)
    assert rv.status_code == 200

    rv = client.post(url,
                     data=dict(test1='test1small', test2='test2large'))
    assert rv.status_code == 302

    print((db.test.find()[0]))

    model = db.test.find()[0]
    assert model['test1'] == 'test1small'
    assert model['test2'] == 'test2large'

    url = '/admin/testview/delete/?id=%s' % model['_id']
    rv = client.post(url)
    assert rv.status_code == 302
    assert db.test.count() == 0
