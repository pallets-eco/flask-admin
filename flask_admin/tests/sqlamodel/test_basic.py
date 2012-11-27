from nose.tools import eq_, ok_, raises

from flask.ext import wtf
from flask.ext.admin.contrib.sqlamodel import ModelView

from . import setup


class CustomModelView(ModelView):
    def __init__(self, model, session,
                 name=None, category=None, endpoint=None, url=None,
                 **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

        super(CustomModelView, self).__init__(model, session,
                                              name, category,
                                              endpoint, url)


def create_models(db):
    class Model1(db.Model):
        def __init__(self, test1=None, test2=None, test3=None, test4=None):
            self.test1 = test1
            self.test2 = test2
            self.test3 = test3
            self.test4 = test4

        id = db.Column(db.Integer, primary_key=True)
        test1 = db.Column(db.String(20))
        test2 = db.Column(db.Unicode(20))
        test3 = db.Column(db.Text)
        test4 = db.Column(db.UnicodeText)

    class Model2(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        int_field = db.Column(db.Integer)
        bool_field = db.Column(db.Boolean)

    db.create_all()

    return Model1, Model2


def test_model():
    app, db, admin = setup()
    Model1, Model2 = create_models(db)
    db.create_all()

    view = CustomModelView(Model1, db.session)
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

    model = db.session.query(Model1).first()
    eq_(model.test1, 'test1large')
    eq_(model.test2, 'test2')
    eq_(model.test3, '')
    eq_(model.test4, '')

    rv = client.get('/admin/model1view/')
    eq_(rv.status_code, 200)
    ok_('test1large' in rv.data)

    url = '/admin/model1view/edit/?id=%s' % model.id
    rv = client.get(url)
    eq_(rv.status_code, 200)

    rv = client.post(url,
                     data=dict(test1='test1small', test2='test2large'))
    eq_(rv.status_code, 302)

    model = db.session.query(Model1).first()
    eq_(model.test1, 'test1small')
    eq_(model.test2, 'test2large')
    eq_(model.test3, '')
    eq_(model.test4, '')

    url = '/admin/model1view/delete/?id=%s' % model.id
    rv = client.post(url)
    eq_(rv.status_code, 302)
    eq_(db.session.query(Model1).count(), 0)


@raises(Exception)
def test_no_pk():
    app, db, admin = setup()

    class Model(db.Model):
        test = db.Column(db.Integer)

    view = CustomModelView(Model)
    admin.add_view(view)


def test_list_columns():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1, db.session,
                           column_list=['test1', 'test3'],
                           column_labels=dict(test1='Column1'))
    admin.add_view(view)

    eq_(len(view._list_columns), 2)
    eq_(view._list_columns, [('test1', 'Column1'), ('test3', 'Test3')])

    client = app.test_client()

    rv = client.get('/admin/model1view/')
    ok_('Column1' in rv.data)
    ok_('Test2' not in rv.data)


def test_exclude_columns():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1, db.session,
                           column_exclude_list=['test2', 'test4'])
    admin.add_view(view)

    eq_(view._list_columns, [('test1', 'Test1'), ('test3', 'Test3')])

    client = app.test_client()

    rv = client.get('/admin/model1view/')
    ok_('Test1' in rv.data)
    ok_('Test2' not in rv.data)


def test_column_searchable_list():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1, db.session,
                           column_searchable_list=['test1', 'test2'])
    admin.add_view(view)

    eq_(view._search_supported, True)
    eq_(len(view._search_fields), 2)
    ok_(isinstance(view._search_fields[0], db.Column))
    ok_(isinstance(view._search_fields[1], db.Column))
    eq_(view._search_fields[0].name, 'test1')
    eq_(view._search_fields[1].name, 'test2')

    db.session.add(Model1('model1'))
    db.session.add(Model1('model2'))
    db.session.commit()

    client = app.test_client()

    rv = client.get('/admin/model1view/?search=model1')
    ok_('model1' in rv.data)
    ok_('model2' not in rv.data)


def test_column_filters():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1, db.session,
                           column_filters=['test1'])
    admin.add_view(view)

    eq_(len(view._filters), 4)

    eq_(view._filter_dict, {'Test1': [(0, 'equals'),
                                      (1, 'not equal'),
                                      (2, 'contains'),
                                      (3, 'not contains')]})

    db.session.add(Model1('model1'))
    db.session.add(Model1('model2'))
    db.session.add(Model1('model3'))
    db.session.add(Model1('model4'))
    db.session.commit()

    client = app.test_client()

    rv = client.get('/admin/model1view/?flt0_0=model1')
    eq_(rv.status_code, 200)
    ok_('model1' in rv.data)
    ok_('model2' not in rv.data)

    rv = client.get('/admin/model1view/?flt0_5=model1')
    eq_(rv.status_code, 200)
    ok_('model1' in rv.data)
    ok_('model2' in rv.data)

    # Test different filter types
    view = CustomModelView(Model2, db.session,
                           column_filters=['int_field'])
    admin.add_view(view)

    eq_(view._filter_dict, {'Int Field': [(0, 'equals'), (1, 'not equal'),
                                          (2, 'greater than'), (3, 'smaller than')]})


