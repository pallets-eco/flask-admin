from wtforms import form, fields

from flask_admin.contrib.pymongo import ModelView

from . import setup


class TestForm(form.Form):
    __test__ = False
    test1 = fields.StringField('Test1')
    test2 = fields.StringField('Test2')


class TestView(ModelView):
    __test__ = False
    column_list = ('test1', 'test2', 'test3', 'test4')
    column_sortable_list = ('test1', 'test2')

    form = TestForm


def test_model():
    app, db, admin = setup()

    view = TestView(db.test, 'Test')
    admin.add_view(view)

    # Drop existing data (if any)
    db.test.delete_many({})

    assert view.name == 'Test'
    assert view.endpoint == 'testview'

    assert 'test1' in view._sortable_columns
    assert 'test2' in view._sortable_columns

    assert view._create_form_class is not None
    assert view._edit_form_class is not None
    assert not view._search_supported
    assert view._filters is None

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

    print(db.test.find()[0])

    model = db.test.find()[0]
    assert model['test1'] == 'test1small'
    assert model['test2'] == 'test2large'

    url = '/admin/testview/delete/?id=%s' % model['_id']
    rv = client.post(url)
    assert rv.status_code == 302
    assert db.test.count() == 0
