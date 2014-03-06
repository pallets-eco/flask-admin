from nose.tools import eq_, ok_, raises

from wtforms import fields

from flask.ext.admin import form
from flask.ext.admin._compat import as_unicode
from flask.ext.admin._compat import iteritems
from flask.ext.admin.contrib.sqla import ModelView

from . import setup


class CustomModelView(ModelView):
    def __init__(self, model, session,
                 name=None, category=None, endpoint=None, url=None,
                 **kwargs):
        for k, v in iteritems(kwargs):
            setattr(self, k, v)

        super(CustomModelView, self).__init__(model, session, name, category,
                                              endpoint, url)


def create_models(db):
    class Model1(db.Model):
        def __init__(self, test1=None, test2=None, test3=None, test4=None, bool_field=False):
            self.test1 = test1
            self.test2 = test2
            self.test3 = test3
            self.test4 = test4
            self.bool_field = bool_field

        id = db.Column(db.Integer, primary_key=True)
        test1 = db.Column(db.String(20))
        test2 = db.Column(db.Unicode(20))
        test3 = db.Column(db.Text)
        test4 = db.Column(db.UnicodeText)
        bool_field = db.Column(db.Boolean)
        enum_field = db.Column(db.Enum('model1_v1', 'model1_v1'), nullable=True)

        def __str__(self):
            return self.test1

    class Model2(db.Model):
        def __init__(self, string_field=None, int_field=None, bool_field=None, model1=None):
            self.string_field = string_field
            self.int_field = int_field
            self.bool_field = bool_field
            self.model1 = model1

        id = db.Column(db.Integer, primary_key=True)
        string_field = db.Column(db.String)
        int_field = db.Column(db.Integer)
        bool_field = db.Column(db.Boolean)
        enum_field = db.Column(db.Enum('model2_v1', 'model2_v2'), nullable=True)

        # Relation
        model1_id = db.Column(db.Integer, db.ForeignKey(Model1.id))
        model1 = db.relationship(Model1, backref='model2')

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
    eq_(view._create_form_class.test1.field_class, fields.TextField)
    eq_(view._create_form_class.test2.field_class, fields.TextField)
    eq_(view._create_form_class.test3.field_class, fields.TextAreaField)
    eq_(view._create_form_class.test4.field_class, fields.TextAreaField)

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
    eq_(model.test1, u'test1large')
    eq_(model.test2, u'test2')
    eq_(model.test3, u'')
    eq_(model.test4, u'')

    rv = client.get('/admin/model1view/')
    eq_(rv.status_code, 200)
    ok_(u'test1large' in rv.data.decode('utf-8'))

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
    data = rv.data.decode('utf-8')
    ok_('Column1' in data)
    ok_('Test2' not in data)


def test_exclude_columns():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(
        Model1, db.session,
        column_exclude_list=['test2', 'test4', 'enum_field']
    )
    admin.add_view(view)

    eq_(
        view._list_columns,
        [('test1', 'Test1'), ('test3', 'Test3'), ('bool_field', 'Bool Field')]
    )

    client = app.test_client()

    rv = client.get('/admin/model1view/')
    data = rv.data.decode('utf-8')
    ok_('Test1' in data)
    ok_('Test2' not in data)


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
    data = rv.data.decode('utf-8')
    ok_('model1' in data)
    ok_('model2' not in data)