def test_url_args():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1, db.session,
                           page_size=2,
                           column_searchable_list=['test1'],
                           column_filters=['test1'])
    admin.add_view(view)

    db.session.add(Model1('data1'))
    db.session.add(Model1('data2'))
    db.session.add(Model1('data3'))
    db.session.add(Model1('data4'))
    db.session.commit()

    client = app.test_client()

    rv = client.get('/admin/model1view/')
    ok_('data1' in rv.data)
    ok_('data3' not in rv.data)

    # page
    rv = client.get('/admin/model1view/?page=1')
    ok_('data1' not in rv.data)
    ok_('data3' in rv.data)

    # sort
    rv = client.get('/admin/model1view/?sort=0&desc=1')
    ok_('data1' not in rv.data)
    ok_('data3' in rv.data)
    ok_('data4' in rv.data)

    # search
    rv = client.get('/admin/model1view/?search=data1')
    ok_('data1' in rv.data)
    ok_('data2' not in rv.data)

    rv = client.get('/admin/model1view/?search=^data1')
    ok_('data2' not in rv.data)

    # like
    rv = client.get('/admin/model1view/?flt0=0&flt0v=data1')
    ok_('data1' in rv.data)

    # not like
    rv = client.get('/admin/model1view/?flt0=1&flt0v=data1')
    ok_('data2' in rv.data)


def test_non_int_pk():
    app, db, admin = setup()

    class Model(db.Model):
        id = db.Column(db.String, primary_key=True)
        test = db.Column(db.String)

    db.create_all()

    view = CustomModelView(Model, db.session, form_columns=['id', 'test'])
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/modelview/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/modelview/new/',
                     data=dict(id='test1', test='test2'))
    eq_(rv.status_code, 302)

    rv = client.get('/admin/modelview/')
    eq_(rv.status_code, 200)
    ok_('test1' in rv.data)

    rv = client.get('/admin/modelview/edit/?id=test1')
    eq_(rv.status_code, 200)
    ok_('test2' in rv.data)


def test_form():
    # TODO: form_columns
    # TODO: form_excluded_columns
    # TODO: form_args
    # TODO: Select columns
    pass


def test_form_override():
    app, db, admin = setup()

    class Model(db.Model):
        id = db.Column(db.String, primary_key=True)
        test = db.Column(db.String)

    db.create_all()

    view1 = CustomModelView(Model, db.session, endpoint='view1')
    view2 = CustomModelView(Model, db.session, endpoint='view2', form_overrides=dict(test=wtf.FileField))
    admin.add_view(view1)
    admin.add_view(view2)

    eq_(view1._create_form_class.test.field_class, wtf.TextField)
    eq_(view2._create_form_class.test.field_class, wtf.FileField)


def test_relations():
    # TODO: test relations
    pass


def test_on_model_change_delete():
    app, db, admin = setup()
    Model1, _ = create_models(db)
    db.create_all()

    class ModelView(CustomModelView):
        def on_model_change(self, form, model):
            model.test1 = model.test1.upper()

        def on_model_delete(self, model):
            self.deleted = True

    view = ModelView(Model1, db.session)
    admin.add_view(view)

    client = app.test_client()

    client.post('/admin/model1view/new/',
                     data=dict(test1='test1large', test2='test2'))

    model = db.session.query(Model1).first()
    eq_(model.test1, 'TEST1LARGE')

    url = '/admin/model1view/edit/?id=%s' % model.id
    client.post(url, data=dict(test1='test1small', test2='test2large'))

    model = db.session.query(Model1).first()
    eq_(model.test1, 'TEST1SMALL')

    url = '/admin/model1view/delete/?id=%s' % model.id
    client.post(url)
    ok_(view.deleted)

def test_multiple_delete():
    app, db, admin = setup()
    M1, _ = create_models(db)

    db.session.add_all([M1('a'), M1('b'), M1('c')])
    db.session.commit()
    eq_(M1.query.count(), 3)

    view = ModelView(M1, db.session)
    admin.add_view(view)

    client = app.test_client()

    rv = client.post('/admin/model1view/action/', data=dict(action='delete', rowid=[1,2,3]))
    eq_(rv.status_code, 302)
    eq_(M1.query.count(), 0)
