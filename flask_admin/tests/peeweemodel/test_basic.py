from nose.tools import eq_, ok_

import peewee

from flask.ext import wtf
from flask.ext.admin.contrib.peeweemodel import ModelView

from . import setup


class CustomModelView(ModelView):
    def __init__(self, model,
                 name=None, category=None, endpoint=None, url=None,
                 **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

        super(CustomModelView, self).__init__(model,
                                              name, category,
                                              endpoint, url)


def create_models(db):
    class BaseModel(peewee.Model):
        class Meta:
            database = db

    class Model1(BaseModel):
        def __init__(self, test1=None, test2=None, test3=None, test4=None):
            super(Model1, self).__init__()

            self.test1 = test1
            self.test2 = test2
            self.test3 = test3
            self.test4 = test4

        test1 = peewee.CharField(max_length=20)
        test2 = peewee.CharField(max_length=20)
        test3 = peewee.TextField(null=True)
        test4 = peewee.TextField(null=True)

    class Model2(BaseModel):
        int_field = peewee.IntegerField()
        bool_field = peewee.BooleanField()

    Model1.create_table()
    Model2.create_table()

    return Model1, Model2


def test_model():
    app, db, admin = setup()
    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1)
    admin.add_view(view)

    eq_(view.model, Model1)
    eq_(view.name, 'Model1')
    eq_(view.endpoint, 'model1view')

    eq_(view._primary_key, 'id')

    ok_('test1' in view._sortable_columns)
    ok_('test2' in view._sortable_columns)
    ok_('test3' in view._sortable_columns)
    ok_('test4' in view._sortable_columns)

    ok_(view._create_form_class is not None)
    ok_(view._edit_form_class is not None)
    eq_(view._search_supported, False)
    eq_(view._filters, None)

    # Verify form
    eq_(view._create_form_class.test1.field_class, wtf.TextField)
    eq_(view._create_form_class.test2.field_class, wtf.TextField)
    eq_(view._create_form_class.test3.field_class, wtf.TextAreaField)
    eq_(view._create_form_class.test4.field_class, wtf.TextAreaField)

    # Make some test clients
    client = app.test_client()

    rv = client.get('/admin/model1view/')
    eq_(rv.status_code, 200)

    rv = client.get('/admin/model1view/new/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/model1view/new/',
                     data=dict(test1='test1large', test2='test2'))
    eq_(rv.status_code, 302)

    model = Model1.select().get()
    eq_(model.test1, 'test1large')
    eq_(model.test2, 'test2')
    eq_(model.test3, None)
    eq_(model.test4, None)

    rv = client.get('/admin/model1view/')
    eq_(rv.status_code, 200)
    ok_('test1large' in rv.data)

    url = '/admin/model1view/edit/?id=%s' % model.id
    rv = client.get(url)
    eq_(rv.status_code, 200)

    rv = client.post(url,
                     data=dict(test1='test1small', test2='test2large'))
    eq_(rv.status_code, 302)

    model = Model1.select().get()
    eq_(model.test1, 'test1small')
    eq_(model.test2, 'test2large')
    eq_(model.test3, None)
    eq_(model.test4, None)

    url = '/admin/model1view/delete/?id=%s' % model.id
    rv = client.post(url)
    eq_(rv.status_code, 302)
    eq_(Model1.select().count(), 0)