def test_column_filters():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(
        Model1, db.session,
        column_filters=['test1']
    )
    admin.add_view(view)

    eq_(len(view._filters), 4)

    eq_([(f['index'], f['operation']) for f in view._filter_groups[u'Test1']],
        [
            (0, u'equals'),
            (1, u'not equal'),
            (2, u'contains'),
            (3, u'not contains')
        ])

    # Test filter that references property
    view = CustomModelView(Model2, db.session,
                           column_filters=['model1'])

    eq_([(f['index'], f['operation']) for f in view._filter_groups[u'Model1 / Test1']],
        [
            (0, u'equals'),
            (1, u'not equal'),
            (2, u'contains'),
            (3, u'not contains')
        ])

    eq_([(f['index'], f['operation']) for f in view._filter_groups[u'Model1 / Test2']],
        [
            (4, 'equals'),
            (5, 'not equal'),
            (6, 'contains'),
            (7, 'not contains')
        ])

    eq_([(f['index'], f['operation']) for f in view._filter_groups[u'Model1 / Test3']],
        [
            (8, u'equals'),
            (9, u'not equal'),
            (10, u'contains'),
            (11, u'not contains')
        ])

    eq_([(f['index'], f['operation']) for f in view._filter_groups[u'Model1 / Test4']],
        [
            (12, u'equals'),
            (13, u'not equal'),
            (14, u'contains'),
            (15, u'not contains')
        ])

    eq_([(f['index'], f['operation']) for f in view._filter_groups[u'Model1 / Bool Field']],
        [
            (16, u'equals'),
            (17, u'not equal'),
        ])

    eq_([(f['index'], f['operation']) for f in view._filter_groups[u'Model1 / Enum Field']],
        [
            (18, u'equals'),
            (19, u'not equal'),
        ])

    # Test filter with a dot
    view = CustomModelView(Model2, db.session,
                           column_filters=['model1.bool_field'])

    eq_([(f['index'], f['operation']) for f in view._filter_groups[u'Model1 / Bool Field']],
        [
            (0, 'equals'),
            (1, 'not equal'),
        ])

    # Fill DB
    model1_obj1 = Model1('model1_obj1', bool_field=True)
    model1_obj2 = Model1('model1_obj2')
    model1_obj3 = Model1('model1_obj3')
    model1_obj4 = Model1('model1_obj4')

    model2_obj1 = Model2('model2_obj1', model1=model1_obj1)
    model2_obj2 = Model2('model2_obj2', model1=model1_obj1)
    model2_obj3 = Model2('model2_obj3')
    model2_obj4 = Model2('model2_obj4')
    db.session.add_all([
        model1_obj1, model1_obj2, model1_obj3, model1_obj4,
        model2_obj1, model2_obj2, model2_obj3, model2_obj4,
    ])
    db.session.commit()

    client = app.test_client()

    rv = client.get('/admin/model1view/?flt0_0=model1_obj1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('model1_obj1' in data)
    ok_('model1_obj2' not in data)

    rv = client.get('/admin/model1view/?flt0_5=model1_obj1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('model1_obj1' in data)
    ok_('model1_obj2' in data)

    # Test different filter types
    view = CustomModelView(Model2, db.session,
                           column_filters=['int_field'])
    admin.add_view(view)

    eq_([(f['index'], f['operation']) for f in view._filter_groups[u'Int Field']],
        [
            (0, 'equals'),
            (1, 'not equal'),
            (2, 'greater than'),
            (3, 'smaller than')
        ])

    # Test filters to joined table field
    view = CustomModelView(
        Model2, db.session,
        endpoint='_model2',
        column_filters=['model1.bool_field'],
        column_list=[
            'string_field',
            'model1.id',
            'model1.bool_field',
        ]
    )
    admin.add_view(view)

    rv = client.get('/admin/_model2/?flt1_0=1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('model2_obj1' in data)
    ok_('model2_obj2' in data)
    ok_('model2_obj3' not in data)
    ok_('model2_obj4' not in data)

    # Test human readable URLs
    view = CustomModelView(
        Model1, db.session,
        column_filters=['test1'],
        endpoint='_model3',
        named_filter_urls=True
    )
    admin.add_view(view)

    rv = client.get('/admin/_model3/?flt1_test1_equals=model1_obj1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('model1_obj1' in data)
    ok_('model1_obj2' not in data)


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
    data = rv.data.decode('utf-8')
    ok_('data1' in data)
    ok_('data3' not in data)

    # page
    rv = client.get('/admin/model1view/?page=1')
    data = rv.data.decode('utf-8')
    ok_('data1' not in data)
    ok_('data3' in data)

    # sort
    rv = client.get('/admin/model1view/?sort=0&desc=1')
    data = rv.data.decode('utf-8')
    ok_('data1' not in data)
    ok_('data3' in data)
    ok_('data4' in data)

    # search
    rv = client.get('/admin/model1view/?search=data1')
    data = rv.data.decode('utf-8')
    ok_('data1' in data)
    ok_('data2' not in data)

    rv = client.get('/admin/model1view/?search=^data1')
    data = rv.data.decode('utf-8')
    ok_('data2' not in data)

    # like
    rv = client.get('/admin/model1view/?flt0=0&flt0v=data1')
    data = rv.data.decode('utf-8')
    ok_('data1' in data)

    # not like
    rv = client.get('/admin/model1view/?flt0=1&flt0v=data1')
    data = rv.data.decode('utf-8')
    ok_('data2' in data)


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
    data = rv.data.decode('utf-8')
    ok_('test1' in data)

    rv = client.get('/admin/modelview/edit/?id=test1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test2' in data)

def test_multiple__pk():
    # Test multiple primary keys - mix int and string together
    app, db, admin = setup()

    class Model(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        id2 = db.Column(db.String(20), primary_key=True)
        test = db.Column(db.String)

    db.create_all()

    view = CustomModelView(Model, db.session, form_columns=['id', 'id2', 'test'])
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/modelview/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/modelview/new/',
                     data=dict(id=1, id2='two', test='test3'))
    eq_(rv.status_code, 302)

    rv = client.get('/admin/modelview/')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test3' in data)

    rv = client.get('/admin/modelview/edit/?id=1&id=two')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test3' in data)

    # Correct order is mandatory -> fail here
    rv = client.get('/admin/modelview/edit/?id=two&id=1')
    eq_(rv.status_code, 302)

def test_form_columns():
    app, db, admin = setup()

    class Model(db.Model):
        id = db.Column(db.String, primary_key=True)
        int_field = db.Column(db.Integer)
        datetime_field = db.Column(db.DateTime)
        text_field = db.Column(db.UnicodeText)
        excluded_column = db.Column(db.String)

    class ChildModel(db.Model):
        id = db.Column(db.String, primary_key=True)
        model_id = db.Column(db.Integer, db.ForeignKey(Model.id))
        model = db.relationship(Model, backref='backref')

    db.create_all()

    view1 = CustomModelView(Model, db.session, endpoint='view1',
                            form_columns=('int_field', 'text_field'))
    view2 = CustomModelView(Model, db.session, endpoint='view2',
                            form_excluded_columns=('excluded_column',))
    view3 = CustomModelView(ChildModel, db.session, endpoint='view3')

    form1 = view1.create_form()
    form2 = view2.create_form()
    form3 = view3.create_form()

    ok_('int_field' in form1._fields)
    ok_('text_field' in form1._fields)
    ok_('datetime_field' not in form1._fields)

    ok_('excluded_column' not in form2._fields)

    ok_(type(form3.model).__name__ == 'QuerySelectField')

    # TODO: form_args


def test_form_override():
    app, db, admin = setup()

    class Model(db.Model):
        id = db.Column(db.String, primary_key=True)
        test = db.Column(db.String)

    db.create_all()

    view1 = CustomModelView(Model, db.session, endpoint='view1')
    view2 = CustomModelView(Model, db.session, endpoint='view2', form_overrides=dict(test=fields.FileField))
    admin.add_view(view1)
    admin.add_view(view2)

    eq_(view1._create_form_class.test.field_class, fields.TextField)
    eq_(view2._create_form_class.test.field_class, fields.FileField)


def test_form_onetoone():
    app, db, admin = setup()

    class Model1(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        test = db.Column(db.String)

    class Model2(db.Model):
        id = db.Column(db.Integer, primary_key=True)

        model1_id = db.Column(db.Integer, db.ForeignKey(Model1.id))
        model1 = db.relationship(Model1, backref=db.backref('model2', uselist=False))

    db.create_all()

    view1 = CustomModelView(Model1, db.session, endpoint='view1')
    view2 = CustomModelView(Model2, db.session, endpoint='view2')
    admin.add_view(view1)
    admin.add_view(view2)

    model1 = Model1(test='test')
    model2 = Model2(model1=model1)
    db.session.add(model1)
    db.session.add(model2)
    db.session.commit()

    eq_(model1.model2, model2)
    eq_(model2.model1, model1)

    eq_(view1._create_form_class.model2.kwargs['widget'].multiple, False)
    eq_(view2._create_form_class.model1.kwargs['widget'].multiple, False)


def test_relations():
    # TODO: test relations
    pass


def test_on_model_change_delete():
    app, db, admin = setup()
    Model1, _ = create_models(db)
    db.create_all()

    class ModelView(CustomModelView):
        def on_model_change(self, form, model, is_created):
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

    rv = client.post('/admin/model1view/action/', data=dict(action='delete', rowid=[1, 2, 3]))
    eq_(rv.status_code, 302)
    eq_(M1.query.count(), 0)


def test_default_sort():
    app, db, admin = setup()
    M1, _ = create_models(db)

    db.session.add_all([M1('c'), M1('b'), M1('a')])
    db.session.commit()
    eq_(M1.query.count(), 3)

    view = CustomModelView(M1, db.session, column_default_sort='test1')
    admin.add_view(view)

    _, data = view.get_list(0, None, None, None, None)

    eq_(len(data), 3)
    eq_(data[0].test1, 'a')
    eq_(data[1].test1, 'b')
    eq_(data[2].test1, 'c')


def test_extra_fields():
    app, db, admin = setup()

    Model1, _ = create_models(db)

    view = CustomModelView(
        Model1, db.session,
        form_extra_fields={
            'extra_field': fields.TextField('Extra Field')
        }
    )
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/model1view/new/')
    eq_(rv.status_code, 200)

    # Check presence and order
    data = rv.data.decode('utf-8')
    ok_('Extra Field' in data)
    pos1 = data.find('Extra Field')
    pos2 = data.find('Test1')
    ok_(pos2 < pos1)


def test_extra_field_order():
    app, db, admin = setup()

    Model1, _ = create_models(db)

    view = CustomModelView(
        Model1, db.session,
        form_columns=('extra_field', 'test1'),
        form_extra_fields={
            'extra_field': fields.TextField('Extra Field')
        }
    )
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/model1view/new/')
    eq_(rv.status_code, 200)

    # Check presence and order
    data = rv.data.decode('utf-8')
    pos1 = data.find('Extra Field')
    pos2 = data.find('Test1')
    ok_(pos2 > pos1)


# TODO: Babel tests
def test_custom_form_base():
    app, db, admin = setup()

    class TestForm(form.BaseForm):
        pass

    Model1, _ = create_models(db)

    view = CustomModelView(
        Model1, db.session,
        form_base_class=TestForm
    )
    admin.add_view(view)

    ok_(hasattr(view._create_form_class, 'test1'))

    create_form = view.create_form()
    ok_(isinstance(create_form, TestForm))


def test_ajax_fk():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(
        Model2, db.session,
        url='view',
        form_ajax_refs={
            'model1': {
                'fields': ('test1', 'test2')
            }
        }
    )
    admin.add_view(view)

    ok_(u'model1' in view._form_ajax_refs)

    model = Model1(u'first')
    model2 = Model1(u'foo', u'bar')
    db.session.add_all([model, model2])
    db.session.commit()

    # Check loader
    loader = view._form_ajax_refs[u'model1']
    mdl = loader.get_one(model.id)
    eq_(mdl.test1, model.test1)

    items = loader.get_list(u'fir')
    eq_(len(items), 1)
    eq_(items[0].id, model.id)

    items = loader.get_list(u'bar')
    eq_(len(items), 1)
    eq_(items[0].test1, u'foo')

    # Check form generation
    form = view.create_form()
    eq_(form.model1.__class__.__name__, u'AjaxSelectField')

    with app.test_request_context('/admin/view/'):
        ok_(u'value=""' not in form.model1())

        form.model1.data = model
        ok_(u'data-json="[%s, &quot;first&quot;]"' % model.id in form.model1())
        ok_(u'value="1"' in form.model1())

    # Check querying
    client = app.test_client()

    req = client.get(u'/admin/view/ajax/lookup/?name=model1&query=foo')
    eq_(req.data.decode('utf-8'), u'[[%s, "foo"]]' % model2.id)

    # Check submitting
    req = client.post('/admin/view/new/', data={u'model1': as_unicode(model.id)})
    mdl = db.session.query(Model2).first()

    ok_(mdl is not None)
    ok_(mdl.model1 is not None)
    eq_(mdl.model1.id, model.id)
    eq_(mdl.model1.test1, u'first')


def test_ajax_fk_multi():
    app, db, admin = setup()

    class Model1(db.Model):
        __tablename__ = 'model1'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(20))

        def __str__(self):
            return self.name

    table = db.Table('m2m', db.Model.metadata,
                     db.Column('model1_id', db.Integer, db.ForeignKey('model1.id')),
                     db.Column('model2_id', db.Integer, db.ForeignKey('model2.id'))
                     )

    class Model2(db.Model):
        __tablename__ = 'model2'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(20))

        model1_id = db.Column(db.Integer(), db.ForeignKey(Model1.id))
        model1 = db.relationship(Model1, backref='models2', secondary=table)

    db.create_all()

    view = CustomModelView(
        Model2, db.session,
        url='view',
        form_ajax_refs={
            'model1': {
                'fields': ['name']
            }
        }
    )
    admin.add_view(view)

    ok_(u'model1' in view._form_ajax_refs)

    model = Model1(name=u'first')
    db.session.add_all([model, Model1(name=u'foo')])
    db.session.commit()

    # Check form generation
    form = view.create_form()
    eq_(form.model1.__class__.__name__, u'AjaxSelectMultipleField')

    with app.test_request_context('/admin/view/'):
        ok_(u'data-json="[]"' in form.model1())

        form.model1.data = [model]
        ok_(u'data-json="[[1, &quot;first&quot;]]"' in form.model1())

    # Check submitting
    client = app.test_client()
    client.post('/admin/view/new/', data={u'model1': as_unicode(model.id)})
    mdl = db.session.query(Model2).first()

    ok_(mdl is not None)
    ok_(mdl.model1 is not None)
    eq_(len(mdl.model1), 1)


def test_safe_redirect():
    app, db, admin = setup()
    Model1, _ = create_models(db)
    db.create_all()

    view = CustomModelView(Model1, db.session)
    admin.add_view(view)

    client = app.test_client()

    rv = client.post('/admin/model1view/new/?url=http://localhost/admin/model2view/',
                     data=dict(test1='test1large', test2='test2'))

    eq_(rv.status_code, 302)
    eq_(rv.location, 'http://localhost/admin/model2view/')

    rv = client.post('/admin/model1view/new/?url=http://google.com/evil/',
                     data=dict(test1='test1large', test2='test2'))

    eq_(rv.status_code, 302)
    eq_(rv.location, 'http://localhost/admin/model1view/')
