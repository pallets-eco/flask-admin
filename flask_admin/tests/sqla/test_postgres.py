from nose.tools import eq_, ok_

from . import setup_postgres
from .test_basic import CustomModelView

from sqlalchemy.dialects.postgresql import HSTORE


def test_hstore():
    app, db, admin = setup_postgres()

    class Model(db.Model):
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        hstore_test = db.Column(HSTORE)

    db.create_all()

    view = CustomModelView(Model, db.session)
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/model/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/model/new/', data={
        'hstore_test-0-key': 'test_val1',
        'hstore_test-0-value': 'test_val2'
    })
    eq_(rv.status_code, 302)

    rv = client.get('/admin/model/')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test_val1' in data)
    ok_('test_val2' in data)

    rv = client.get('/admin/model/edit/?id=1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test_val1' in data)
    ok_('test_val2' in data)
